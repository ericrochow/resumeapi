#!/usr/bin/env python3

import bcrypt
from contextlib import suppress
import time
from typing import Dict, List

from peewee import DoesNotExist, Model

import jwt
from decouple import config

# from resumeapi.models import (  # noqa: F401
from models import (  # noqa: F401
    BasicInfo,
    Certification,
    Competency,
    Education,
    Job,
    JobDetail,
    JobHighlight,
    PersonalInterest,
    Preference,
    SideProject,
    Skill,
    SocialLink,
    TechnicalInterest,
    User,
)


class Auth:
    def __init__(self) -> None:
        pass

    def create_user(self, email: str, password: str, is_active: bool = True) -> Model:
        """
        Creates a new user in the database.

        Args:
            email: A string specifying the user's email address
            password: A string specifying the plaintext password of the user
            is_active: A boolean specifying whether the user should be active
                (optional, defaults to True)
        Returns:
            An object of the User class.
        """
        user = User.create(
            email=email.lower(),
            pw_hash=bcrypt.hashpw(password.encode()),
            is_active=is_active,
        )
        return user

    def login(self, email: str, password: str) -> bool:
        """
        Logs a user into the API.

        Args:
            email: A string specifying the user's email address
            password: A string specifying the user's plain-text password
        Returns:
            A boolean specifying whether the login operation was successful.
        """
        try:
            user = User.get(User.email == email.lower())
            if user.is_active:
                return bcrypt.checkpw(password.encode(), user.pw_hash)
        except DoesNotExist:
            return False

    def deactivate_user(self, email: str) -> None:
        """"""
        user = User.get(User.email == email.lower())
        user.is_active = False


class TokenMgmt:
    JWT_SECRET = config("SECRET")
    JWT_ALGORITHM = config("ALGORITHM")

    def __init__(self) -> None:
        pass

    def token_response(self, token: str):
        return {"access_token": token}

    def sign_jwt(self, user_id: str) -> Dict[str, str]:
        payload = {"user_id": user_id, "expires": time.time() + 600}
        token = jwt.encode(payload, self.JWT_SECRET, algorithm=self.JWT_ALGORITHM)

        return self.token_response(token)

    def decode_jwt(self, token: str) -> dict:
        try:
            decoded_token = jwt.decode(
                token, self.JWT_SECRET, algorithms=[self.JWT_ALGORITHM]
            )
            return decoded_token if decoded_token["expires"] >= time.time() else None
        except Exception:
            return {}


class ResumeController:
    def __init__(self) -> None:
        pass

    def get_basic_info(self) -> Dict[str, str]:
        """"""

        info = BasicInfo.select()
        resp = {}
        for i in info:
            resp[i.fact] = i.value
        return resp

    def get_basic_info_item(self, fact: str) -> Dict[str, str]:
        """"""
        try:
            info = BasicInfo.get(BasicInfo.fact == fact)
            return {info.fact: info.value}
        except DoesNotExist:
            raise KeyError("Fact does not exist in the DB.")

    def get_all_education_history(self) -> List[Dict[str, str]]:
        """
        Retrieves all education history objects stored in the database.

        Args:
            None
        Returns:
            A list of all education history objects.
        """
        education = Education.select()
        history = []
        for edu in education:
            e = {
                "institution": edu.institution,
                "degree": edu.degree,
                "graduation_date": edu.graduation_date,
                "gpa": edu.gpa,
            }
            history.append(e)
        return history

    def get_education_item(self, index: int) -> Dict[str, str]:
        """
        Retrieves and education object by its id (index).

        Args:
            index:
        Returns:
            A dict containing details about the requested education item.
        """
        try:
            edu = Education.get_by_id(index)
            e = {
                "institution": edu.institution,
                "degree": edu.degree,
                "graduation_date": edu.graduation_date,
                "gpa": edu.gpa,
            }
            return e
        except DoesNotExist:
            raise IndexError("No item exists at this index.")

    def get_experience(self) -> List[Dict[str, str]]:
        """"""
        resp = []
        for ctr in range(1, 99):
            try:
                resp.append(self.get_experience_item(ctr))
            except IndexError:
                break
        return resp

    def get_experience_item(self, index: int) -> Dict[str, str]:
        """"""
        try:
            exp = Job.get_by_id(index)
        except DoesNotExist:
            raise IndexError("No such experience exists in the DB.")
        resp = {
            "employer": exp.employer,
            "employer_summary": exp.employer_summary,
            "location": exp.location,
            "job_title": exp.job_title,
            "job_summary": exp.job_summary,
            "details": [],
            "highlights": [],
        }
        with suppress(DoesNotExist):
            for detail in exp.details:
                resp["details"].append(detail.detail)
        with suppress(DoesNotExist):
            for hl in exp.highlights:
                resp["highlights"].append(hl.highlight)
        return resp

    def get_all_preferences(self) -> Dict[str, str]:
        """
        Retrieves all preferences stored in the database.

        Args:
            None
        Returns:
            A dict containing the k/v pairs of all preferences and values.
        """
        prefs = Preference.select()
        resp = {}
        for pref in prefs:
            resp[pref.preference] = pref.value
        return prefs

    def get_preference(self, preference: str) -> str:
        """
        Retrieves the value of a specified preference.

        Args:
            preference: A string specifying the title of a preference (e.g. `OS`)
        Returns:
            A string specifying the value of the requested preference.
        Raises:
            KeyError: No value for the given preference is stored in the DB.
        """
        try:
            pref = Preference.get(Preference.preference == preference)
            return pref.value
        except DoesNotExist:
            raise KeyError(f"No value for {preference} stored in the DB.")

    def add_preference(self, preference: str, value: str) -> Dict[str, str]:
        """
        Adds a new preference to the preferences list.

        Args:
            preference: A string specifying the title of the preference (e.g. `OS`)
            value: A string specifying the preference itself (e.g. `Arch Linux`)
        Returns:
            A dict containing the DB values of prefrerence and value as well as whether
                the DB entry needed to be created (i.e. whether the pref/value pair
                did not exist).
        """
        pref, created = Preference.get_or_create(preference=preference, value=value)
        return {"preference": pref.preference, "value": pref.value, "created": created}

    def get_certifications(self, valid_only: bool = False) -> List[Dict[str, str]]:
        """
        Retrieves all configured certifications (or optionally only currently-valid
            certifications).

        Args:
            valid_only: A boolean specifying whether to limit the results to only
                currently-valid certifications (optional, defaults to False)
        Returns:
            A list of certifications and their info.
        """
        if valid_only:
            certifications = Certification.select().where(Certification.valid)
        else:
            certifications = Certification.select()
        resp = []
        for c in certifications:
            cert = {
                "cert": c.cert,
                "full_name": c.full_name,
                "time": c.time,
                "valid": c.valid,
                "progress": c.progress,
            }
            resp.append(cert)
        return resp

    def get_certification_by_name(self, certification: str) -> Dict[str, str]:
        """
        Retrieves information about a specified certification.

        Args:
            certification: A string specifying the name of the certification
        Returns:
            A dict containing information about the requested certification.
        Raises:
            KeyError: The certification does not exist in the DB.
        """
        try:
            c = Certification.get(Certification.cert == certification)
            resp = {
                "cert": c.cert,
                "full_name": c.full_name,
                "time": c.time,
                "valid": c.valid,
                "progress": c.progress,
            }
            return resp
        except DoesNotExist:
            raise KeyError("Certification not implemented in the DB.")

    def get_side_projects(self) -> List[Dict[str, str]]:
        """
        Retrieves information about all side projects stored in the DB.

        Args:
            None
        Returns:
            A list with info about each configured side project.
        """
        projects = SideProject.select()
        resp = []
        for p in projects:
            project = {"title": p.title, "tagline": p.tagline, "link": p.link}
            resp.append(project)
        return resp

    def get_side_project(self, project: str) -> Dict[str, str]:
        """
        Retrieves information about the requested side project.

        Args:
            project: A string specifying the title of the project to look up
        Returns:
            A dict containing details about the request project.
        Raises:
            KeyError: The requested project does not exist in the DB.
        """
        try:
            p = SideProject.get(SideProject.title == project)
            resp = {"title": p.title, "tagline": p.tagline, "link": p.link}
            return resp
        except DoesNotExist:
            raise KeyError("The requested project does not exist.")

    def get_technical_interests(self) -> List[str]:
        """
        Retrives a list of all configured technical interests.

        Args:
            None
        Returns:
            A list of all configured technical interests.
        """
        return [interest.interest for interest in TechnicalInterest.select()]

    def get_personal_interests(self) -> List[str]:
        """
        Retrieves a list of all configured personal interests.

        Args:
            None
        Returns:
            A list of all configured technical interests.
        """
        return [interest.interest for interest in PersonalInterest.select()]

    def get_social_links(self) -> Dict[str, str]:
        """
        Retrieves all social links.

        Args:
            None
        Returns:
            A dict containing a link to all configured social platforms.
        """
        links = SocialLink.select()
        resp = {}
        for link in links:
            resp[link.platform] = link.link
        return resp

    def get_social_link(self, platform: str) -> Dict[str, str]:
        """
        Retrives a link to the requested social platform.

        Args:
            platform: A string specifying the desired social platform whose link to
                return.
        Returns:
            A dict containing the link to the requested platform.
        Raises:
            KeyError: The requested platform is not configured.
        """
        try:
            link = SocialLink.get(SocialLink.platform == platform)
            return {platform: link.link}
        except DoesNotExist:
            raise KeyError("The requested platform is not configured")
