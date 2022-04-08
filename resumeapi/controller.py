#!/usr/bin/env python3

import ast
from contextlib import suppress
from datetime import datetime, timedelta
import logging
import os

from typing import List, Optional

from dotenv import load_dotenv
from jose import jwt  # noqa

from passlib.context import CryptContext
from sqlmodel import Session, select

import models


class AuthController:
    """Interact with authentication methods."""

    def __init__(self) -> None:
        load_dotenv()
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.secret_key = os.getenv("SECRET_KEY")
        self.algorithm = os.getenv("ALGORITHM")
        self.logger = logging.getLogger(__name__)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify that the given password matches the hash stored in the database.

        :param plain_password: The plaintext password
        :type plain_password: str
        :param hashed_password: The bcrypt-hashed password
        :type hashed_password: str
        :return: Whether the password matches
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Provide a bcrypt hash of the given plaintext password.

        :param password: A plain-text password to be hashed
        :type password: str
        :return: The bcrypt-hashed password
        :rtype: str
        """
        return self.pwd_context.hash(password)

    @staticmethod
    def get_user(username: str) -> models.User:
        """
        Get information about the requested user.

        :param username: The username of the user to look up
        :type username: str
        :return: The requested user
        :rtype: models.py.bak.User
        :raises KeyError: No such user exists.
        """
        with Session(models.engine) as session:
            statement = select(models.User).where(models.User.username == username)
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("No such user exists")
            return results

    def authenticate_user(self, username: str, password: str) -> models.User:
        """
        Authenticate a user.

        :param username:
        :type username: str
        :param password:
        :type password: str
        :return: The authenticated user
        :rtype: models.py.bak.User
        :raises KeyError: No such user exists.
        """
        user = self.get_user(username)
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

        :param data: Username of the user whose token to generate
        :type data: dict
        :param expires_delta: Maximum lifetime of the token
        :type expires_delta: timedelta, optional
        :return: An encoded JSON web token.
        :rtype: str
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
    ) -> models.User:
        """
        Create a new user in the database.

        :param username: The user's email address
        :type username: str
        :param password: The plaintext password of the user
        :type password: str
        :param disabled: Whether the user should be active, defaults to False
        :type disabled: bool, optional
        :return: The created user
        :rtype: models.py.bak.User
        """
        with Session(models.engine) as session:
            user = models.User(
                username=username.lower(),
                password=self.get_password_hash(password),
                disabled=disabled,
            )
            session.add(user)
            session.commit()
            session.refresh(user)
        return user

    def deactivate_user(self, username: str) -> models.User:
        """
        Deactivate an existing user in the DB.

        :param username: The username of the user to disable
        :type username: str
        :return: The deactivated user
        :rtype: models.py.bak.User
        :raises KeyError: The user does not exist in the DB
        """
        self.logger.info("Attempting to deactivate user %s", username)
        with Session(models.engine) as session:
            statement = select(models.User).where(
                models.User.username == username.lower()
            )
            results = session.exec(statement)
            user = results.one()
            if not user:
                self.logger.error(
                    "Failed to deactivate user %s because they are not in the db!",
                    username,
                )
                raise KeyError("The requested user does not exist!")
            user.disabled = True
            session.commit()
            session.refresh(user)
            self.logger.info("Successfully deactivated user %s", username)
            return user


class ResumeController:
    """Interact with resume methods."""

    def __init__(self) -> None:
        pass

    @staticmethod
    def get_all_users() -> List[models.User]:
        """
        List all configured users for auditing purposes.

        :return: Username and disabled status of each user
        :rtype: dict
        """
        with Session(models.engine) as session:
            statement = select(models.User)
            results = session.exec(statement).all()
            return results

    @staticmethod
    def get_basic_info() -> models.BasicInfos:
        """
        List all configured basic info facts.

        :return: All facts
        :rtype: dict
        """
        with Session(models.engine) as session:
            statement = select(models.BasicInfo)
            results = session.exec(statement).all()
            repsonse_dict = dict()
            for info in results:
                try:
                    repsonse_dict[info.fact] = ast.literal_eval(info.value)
                except (ValueError, SyntaxError):
                    repsonse_dict[info.fact] = info.value
            resp = models.BasicInfos.parse_obj(repsonse_dict)
            return resp

    @staticmethod
    def get_basic_info_item(fact: str) -> models.BasicInfo:
        """
        Find the value of the requested basic value fact.

        :param fact: The fact to look up (e.g. name)
        :type fact: str
        :return: The requested fact
        :rtype dict:
        :raises KeyError: The requested fact does not exist.
        """
        with Session(models.engine) as session:
            statement = select(models.BasicInfo).where(models.BasicInfo.fact == fact)
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("Fact does not exist in the DB.")
            return results

    @staticmethod
    def upsert_basic_info_item(item: models.BasicInfo) -> models.BasicInfo:
        """
        Create or update an existing fact.

        :param item: k/v pair of the fact "fact" and the "value"
        :type item: dict
        :return: The k/v pair
        :rtype: dict
        """
        with Session(models.engine) as session:
            statement = select(models.BasicInfo).where(
                models.BasicInfo.fact == item.fact
            )
            fact = session.exec(statement).first()
            if fact is None:
                fact = models.BasicInfo()
            for key, value in item.dict(exclude_unset=True).items():
                setattr(fact, key, value)
            session.add(fact)
            session.commit()
            session.refresh(fact)
            return fact

    @staticmethod
    def delete_basic_info_item(fact: str) -> None:
        """
        Delete an existing fact.

        :param fact: The name of the fact
        :type fact: str
        :raises KeyError: The fact does not exist in the DB.
        """
        with Session(models.engine) as session:
            statement = select(models.BasicInfo).where(models.BasicInfo.fact == fact)
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested fact does not exist")
            session.delete(results)
            session.commit()

    @staticmethod
    def get_all_education_history() -> List[models.Education]:
        """
        Retrieve all education history objects stored in the database.

        :return: All education history objects.
        :rtype: list
        """
        with Session(models.engine) as session:
            statement = select(models.Education)
            results = [e[0] for e in session.execute(statement).all()]
            return results

    @staticmethod
    def get_education_item(index: int) -> models.Education:
        """
        Retrieve and education object by its id (index).

        :param index: The ID of the education entry
        :type index: int
        :return: Details about the requested education item.
        :rtype: dict
        :raises IndexError: No item exists at this index.
        """
        with Session(models.engine) as session:
            results = session.get(models.Education, index)
            if not results:
                raise IndexError("No item exists at this index.")
            return results

    @staticmethod
    def upsert_education_item(edu: models.Education) -> models.Education:
        """
        Create or update an education item.

        :param edu: An Education schema object
        :type edu: schema.Education
        :return: Details of the new or updated education item
        :rtype schema.Education
        """
        with Session(models.engine) as session:
            statement = (
                select(models.Education)
                .where(models.Education.institution == edu.institution)
                .where(
                    models.Education.degree == edu.degree,
                    models.Education.graduation_date == edu.graduation_date,
                )
            )
            results = session.exec(statement).first()
            if results is None:
                results = edu
            for key, value in results.dict(exclude_unset=True).items():
                setattr(results, key, value)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_education_item(index: int) -> None:
        """
        Delete an existing education item.

        :param index: The ID of the education items to delete
        :type index: int
        :raises KeyError: No item exists at this index.
        """
        with Session(models.engine) as session:
            item = session.get(models.Education, index)
            if not item:
                raise IndexError("No item exists at this index.")
            session.delete(item)
            session.commit()

    @classmethod
    def get_experience(cls) -> List[models.Job]:
        """
        Retrieve a list of previous jobs.

        :return: All previous jobs and their related details.
        :rtype list:
        """
        resp = []
        with Session(models.engine) as session:
            statement = select(models.Job)
            results = session.exec(statement).all()
            for job in results:
                j = ResumeController.get_experience_item(job.id)
                resp.append(j)
            return results

    @classmethod
    def get_experience_item(cls, job_id: int) -> models.JobResponse:
        """
        Retrieve details for previous job.

        :param job_id: The ID of the experience item to return
        :type job_id: int
        :return: The details of the job
        :rtype: schema.JobResponse
        """
        with Session(models.engine) as session:
            results = session.get(models.Job, job_id)
            if results is None:
                raise IndexError("No such experience exists in the DB.")
            results = models.JobResponse.parse_obj(results.dict())
            details = ResumeController.get_experience_detail(job_id)
            if details is not None:
                setattr(results, "details", [])
                for detail in details:
                    results.details.append(detail)
            highlights = ResumeController.get_experience_highlight(job_id)
            if highlights is not None:
                setattr(results, "highlights", [])
                for hl in highlights:
                    results.highlights.append(hl)
            return results

    @staticmethod
    def get_experience_detail(job_id: int) -> List[models.JobDetail]:
        """
        Gather details about the requested Job.

        :param job_id: The ID of the job whose details to return
        :type job_id: int
        :return: All details for the requested Job
        :rtype: list
        """
        with Session(models.engine) as session:
            statement = select(models.JobDetail).where(
                models.JobDetail.job_id == job_id
            )
            details = session.exec(statement).all()
            return details

    @staticmethod
    def get_experience_highlight(job_id: int) -> List[models.JobHighlight]:
        """
        Gather highlights from the requested Job.

        :param job_id: The ID of the job whose highlights to return
        :type job_id: int
        :return: All highlights for the requested Job
        :rtype: list
        """
        with Session(models.engine) as session:
            statement = select(models.JobHighlight).where(
                models.JobHighlight.job_id == job_id
            )
            details = session.exec(statement).all()
            return details

    @staticmethod
    def upsert_experience_item(job: models.Job) -> models.Job:
        """
        Create or update an experience item.

        :param job: The job to add to the job history
        :type job: schema.Job
        :return: The job added to the job history
        :rtype: schema.Job
        """
        with Session(models.engine) as session:
            statement = select(models.Education).where(
                models.Job.employer == job.employer
            )
            results = session.exec(statement).first()
            if results is None:
                results = job
            for key, value in job.dict(exclude_unset=True).items():
                setattr(results, key, value)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_experience_item(index: int) -> None:
        """
        Delete a Job item by the given index (id).

        :param index: The ID of the job to delete
        :type index: int
        :raises IndexError: No such item exists at this index.
        """
        with Session(models.engine) as session:
            results = session.get(models.Job, index)
            if results is None:
                raise IndexError("No item exists at this index.")
            session.delete(results)
            session.commit()

    @staticmethod
    def upsert_job_detail(job_detail: models.JobDetail) -> models.JobDetail:
        """
        Create a new job detail.

        :param job_detail: Details to add to a job
        :type job_detail: schema.JobDetail
        :return: Updated job details
        :rtype: schema.JobDetail
        """
        with Session(models.engine) as session:
            statement = select(models.JobDetail).where(
                models.JobDetail.id == job_detail.id
            )
            results = session.exec(statement).first()
            if results is None:
                results = job_detail
            for key, value in job_detail.dict(exclude_unset=True).items():
                setattr(results, key, value)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_job_detail(job_detail_id: int) -> None:
        """
        Remove a job detail with the given ID.

        :param job_detail_id: The ID of the job detail to remove
        :type job_detail_id: int
        """
        with Session(models.engine) as session:
            results = session.get(models.BasicInfo, job_detail_id)
            if not results:
                raise KeyError("The requested job detail does not exist")
            session.delete(results)
            session.commit()

    @staticmethod
    def upsert_job_highlight(job_highlight: models.JobHighlight) -> models.JobHighlight:
        """
        Create or updates a job highlight.

        :param job_highlight: A highlight to add to a job
        :type job_highlight: models.py.bak.JobHighlight
        :return: The updated job highlight
        :rtype: models.py.bak.JobHighlight
        """
        with Session(models.engine) as session:
            results = session.get(models.JobHighlight.id, job_highlight.id)
            if results is None:
                results = job_highlight
            for key, value in job_highlight:
                setattr(results, key, value)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_job_highlight(job_highlight_id: int) -> None:
        """
        Remove a job highlight with the given ID.

        :param job_highlight_id: The ID of the job highlight to remove
        :type job_highlight_id: int
        """
        with Session(models.engine) as session:
            results = session.get(models.BasicInfo, job_highlight_id)
            if results is None:
                raise KeyError("The requested job highlight does not exist")
            session.delete(results)
            session.commit()

    @staticmethod
    def get_all_preferences() -> models.Preferences:
        """
        Retrieve all preferences stored in the database.

        :return: k/v pairs of all preferences and values
        :rtype: schema.Preferences
        """
        with Session(models.engine) as session:
            statement = select(models.Preference)
            results = session.exec(statement).all()
            model = dict()
            for r in results:
                try:
                    model[r.preference] = ast.literal_eval(r.value)
                except (ValueError, SyntaxError):
                    model[r.preference] = r.value
            resp = models.Preferences.parse_obj(model)
            return resp

    @staticmethod
    def get_preference(preference: str) -> models.Preference:
        """
        Retrieve the value of a specified preference.

        :param preference: The title of a preference (e.g. `OS`)
        :type preference: str
        :return: The value of the requested preference
        :rtype: str
        :raises KeyError: No value for the given preference is stored in the DB.
        """
        with Session(models.engine) as session:
            statement = select(models.Preference).where(
                models.Preference.preference == preference
            )
            results = session.exec(statement).first()
            if results is None:
                raise KeyError(f"No value for {preference} stored in the DB.")
            return results

    @staticmethod
    def upsert_preference(preference: models.Preference) -> models.Preference:
        """
        Create or updates an existing preference.

        :param preference: A k/v pair of a preference and its value
        :type preference: schema.Preference
        ;return: The updated preference and value
        :rtype: models.py.bak.Preference
        """
        with Session(models.engine) as session:
            statement = select(models.Preference).where(
                models.Preference.preference == preference.preference
            )
            results = session.exec(statement).first()
            if results is None:
                results = preference
            for key, value in preference.dict(exclude_unset=True).items():
                setattr(results, key, value)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_preference(preference: str) -> None:
        """
        Delete a preference item.

        :param preference: The name of the preference to be deleted
        :type preference: str
        :raises KeyError: The requested preference does not exist.
        """
        with Session(models.engine) as session:
            statement = select(models.Preference).where(
                models.Preference.preference == preference
            )
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested preference does not exist")
            session.delete(results)
            session.commit()

    @staticmethod
    def get_certifications(valid_only: bool = False) -> List[models.Certification]:
        """
        Retrieve all configured certifications.

        Can optionally filter to only currently-valid certifications.

        :param valid_only: Whether to limit the results to only currently-valid certifications, defaults to False
        :type valid_only: bool, optional
        :return: All certifications and their info
        :rtype: List[schema.Certification]
        """
        with Session(models.engine) as session:
            statement = select(models.Certification)
            if valid_only:
                statement = statement.where(models.Certification.valid)
            results = session.exec(statement).all()
            return results

    @staticmethod
    def get_certification_by_name(certification: str) -> models.Certification:
        """
        Retrieve information about a specified certification.

        :param certification: The name of the certification
        :type certification: str
        :return: Information about the requested certification
        :rtype: schema.Certification
        :raises KeyError: The certification does not exist in the DB.
        """
        with Session(models.engine) as session:
            statement = select(models.Certification).where(
                models.Certification.cert == certification
            )
            results = session.exec(statement).first()
            if not results:
                raise KeyError("Certification not implemented in the DB.")
            return results

    @staticmethod
    def upsert_certification(
        certification: models.Certification,
    ) -> models.Certification:
        """
        Create or update a certification.

        :param certification: A certification to update or add
        :type certification: schema.Certification
        :return: The updated certification details
        :rtype: schema.Certification
        """
        with Session(models.engine) as session:
            statement = select(models.Certification).where(
                models.Certification.cert == certification.cert
            )
            results = session.exec(statement).first()
            if results is None:
                results = certification
            for key, value in certification.dict(exclude_unset=True).items():
                setattr(results, key, value)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_certification(cert: str) -> None:
        """
        Remove a certification by its name.

        :param cert: The name of the certification to remove
        :type cert: str
        :raises KeyError: The requested certification does not exist
        """
        with Session(models.engine) as session:
            statement = select(models.Certification).where(
                models.Certification.cert == cert
            )
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested certification does not exist")
            session.delete(results)
            session.commit()

    @staticmethod
    def get_side_projects() -> List[models.SideProject]:
        """
        Retrieve information about all side projects stored in the DB.

        :return: Info about each configured side project
        :rtype: schema.SideProjects
        """
        with Session(models.engine) as session:
            statement = select(models.SideProject)
            results = session.exec(statement).all()
            return results

    @staticmethod
    def get_side_project(project: str) -> models.SideProject:
        """
        Retrieve information about the requested side project.

        :param project: The title of the project to look up
        :type project: str
        :return: Details about the requested project
        :rtype: schema.SideProject
        :raises KeyError: The requested project does not exist in the DB
        """
        with Session(models.engine) as session:
            statement = select(models.SideProject).where(
                models.SideProject.title == project
            )
            results = session.exec(statement).first()
            if not results:
                raise KeyError("The requested project does not exist.")
            return results

    @staticmethod
    def upsert_side_project(side_project: models.SideProject) -> models.SideProject:
        """
        Insert or update project depending on whether it already has an entry.

        :param side_project: Details of the side project
        :type side_project: schema.SideProject
        :return: The updated or created side project
        :rtype: models.py.bak.SideProject
        """
        with Session(models.engine) as session:
            statement = select(models.SideProject).where(
                models.SideProject.title == side_project.title
            )
            results = session.exec(statement).first()
            if results is None:
                results = side_project
            for key, value in side_project.dict(exclude_unset=True).items():
                setattr(results, key, value)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_side_project(title: str) -> None:
        """
        Delete a side project given the title of the project.

        :param title: The title of the project.
        :type title: str
        :raises KeyError: The requested side project does not exist.
        """
        with Session(models.engine) as session:
            statement = select(models.SideProject).where(
                models.SideProject.title == title
            )
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested side project does not exist")
            session.delete(results)
            session.commit()

    @staticmethod
    def get_interests_by_category(category: str) -> List[models.Interest]:
        """
        Retrieve a list of all configured technical interests.

        :param category: The category of interest to return
        :type category: str
        :return: All configured interests of the requested category
        :rtype: dict
        """
        with Session(models.engine) as session:
            statement = (
                select(models.Interest)
                .join(models.InterestType, isouter=True)
                .where(models.InterestType.interest_type == category)
            )
            results = session.exec(statement).all()
        return results

    @staticmethod
    def upsert_interest(
        category: models.InterestTypes, interest: str
    ) -> models.Interest:
        """
        Add a new interest.

        :param category: The category of the interest
        :type category: str
        :param interest: The value of the interest
        :type interest: str
        :return: The updated or created interest
        :rtype: models.py.bak.Interest
        """
        with Session(models.engine) as session:
            statement = select(models.InterestType).where(
                models.InterestType.interest_type == category
            )
            category_id = session.exec(statement).one()
            statement = select(models.Interest).where(
                models.Interest.interest == interest
            )
            results = session.exec(statement).first()
            if results is None:
                results = models.Interest()
            setattr(results, "interest", interest)
            setattr(results, "interest_type_id", category_id.id)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_interest(interest: str) -> None:
        """
        Delete an interest.

        :param interest: The interest to remove
        :type interest: str
        :raises KeyError: The requested interest does not exist.
        """
        with Session(models.engine) as session:
            statement = select(models.Interest).where(
                models.Interest.interest == interest
            )
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested interest does not exist")
            session.delete(results)
            session.commit()

    @classmethod
    def get_all_interests(cls) -> models.InterestsResponse:
        """
        Retrieve all interests personal and technical.

        :return: All interests
        :rtype: dict
        """
        results = models.InterestsResponse()
        results.personal = [i.interest for i in ResumeController.get_interests_by_category("personal")]
        results.technical = [i.interest for i in ResumeController.get_interests_by_category("technical")]
        return results

    @staticmethod
    def get_social_links() -> List[models.SocialLink]:
        """
        Retrieve all social links.

        :return: Links to all configured social platforms.
        :rtype: dict
        """
        with Session(models.engine) as session:
            statement = select(models.SocialLink)
            results = session.exec(statement).all()
            return results

    @staticmethod
    def get_social_link(platform: str) -> models.SocialLink:
        """
        Retrieve a link to the requested social platform.

        :param platform: The desired social platform whose link to return
        :type platform: str
        :return: A link to the requested platform.
        :rtype: schema.SocialLink
        :raises KeyError: The requested platform is not configured.
        """
        with Session(models.engine) as session:
            statement = select(models.SocialLink).where(
                models.SocialLink.platform == platform
            )
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested platform is not configured")
            return results

    @staticmethod
    def upsert_social_link(social_link: models.SocialLink) -> models.SocialLink:
        """
        Add or update a social link.

        :param social_link: Info for a social platform
        :type social_link: models.py.bak.SocialLink
        :returns: The updated configuration for the social platform
        :rtype models.SocialLink:
        """
        with Session(models.engine) as session:
            statement = select(models.SocialLink).where(
                models.SocialLink.platform == social_link.platform
            )
            results = session.exec(statement).first()
            if results is None:
                results = social_link
            for key, value in social_link.dict(exclude_unset=True).items():
                setattr(results, key, value)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_social_link(platform: str) -> None:
        """
        Remove a social link given the platform.

        :param platform: The name of the social platform to remove
        :type platform: str
        :raises KeyError: The requested platform does not exist
        """
        with Session(models.engine) as session:
            statement = select(models.SocialLink).where(
                models.SocialLink.platform == platform
            )
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested platform does not exist")
            session.delete(results)
            session.commit()

    @staticmethod
    def get_skills() -> List[models.Skill]:
        """
        Retrieve a list of all configured skills.

        :return: All configured skills and their respective details
        :rtype: dict
        """
        with Session(models.engine) as session:
            statement = select(models.Skill)
            results = session.exec(statement).all()
        return results

    @staticmethod
    def get_skill(skill: str) -> models.Skill:
        """
        Retrieve details about the requested skill.

        Args:
            skill: A string specifying the desired skill
        :return: Details about the requested skill
        :rtype: dict
        :raises KeyError: The requested skill is not listed
        """
        with Session(models.engine) as session:
            statement = select(models.Skill).where(models.Skill.skill == skill)
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested skill does not exist (yet!)")
            return results

    @staticmethod
    def upsert_skill(skill: models.Skill) -> models.Skill:
        """
        Create a new skill or updates an existing skill.

        :param skill: Details of the skill to update or add
        :type: schema.Skill
        :return: Details about the updated skill
        :rtype: models.py.bak.Skill
        """
        with Session(models.engine) as session:
            statement = select(models.BasicInfo).where(
                models.Skill.skill == skill.skill
            )
            results = session.exec(statement).first()
            if results is None:
                results = skill
            for key, value in skill.dict(exclude_unset=True).items():
                setattr(results, key, value)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_skill(skill: str) -> None:
        """
        Delete a Skill.

        :param skill: The name of the skill to remove
        :type skill: str
        :raises KeyError: The requested skill does not exist
        """
        with Session(models.engine) as session:
            statement = select(models.Skill).where(models.Skill.skill == skill)
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested skill does not exist")
            session.delete(results)
            session.commit()

    @staticmethod
    def get_competencies() -> List[models.Competency]:
        """
        Retrieve a list of configured competencies.

        :return: All configured competencies.
        :rtype: list
        """
        with Session(models.engine) as session:
            statement = select(models.Competency)
            results = session.exec(statement).all()
            return results

    @staticmethod
    def upsert_competency(competency: str) -> models.Competency:
        """
        Create a new competency.

        :param competency: The competency to add
        :type competency: str
        :return: The updated competency
        :rtype: dict
        """
        with Session(models.engine) as session:
            statement = select(models.Competency).where(
                models.Competency.competency == competency
            )
            results = session.exec(statement).first()
            if results is None:
                results = models.Competency(competency=competency)
            session.add(results)
            session.commit()
            session.refresh(results)
            return results

    @staticmethod
    def delete_competency(competency: str) -> None:
        """
        Remove a competency string.

        :param competency: The competency to remove
        :param competency: str
        :raises KeyError: The requested competency does not exist.
        """
        with Session(models.engine) as session:
            statement = select(models.Competency).where(
                models.Competency.competency == competency
            )
            results = session.exec(statement).first()
            if results is None:
                raise KeyError("The requested competency does not exist")
            session.delete(results)
            session.commit()

    @classmethod
    def get_full_resume(cls) -> models.FullResume:
        """
        Assemble all elements of the resume into a single response.

        :return: All elements of the resume
        :rtype: modes.FullResume
        """
        # TODO: Use model instead of raw dict
        results = dict()
        results["basic_info"] = ResumeController.get_basic_info()
        results["experience"] = ResumeController.get_experience()
        results["education"] = ResumeController.get_all_education_history()
        results["certifications"] = ResumeController.get_certifications()
        results["side_projects"] = ResumeController.get_side_projects()
        results["interests"] = ResumeController.get_all_interests()
        results["social_links"] = ResumeController.get_social_links()
        results["skills"] = ResumeController.get_skills()
        results["preferences"] = ResumeController.get_all_preferences()
        results["competencies"] = ResumeController.get_competencies()
        response = models.FullResume.parse_obj(results)
        return response
