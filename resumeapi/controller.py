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

import models
import schema


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
        Verify that the given password matches the hash stored in the database.

        Args:
            plain_password: A string containing the plaintext password
            hashed_password: A string containing the bcrypt-hashed password
        Returns:
            A boolean specifying whether the password matches.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Provide a bcrypt hash of the given plaintext password.

        Args:
            password: A string containing a plain-text password to be hashed.
        Returns:
            A string containing the bcrypt-hashed password.
        """
        return self.pwd_context.hash(password)

    def get_user(self, username: str) -> models.User:
        """
        Get information about the requested user.

        Args:
            username: A string specifying the username of the user to look up.
        Returns:
            A User model of the requested user.
        Raises:
            KeyError: No such user exists.
        """
        try:
            return models.User.get(models.User.username == username)
        except DoesNotExist:
            raise KeyError("No such user exists")

    def authenticate_user(self, username: str, password: str) -> models.User:
        """
        Authenticate a user.

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
            user = models.User.get(models.User.username == username)
            self.logger.debug("User %s found", user.username)
            if self.verify_password(password, user.password) and not user.disabled:
                self.logger.info("Successful authentication")
                return user
            self.logger.error("Incorrect password")

    def create_access_token(
        self, data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create an access token for a user.

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
        Create a new user in the database.

        Args:
            email: A string specifying the user's email address
            password: A string specifying the plaintext password of the user
            is_active: A boolean specifying whether the user should be active
                (optional, defaults to True)
        Returns:
            An object of the User class.
        """
        user = schema.User.create(
            username=username.lower(),
            password=self.get_password_hash(password),
            disabled=disabled,
        )
        return user

    def deactivate_user(self, username: str) -> None:
        """
        Deactivate an existing user in the DB.

        Args:
            username: A string specifying the username of the user to disable
        Returns:
            None
        Raises:
            KeyError: The user does not exist in the DB
        """
        self.logger.info("Attempting to deactivate user %s", username)
        try:
            user = models.User.get(models.User.username == username.lower())
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
        List all configured users for auditing purposes.

        Args:
            None
        Returns:
            A list of dictionaries containing the username and disabled status of each
                user.
        """
        users = {
            "users": [
                {"username": user.username, "disabled": user.disabled}
                for user in models.User.select()
            ]
        }
        return users

    @staticmethod
    def get_basic_info() -> Dict[str, str]:
        """
        List all configured basic info facts.

        Args:
            None
        Returns:
            A dict containing each fact as a key/value pair.
        """
        info = models.BasicInfo.select()
        resp = {}
        for i in info:
            resp[i.fact] = i.value
        return resp

    @staticmethod
    def get_basic_info_item(fact: str) -> Dict[str, str]:
        """
        Find the value of the requested basic value fact.

        Args:
            fact: A string specifying the fact to look up (e.g. name)
        Returns:
            A dict containing a single key/value pair for the requested item.
        Raises:
            KeyError: The requested fact does not exist.
        """
        try:
            info = models.BasicInfo.get(models.BasicInfo.fact == fact)
            return {info.fact: info.value}
        except DoesNotExist:
            raise KeyError("Fact does not exist in the DB.")

    @staticmethod
    def upsert_basic_info_item(item: Dict[str, str]) -> int:
        """
        Create or update an existing fact.

        Args:
            item: A dict containing the name of the fact "fact" and the value "value"
        Returns:
            An integer specifying the ID of the key/value pair.
        """
        query = models.BasicInfo.insert(fact=item.fact, value=item.value).on_conflict(
            conflict_target=[models.BasicInfo.fact],
            preserve=[models.BasicInfo.fact],
            update={models.BasicInfo.value: item.value},
        )
        return query.execute()

    @staticmethod
    def delete_basic_info_item(fact: str) -> None:
        """
        Delete an existing fact.

        Args:
            fact: A string specifying the name of the fact
        Returns:
            An integer specifying the number of impacted rows in the DB.
        Raises:
            KeyError: The fact does not exist in the DB.
        """
        try:
            item = models.BasicInfo.get(models.BasicInfo.fact == fact)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested fact does not exist")

    @staticmethod
    def get_all_education_history() -> List[Dict[str, str]]:
        """
        Retrieve all education history objects stored in the database.

        Args:
            None
        Returns:
            A list of all education history objects.
        """
        education = models.Education.select()
        history = []
        for edu in education:
            e = {
                "id": edu.id,
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
        Retrieve and education object by its id (index).

        Args:
            index:
        Returns:
            A dict containing details about the requested education item.
        Raises:
            IndexError: No item exists at this index.
        """
        try:
            edu = models.Education.get_by_id(index)
            e = {
                "id": edu.id,
                "institution": edu.institution,
                "degree": edu.degree,
                "graduation_date": edu.graduation_date,
                "gpa": edu.gpa,
            }
            return e
        except DoesNotExist:
            raise IndexError("No item exists at this index.")

    @staticmethod
    def upsert_education_item(edu: schema.Education) -> int:
        """"""
        query = models.Education.insert(
            institution=edu.institution,
            degree=edu.degree,
            graduation_date=edu.graduation_date,
            gpa=edu.gpa,
        ).on_conflict(
            conflict_target=[models.Education.institution, models.Education.degree],
            preserve=[models.Education.institution, models.Education.degree],
            update={
                models.Education.graduation_date: edu.graduation_date,
                models.Education.gpa: edu.gpa,
            },
        )
        return query.execute()

    @staticmethod
    def delete_education_item(index: int) -> None:
        """"""
        try:
            item = models.Education.get_by_id(index)
            item.delete_instance()
        except DoesNotExist:
            raise IndexError("No item exists at this index.")

    @classmethod
    def get_experience(cls) -> List[Dict[str, str]]:
        """
        Retrieve a list of previous jobs.

        Args:
            None
        Returns:
            A list of previous jobs and their related details.
        """
        resp = []
        jobs = models.Job.select()
        for job in jobs:
            j = ResumeController.get_experience_item(job.id)
            resp.append(j)
        return resp

    @staticmethod
    def get_experience_item(job_id: int) -> schema.Job:
        """
        Retrieve details for previous job.

        Args:
            job_id: An integer specifying the ID of the experience item to return
        Returns:
            A dict containing the details of the job.
        """
        try:
            exp = models.Job.get_by_id(job_id)
        except DoesNotExist:
            raise IndexError("No such experience exists in the DB.")
        resp = {
            "id": exp.id,
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
                resp["details"].append(
                    {"id": detail.get_id(), "detail": detail.detail}
                )
        with suppress(DoesNotExist):
            for hl in exp.highlights:
                resp["highlights"].append(
                    {"id": hl.get_id(), "highlight": hl.highlight}
                )
        return resp

    @staticmethod
    def upsert_experience_item(job: schema.Job) -> int:
        """"""
        query = models.Education.insert(
            employer=job.employer,
            employer_summary=job.summary,
            location=job.location,
            job_title=job.job_title,
            job_summary=job.job_summary,
        ).on_conflict(
            conflict_target=[models.Job.employer, models.Job.job_title],
            preserve=[models.Job.employer, models.Job.location, models.Job.job_title],
            update={
                models.Job.employer_summary: job.employer_summary,
                models.Job.job_summary: job.job_summary,
            },
        )
        return query.execute()

    @staticmethod
    def delete_experience_item(index: int) -> int:
        """
        Delete a Job item by the given index (id).

        Args:
            index: An integer specifying the ID of the job.
        Returns:
            An integer specifying the number of rows impacted by the operation.
        Raises:
            IndexError: No such item exists at this index.
        """
        try:
            item = models.Job.get_by_id(index)
            return item.delete_instance()
        except DoesNotExist:
            raise IndexError("No item exists at this index.")

    @staticmethod
    def upsert_job_detail(job_detail: schema.JobDetail) -> int:
        """
        Create a new job detail.

        Args:
            job_detail: A JobDetail object
        Returns:
            An integer indicating the ID of the newly-created job detail.
        """
        query = models.JobDetail.insert(
            id=job_detail.id, detail=job_detail.detail, job=job_detail.job
        ).on_conflict(
            conflict_target=[models.JobDetail.id],
            preserve=[models.JobDetail.id],
            update={
                models.JobDetail.detail: job_detail.job_detail,
                models.JobDetail.job: job_detail.job,
            },
        )
        return query.execute()

    @staticmethod
    def delete_job_detail(job_detail_id: int) -> int:
        """
        Remove a job detail with the given ID.

        Args:
            job_detail_id: An integer specifying the ID of the job detail to remove
        Returns:
            An integer indicating the number of job detail records impacted by the
                operation.
        """
        try:
            item = models.BasicInfo.get_by_id(job_detail_id)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested job detail does not exist")

    @staticmethod
    def upsert_job_highlight(job_highlight: schema.JobHighlight) -> int:
        """
        Create or updates a job highlight.

        Args:
            job_highlight: A JobHighlight model
        Returns:
            An integer specifying the ID of the job highlight.
        """
        query = models.JobHighlight.insert(
            id=job_highlight.id,
            highlight=job_highlight.job_highlight,
            job=job_highlight.job,
        ).on_conflict(
            conflict_target=[models.JobHighlight.id],
            preserve=[models.JobHighlight.id],
            update={
                models.JobHighlight.highlight: job_highlight.job_highlight,
                models.JobHighlight.job: job_highlight.job,
            },
        )
        return query.execute()

    @staticmethod
    def delete_job_highlight(job_highlight_id: int) -> int:
        """
        Remove a job highlight with the given ID.

        Args:
            job_highlight_id: An integer specifying the ID of the job highlight to
                remove
        Returns:
            An integer indicating the number of job highlight records affected by the
                operation.
        """
        try:
            item = models.BasicInfo.get_by_id(job_highlight_id)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested job highlight does not exist")

    @staticmethod
    def get_all_preferences() -> schema.Preferences:
        """
        Retrieve all preferences stored in the database.

        Args:
            None
        Returns:
            A dict containing the k/v pairs of all preferences and values.
        """
        prefs = models.Preference.select()
        resp = {}
        for pref in prefs:
            resp[pref.preference] = pref.value
        return resp

    @staticmethod
    def get_preference(preference: str) -> str:
        """
        Retrieve the value of a specified preference.

        Args:
            preference: A string specifying the title of a preference (e.g. `OS`)
        Returns:
            A string specifying the value of the requested preference.
        Raises:
            KeyError: No value for the given preference is stored in the DB.
        """
        try:
            pref = models.Preference.get(models.Preference.preference == preference)
            return pref.value
        except DoesNotExist:
            raise KeyError(f"No value for {preference} stored in the DB.")

    @staticmethod
    def upsert_preference(preference: schema.Preferences) -> int:
        """
        Create or updates an existing preference.

        Args:
            preference: A dict containing a preference and its value
        Returns:
            An integer specifying the ID of the preference object.
        """
        query = models.Preference.insert(
            preference=preference.preference, value=preference.value
        ).on_conflict(
            conflict_target=[models.Preference.preference],
            preserve=[models.Preference.preference],
            update={models.Preference.value: preference.value},
        )
        return query.execute()

    @staticmethod
    def delete_preference(preference: str) -> int:
        """
        Delete a preference item.

        Args:
            preference: A string specifying the preference to be deleted
        Returns:
            An integer specifying the number of rows modified.
        Raises:
            KeyError: The requested preference does not exist.
        """
        try:
            item = models.Preference.get(models.Preference.preference == preference)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested preference does not exist")

    @staticmethod
    def get_certifications(valid_only: bool = False) -> schema.CertificationHistory:
        """
        Retrieve all configured certifications.

        Can optionally filter to only currently-valid certifications.

        Args:
            valid_only: A boolean specifying whether to limit the results to only
                currently-valid certifications (optional, defaults to False)
        Returns:
            A list of certifications and their info.
        """
        if valid_only:
            certifications = models.Certification.select().where(
                models.Certification.valid
            )
        else:
            certifications = models.Certification.select()
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
    def get_certification_by_name(certification: str) -> schema.Certification:
        """
        Retrieve information about a specified certification.

        Args:
            certification: A string specifying the name of the certification
        Returns:
            A dict containing information about the requested certification.
        Raises:
            KeyError: The certification does not exist in the DB.
        """
        try:
            c = models.Certification.get(models.Certification.cert == certification)
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
    def upsert_certification(certification: schema.Certification) -> int:
        """
        Create or update a certification.

        Args:
            certification: A Certification object
        Returns:
            An integer indicating the ID of the certification object.
        """
        query = models.Certification.insert(
            cert=certification.cert,
            full_name=certification.full_name,
            time=certification.time,
            valid=certification.valid,
            progress=certification.progress,
        ).on_conflict(
            conflict_target=[models.Certification.cert],
            preserve=[models.Certification.cert],
            update={
                models.Certification.full_name: certification.full_name,
                models.Certification.time: certification.time,
                models.Certification.valid: certification.valid,
                models.Certification.progress: certification.valid,
            },
        )
        return query.execute()

    @staticmethod
    def delete_certification(cert: str) -> int:
        """
        Remove a certification by its name.

        Args
            cert: A string specifying the certification to remove
        Returns:
            An integer indicating the number of certifications impacted by the
                operation.
        Raises:
            KeyError: The requested certification does not exist
        """
        try:
            item = models.Certification.get(models.Certification.cert == cert)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested certification does not exist")

    @staticmethod
    def get_side_projects() -> schema.SideProjects:
        """
        Retrieve information about all side projects stored in the DB.

        Args:
            None
        Returns:
            A list with info about each configured side project.
        """
        projects = models.SideProject.select()
        resp = [
            {"title": p.title, "tagline": p.tagline, "link": p.link} for p in projects
        ]
        return resp

    @staticmethod
    def get_side_project(project: str) -> schema.SideProject:
        """
        Retrieve information about the requested side project.

        Args:
            project: A string specifying the title of the project to look up
        Returns:
            A dict containing details about the request project.
        Raises:
            KeyError: The requested project does not exist in the DB.
        """
        try:
            p = models.SideProject.get(models.SideProject.title == project)
            resp = {"title": p.title, "tagline": p.tagline, "link": p.link}
            return resp
        except DoesNotExist:
            raise KeyError("The requested project does not exist.")

    @staticmethod
    def upsert_side_project(side_project: schema.SideProjects) -> int:
        """
        Insert or update project depending on whether it already has an entry.

        Args:
            side_project: A dictionary containing the details of the side project
        Returns:
            An integer indicating the ID of the side proect entry.
        """
        query = models.SideProject.insert(
            title=side_project.title,
            tagline=side_project.tagline,
            link=side_project.link,
        ).on_conflict(
            conflict_target=[models.SideProject.title],
            preserve=[models.SideProject.title],
            update={
                models.SideProject.tagline: side_project.tagline,
                models.SideProject.link: side_project.link,
            },
        )
        return query.execute()

    @staticmethod
    def delete_side_project(title: str) -> int:
        """
        Delete a side project given the title of the project.

        Args:
            title: A string specifying the title of the project.
        Returns:
            An integer indicating the number of affected entries.
        Raises:
            KeyError: The requested side project does not exist.
        """
        try:
            item = models.SideProject.get(models.SideProject.title == title)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested side project does not exist")

    @staticmethod
    def get_interests_by_category(category: str) -> Dict[str, List[str]]:
        """
        Retrive a list of all configured technical interests.

        Args:
            A string specifying the category of interest to return
        Returns:
            A list of all configured interests of the requested category.
        """
        interests = (
            models.Interest.select(
                models.Interest.interest, models.InterestType.interest_type
            )
            .join(
                models.InterestType,
            )
            .where(models.InterestType.interest_type == category)
        )
        return {category: [interest.interest for interest in interests]}

    @staticmethod
    def upsert_interest(category: schema.InterestTypes, interest: str) -> int:
        """
        Add a new interest.

        Args:
            category: A string contining the category of the itnerest
            interest: A string containing the value of the interest
        Returns:
            An integer indicating the ID of the interest.
        """
        cat = models.InterestType.get(models.InterestType.interest_type == category).id
        query = models.Interest.insert(
            interest=interest, interest_type=cat
        ).on_conflict_ignore()
        return query.execute()

    @staticmethod
    def delete_interest(interest: str) -> int:
        """
        Delete an interest.

        Args:
            interest: A string specifying an interest to remove
        Returns:
            An integer indicating the number of interests affected by the operation.
        Raises:
            KeyError: The requested interest does not exist.
        """
        try:
            item = models.Interest.get(models.Interest.interest == interest)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested interest does not exist")

    @classmethod
    def get_all_interests(cls) -> Dict[str, List[str]]:
        """
        Retrieve all interests personal and technical.

        Args:
            None
        Retrns:
            A dict containing all interests.
        """
        return {
            **ResumeController.get_interests_by_category("technical"),
            **ResumeController.get_technical_by_category("personal"),
        }

    @staticmethod
    def get_social_links() -> schema.SocialLinks:
        """
        Retrieve all social links.

        Args:
            None
        Returns:
            A dict containing a link to all configured social platforms.
        """
        links = models.SocialLink.select()
        resp = []
        for link in links:
            resp.append({"platform": link.platform, "link": link.link})
        return resp

    @staticmethod
    def get_social_link(platform: str) -> schema.SocialLink:
        """
        Retrive a link to the requested social platform.

        Args:
            platform: A string specifying the desired social platform whose link to
                return.
        Returns:
            A dict containing the link to the requested platform.
        Raises:
            KeyError: The requested platform is not configured.
        """
        try:
            link = models.SocialLink.get(models.SocialLink.platform == platform)
            return {"platform": link.platform, "link": link.link}
        except DoesNotExist:
            raise KeyError("The requested platform is not configured")

    @staticmethod
    def upsert_social_link(social_link: schema.SocialLink) -> int:
        """
        Add or update a social link.

        Args:
            social_link: A SocialLink object containing the name of the platform and a
                link to the user's account on that platform
        Returns:
            An integer indicating the ID of the SocialLink object.
        """
        query = models.BasicInfo.insert(
            platform=social_link.platform, link=social_link.link
        ).on_conflict(
            conflict_target=[models.SocialLink.platform],
            preserve=[models.SocialLink.platform],
            update={models.SocialLink.link: social_link.link},
        )
        return query.execute()

    @staticmethod
    def delete_social_link(platform: str):
        """
        Remove a social link given the platform.

        Args:
            platform: A string specifying the social platform to remove
        Returns:
            An integer specifying the number of affected social links.
        Returns:
            KeyError: The requested platform does not exist.
        """
        try:
            item = models.BasicInfo.get(models.SocialLink.platform == platform)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested platform does not exist")

    @staticmethod
    def get_skills() -> Dict[str, List[Dict[str, str]]]:
        """
        Retrive a list of all configured skills.

        Args:
            None
        Returns:
            A list of configured skills and their respective details.
        """
        return {
            "skills": [
                {"skill": skill.skill, "level": skill.level}
                for skill in models.Skill.select()
            ]
        }

    @staticmethod
    def get_skill(skill: str) -> schema.Skill:
        """
        Retrieve details about the requested skill.

        Args:
            skill: A string specifying the desired skill
        Returns:
            A dict contatining details about the requested skill
        Raises:
            KeyError: The requested skill is not listed.
        """
        try:
            details = models.Skill.get(models.Skill.skill == skill)
            return {"skill": details.skill, "level": details.level}
        except DoesNotExist:
            raise KeyError("The requested skill does not exist (yet!)")

    @staticmethod
    def upsert_skill(skill: schema.Skill) -> int:
        """
        Create a new skill or updates an existing skill.

        Args:
            skill: A Skill object specifying the name of the skill and the skill level.
        Returns:
            An integer indicating the ID of the skill.
        """
        query = models.BasicInfo.insert(skill=skill).on_conflict(
            conflict_target=[models.Skill.skill],
            preserve=[models.Skill.skill],
            update={models.Skill.level: skill.level},
        )
        return query.execute()

    @staticmethod
    def delete_skill(skill: str) -> int:
        """
        Delete a Skill.

        Args:
            skill: A string indicating the name of the skill to remove.
        Returns:
            An integer indicating the number of objects affected by the operation.
        Raises:
            KeyError: The requested skill does not exist.
        """
        try:
            item = models.Skill.get(models.Skill.skill == skill)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested skill does not exist")

    @staticmethod
    def get_competencies() -> Dict[str, List[str]]:
        """
        Retrieve a list of configured competencies.

        Args:
            None
        Returns:
            A list of configured competencies.
        """
        return {
            "competencies": [comp.competency for comp in models.Competency.select()]
        }

    @staticmethod
    def upsert_competency(competency: str) -> int:
        """
        Create a new competency.

        Args:
            competency: A string specifying the competency
        Returns:
            An integer indicating the ID of the competency.
        """
        query = models.Competency.insert(competency=competency).on_conflict_ignore()
        return query.execute()

    @staticmethod
    def delete_competency(competency: str) -> int:
        """
        Remove a competency string.

        Args:
            competency: A string specifying the competency to remove.
        Returns:
            An integer indicating the number of competency objects affected by the
                operation.
        Raises:
            KeyError: The requested competency does not exist.
        """
        try:
            item = models.Competency.get(models.Competency.competency == competency)
            return item.delete_instance()
        except DoesNotExist:
            raise KeyError("The requested competency does not exist")
