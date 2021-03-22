#!/usr/bin/env python3

from contextlib import suppress
from datetime import datetime, timedelta
import logging
import os

from typing import Dict, List, Optional

from dotenv import load_dotenv
from jose import jwt
from peewee import DoesNotExist, Model
from passlib.context import CryptContext

from models import (
    BasicInfo,
    Certification,
    Competency,
    Education,
    Job,
    PersonalInterest,
    Preference,
    SideProject,
    Skill,
    SocialLink,
    TechnicalInterest,
    User as UserModel,
)

from schema import User


class AuthController:
    def __init__(self) -> None:
        load_dotenv()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = os.getenv("ALGORITHM")
        self.logger = logging.getLogger(__name__)
        self.logger.addHandler(logging.StreamHandler)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies that the given password matches the hash stored in the database.

        Args:
            plain_password: A string containing the plaintext password
            hashed_password: A string containing the bcrypt-hashed password
        Returns:
            A boolean specifying whether the password matches.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Provides a bcrypt hash of the given plaintext password.

        Args:
            password: A string containing a plain-text password to be hashed.
        Returns:
            A string containing the bcrypt-hashed password.
        """
        return self.pwd_context.hash(password)

    def get_user(self, username: str) -> UserModel:
        """
        Gets information about the requested user.

        Args:
            username: A string specifying the username of the user to look up.
        Returns:
            A User model of the requested user.
        Raises:
            KeyError: No such user exists.
        """
        try:
            return UserModel.get(UserModel.username == username)
        except DoesNotExist:
            raise KeyError("No such user exists")

    def authenticate_user(self, username: str, password: str) -> UserModel:
        """
        Authenticates a user.

        Args:
            username: A string containing the user's username
            password: A string containing the user's password
        Returns:
            A User model object of the authenticated user.
        Raises:
            KeyError: No such user exists.
        """
        with suppress(DoesNotExist):
            self.logger.debug("Looking for user %s", username)
            user = UserModel.get(UserModel.username == username)
            self.logger.debug("User %s found", user.username)
            if self.verify_password(password, user.password) and not user.disabled:
                self.logger.info("Successful authentication")
                return user
            self.logger.error("Incorrect password")

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Creates an access token for a user.

        Args:
            data: A dict containing the username of the user whose token to generate
            expires_delta: A timedelta object containing the maximum lifetime of the
                token (optional)
        Returns:
            A string containing an encoded JSON web token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_user(
        self, username: str, password: str, disabled: bool = False
    ) -> Model:
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
            username=username.lower(),
            password=self.get_password_hash(password),
            disabled=disabled,
        )
        return user

    def deactivate_user(self, username: str) -> None:
        """
        Deactivates an existing user in the DB.

        Args:
            username: A string specifying the username of the user to disable
        Returns:
            None
        Raises:
            KeyError: The user does not exist in the DB
        """
        self.logger.info("Attempting to deactivate user %s", username)
        try:
            user = UserModel.get(UserModel.username == username.lower())
            user.disabled = True
            user.save()
            self.logger.info("Successfully deactivated user %s", username)
        except DoesNotExist:
            self.logger.error(
                "Failed to deactivate user %s because they are not in the db!",
                username,
            )
            raise KeyError("The requested user does not exist!")


class ResumeController:
    def __init__(self) -> None:
        pass

    @staticmethod
    def get_all_users() -> List[Dict[str, str]]:
        """
        Lists all configured users for auditing purposes.

        Args:
            None
        Returns:
            A list of dictionaries containing the username and disabled status of each
                user.
        """
        users = {
            "users": [
                {"username": user.username, "disabled": user.disabled}
                for user in UserModel.select()
            ]
        }
        return users

    @staticmethod
    def get_basic_info() -> Dict[str, str]:
        """
        Lists all configured basic info facts.

        Args:
            None
        Returns:
            A dict containing each fact as a key/value pair.
        """
        info = BasicInfo.select()
        resp = {}
        for i in info:
            resp[i.fact] = i.value
        return resp

    @staticmethod
    def get_basic_info_item(fact: str) -> Dict[str, str]:
        """
        Finds the value of the requested basic value fact.

        Args:
            fact: A string specifying the fact to look up (e.g. name)
        Returns:
            A dict containing a single key/value pair for the requested item.
        Raises:
            KeyError: The requested fact does not exist.
        """
        try:
            info = BasicInfo.get(BasicInfo.fact == fact)
            return {info.fact: info.value}
        except DoesNotExist:
            raise KeyError("Fact does not exist in the DB.")

    @staticmethod
    def upsert_basic_info_item(item: Dict[str, str]) -> int:
        """
        Creates or updates an existing fact.

        Args:
            item: A dict containing the name of the fact "fact" and the value "value"
        Returns:
            An integer specifying the ID of the key/value pair.
        """
        query = BasicInfo.insert(fact=item.fact, value=item.value).on_conflict(
            conflict_target=[BasicInfo.fact],
            preserve=[BasicInfo.fact],
            update={BasicInfo.value: item.value},
        )
        return query.execute()

    @staticmethod
    def delete_basic_info_item(fact: str) -> None:
        """
        Deletes an existing fact.

        Args:
            fact: A string specifying the name of the fact
        Returns:
            An integer specifying the number of impacted rows in the DB.
        Raises:
            KeyError: The fact does not exist in the DB.
        """
        try:
            item = BasicInfo.get(BasicInfo.fact == fact)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested fact does not exist")

    @staticmethod
    def get_all_education_history() -> List[Dict[str, str]]:
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
                "edu_id": edu.id,
                "institution": edu.institution,
                "degree": edu.degree,
                "graduation_date": edu.graduation_date,
                "gpa": edu.gpa,
            }
            history.append(e)
        return history

    @staticmethod
    def get_education_item(index: int) -> Dict[str, str]:
        """
        Retrieves and education object by its id (index).

        Args:
            index:
        Returns:
            A dict containing details about the requested education item.
        Raises:
            IndexError: No item exists at this index.
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

    @staticmethod
    def upsert_education_item(edu: Dict[str, str]) -> int:
        """"""
        query = Education.insert(
            institution=edu.institution,
            degree=edu.degree,
            graduation_date=edu.graduation_date,
            gpa=edu.gpa,
        ).on_conflict(
            conflict_target=[Education.institution, Education.degree],
            preserve=[Education.institution, Education.degree],
            update={
                Education.graduation_date: edu.graduation_date,
                Education.gpa: edu.gpa,
            },
        )
        return query.execute()

    @staticmethod
    def delete_education_item(index: int) -> None:
        """"""
        try:
            item = Education.get_by_id(index)
            item.delete_instance()
        except DoesNotExist:
            raise IndexError("No item exists at this index.")

    @classmethod
    def get_experience(cls) -> List[Dict[str, str]]:
        """
        Retrieves a list of previous jobs.

        Args:
            None
        Returns:
            A list of previous jobs and their related details.
        """
        resp = []
        jobs = Job.select()
        for job in jobs:
            j = ResumeController.get_experience_item(job.id)
            resp.append(j)
        return resp

    @staticmethod
    def get_experience_item(job_id: int) -> Dict[str, str]:
        """
        Retrieves details for previous job.

        Args:
            job_id
        Returns:
            A dict containing the details of the job.
        """
        try:
            exp = Job.get_by_id(job_id)
        except DoesNotExist:
            raise IndexError("No such experience exists in the DB.")
        resp = {
            "job_id": exp.id,
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

    @staticmethod
    def upsert_experience_item(job: Dict[str, str]) -> int:
        """"""
        query = Education.insert(
            employer=job.employer,
            employer_summary=job.summary,
            location=job.location,
            job_title=job.job_title,
            job_summary=job.job_summary,
        ).on_conflict(
            conflict_target=[Job.employer, Job.job_title],
            preserve=[Job.employer, Job.location, Job.job_title],
            update={
                Job.employer_summary: job.employer_summary,
                Job.job_summary: job.job_summary,
            },
        )
        return query.execute()

    @staticmethod
    def delete_experience_item(index: int):
        try:
            item = Job.get_by_id(index)
            item.delete_instance()
        except DoesNotExist:
            raise IndexError("No item exists at this index.")

    @staticmethod
    def upsert_job_detail():
        pass

    @staticmethod
    def delete_job_detail():
        pass

    @staticmethod
    def upsert_job_highlight():
        pass

    @staticmethod
    def delete_job_highlight():
        pass

    @staticmethod
    def get_all_preferences() -> Dict[str, str]:
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

    @staticmethod
    def get_preference(preference: str) -> str:
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

    @staticmethod
    def add_preference(preference: str, value: str) -> Dict[str, str]:
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

    @staticmethod
    def upsert_preference():
        pass

    @staticmethod
    def delete_preference():
        pass

    @staticmethod
    def get_certifications(valid_only: bool = False) -> List[Dict[str, str]]:
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

    @staticmethod
    def get_certification_by_name(certification: str) -> Dict[str, str]:
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

    @staticmethod
    def upsert_certification():
        pass

    @staticmethod
    def delete_certification():
        pass

    @staticmethod
    def get_side_projects() -> List[Dict[str, str]]:
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

    @staticmethod
    def get_side_project(project: str) -> Dict[str, str]:
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

    @staticmethod
    def upsert_side_project():
        pass

    @staticmethod
    def delete_side_project():
        pass

    @staticmethod
    def get_technical_interests() -> List[str]:
        """
        Retrives a list of all configured technical interests.

        Args:
            None
        Returns:
            A list of all configured technical interests.
        """
        return {
            "technical": [interest.interest for interest in TechnicalInterest.select()]
        }

    @staticmethod
    def upsert_technical_interest():
        pass

    @staticmethod
    def delete_technical_interest():
        pass

    @staticmethod
    def get_personal_interests() -> List[str]:
        """
        Retrieves a list of all configured personal interests.

        Args:
            None
        Returns:
            A list of all configured technical interests.
        """
        return {
            "personal": [interest.interest for interest in PersonalInterest.select()]
        }

    @staticmethod
    def upsert_personal_interest():
        pass

    @staticmethod
    def delete_personal_interest():
        pass

    @classmethod
    def get_all_interests(cls) -> Dict[str, List[str]]:
        """"""
        return {
            **ResumeController.get_personal_interests(),
            **ResumeController.get_technical_interests(),
        }

    @staticmethod
    def get_social_links() -> Dict[str, str]:
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

    @staticmethod
    def get_social_link(platform: str) -> Dict[str, str]:
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

    @staticmethod
    def upsert_social_link():
        pass

    @staticmethod
    def delete_social_link():
        pass

    @staticmethod
    def get_skills() -> Dict[str, List[Dict[str, str]]]:
        """
        Retrives a list of all configured skills.

        Args:
            None
        Returns:
            A list of configured skills and their respective details.
        """
        return {
            "skills": [
                {"skill": skill.skill, "level": skill.level}
                for skill in Skill.select()
            ]
        }

    @staticmethod
    def get_skill(skill: str) -> Dict[str, str]:
        """
        Retrieves details about the requested skill.

        Args:
            skill: A string specifying the desired skill
        Returns:
            A dict contatining details about the requested skill
        Raises:
            KeyError: The requested skill is not listed.
        """
        try:
            details = Skill.get(Skill.skill == skill)
            return {"skill": details.skill, "level": details.level}
        except DoesNotExist:
            raise KeyError("The requested skill does not exist (yet!)")

    @staticmethod
    def upsert_skill():
        pass

    @staticmethod
    def delete_skill():
        pass

    @staticmethod
    def get_competencies() -> Dict[str, List[str]]:
        """
        Retrieves a list of configured competencies.

        Args:
            None
        Returns:
            A list of configured competencies.
        """
        return {"competencies": [comp.competency for comp in Competency.select()]}

    @staticmethod
    def upsert_competency():
        pass

    @staticmethod
    def delete_competency():
        pass
