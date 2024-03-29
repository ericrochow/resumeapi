#!/usr/bin/env python3
"""Database models and pydantic schemas for use with by the API."""
# pylint: disable=too-few-public-methods

from enum import Enum
import logging
import os
from pathlib import Path
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr
from sqlmodel import Field, SQLModel, UniqueConstraint, create_engine
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


class User(SQLModel, table=True):  # noqa: D101
    """User table and object model."""

    __table_args__ = (UniqueConstraint("username"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field()
    password: str
    disabled: bool = Field(default=False)


class Users(BaseModel):  # noqa: D101
    """Users object model."""

    __root__: List[User]

    class Config:  # pylint: disable=too-few-public-methods
        """Users configuration."""

        schema_extra = {
            "example": {
                "users": [
                    {"username": "leeroy", "disabled": True},
                    {"username": "jenkins", "disabled": False},
                ]
            }
        }

    # TODO: write function to redact the password hash before returning


class Token(BaseModel):  # noqa: D101
    """Token object model."""

    access_token: str
    token_type: Literal["bearer"]

    class Config:  # pylint: disable=too-few-public-methods
        """Token configuration."""

        schema_extra = {
            "example": {
                "access_token": "long_bearer_token_here",
                "token_type": "bearer",
            }
        }


class BasicInfo(SQLModel, table=True):  # noqa: D101
    """Basic info table and object model."""

    __table_args__ = (UniqueConstraint("fact"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    fact: str = Field()
    value: str

    class Config:  # noqa: D106
        """BasicInfo configuration."""

        schema_extra = {
            "example": {
                "fact": "name",
                "value": "John Jacobs",
            }
        }


class BasicInfos(BaseModel):  # noqa: D101
    """Basic info object model."""

    name: str
    pronouns: List[str]
    email: EmailStr
    phone: str
    about: str

    class Config:  # pylint: disable=too-few-public-methods
        """BasicInfos configuration."""

        schema_extra = {
            "example": {
                "name": "John Jacobs",
                "pronouns": "['they', 'them']",
                "email": "email@domain.tld",
                "phone": "+1 (555) 555-5555",
                "about": "I am job.",
            }
        }


class Education(SQLModel, table=True):  # noqa: D101
    """Education table and object model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    institution: str
    degree: str
    graduation_date: int
    gpa: float

    class Config:  # noqa: D106
        """Education configuration."""

        schema_extra = {
            "example": {
                "id": 1,
                "institution": "University of Oxford",
                "degree": "Bachelor of Fine Arts in Comma Usage",
                "graduation_date": 2001,
                "gpa": 4.0,
            }
        }


class Job(SQLModel, table=True):  # noqa: D101
    """Job table."""

    id: Optional[int] = Field(default=None, primary_key=True)
    employer: str
    employer_summary: str
    location: str
    job_title: str
    job_summary: str
    time: str

    class Config:  # noqa: D106
        """Job configuration."""

        schema_extra = {
            "example": {
                "id": 1,
                "employer": "Acme, LLC",
                "employer_summary": "Acme, LLC makes or sells something I think",
                "location": "Easytown, USA",
                "job_title": "Chief Scotch Officer",
                "job_summary": "Report to my uncle the CEO and attend meetings",
                "time": "2015-Present",
            }
        }


class JobResponse(BaseModel):  # noqa: D101
    """Job object model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    employer: str
    employer_summary: str
    location: str
    job_title: str
    job_summary: str
    time: str
    details: Optional[list]
    highlights: Optional[list]

    class Config:  # noqa: D106
        """JobResponse configuration."""

        schema_extra = {
            "example": {
                "id": 1,
                "employer": "Acme, LLC",
                "employer_summary": "Acme, LLC makes or sells something I think",
                "job_title": "Chief Scotch Officer",
                "job_summary": "Report to my uncle the CEO and attend meetings",
                "details": [{"id": 1, "detail": "Various duties as assigned"}],
                "highlights": [
                    {
                        "id": 1,
                        "highlight": "I once made my chair swivel around 64 times"
                        " without getting sick",
                    }
                ],
            }
        }


class JobHighlight(SQLModel, table=True):  # noqa: D101
    """Job highlight table and object model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    highlight: str
    job_id: Optional[int] = Field(default=None, foreign_key="job.id")


class JobDetail(SQLModel, table=True):  # noqa: D101
    """Job detail table and object model."""

    id: Optional[int] = Field(default=None, primary_key=True)
    detail: str
    job_id: Optional[int] = Field(default=None, foreign_key="job.id")


class Certification(SQLModel, table=True):  # noqa: D101
    """Certification table and object model."""

    __table_args__ = (UniqueConstraint("cert"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    cert: str = Field()
    full_name: str
    time: str
    valid: bool
    progress: int

    class Config:  # noqa: D106
        """Certification configuration."""

        schema_extra = {
            "example": {
                "cert": "CCIE",
                "full_name": "Cisco Certified Internetwork Expert",
                "time": "2001 - Present",
                "valid": True,
                "progress": 100,
            }
        }


class Competency(SQLModel, table=True):  # noqa: D101
    """Competency table and object model."""

    __table_args__ = (UniqueConstraint("competency"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    competency: str = Field()


class InterestType(SQLModel, table=True):  # noqa: D101
    """InterestType table and object model."""

    __table_args__ = (UniqueConstraint("interest_type"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    interest_type: str = Field(index=True)


class InterestTypes(str, Enum):  # noqa: D101
    """Enum of interest types."""

    personal = "personal"  # pylint: disable=invalid-name
    technical = "technical"  # pylint: disable=invalid-name


class Interest(SQLModel, table=True):  # noqa: D101
    """Interest table."""

    __table_args__ = (UniqueConstraint("interest"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    interest_type_id: Optional[int] = Field(default=None, foreign_key="interesttype.id")
    interest: str = Field()


class InterestsResponse(BaseModel):  # noqa: D101
    """Interest object model."""

    personal: Optional[List[str]]
    technical: Optional[List[str]]

    class Config:  # noqa: D106
        """InsterestsResponse configuration."""

        schema_extra = {
            "example": {
                "personal": ["Movies", "Sports", "Books"],
                "technical": ["Python", "Rust", "Routing"],
            }
        }


class Preference(SQLModel, table=True):  # noqa: D101
    """Preference table and object model."""

    __table_args__ = (UniqueConstraint("preference"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    preference: str = Field()
    value: str


class Preferences(BaseModel):  # noqa: D101
    """Preference object model."""

    OS: List[str]
    EDITOR: str
    TERMINAL: str
    COLOR_THEME: Optional[str]
    CODE_COMPLETION: Optional[str]
    CODE_STYLE: Optional[str]
    LANGUAGES: List[str]
    TEST_SUITES: List[str]

    class Config:  # noqa: D106
        """Preferences configuration."""

        schema_extra = {
            "example": {
                "OS": ["Favorite OS 1", "Favorite OS 2"],
                "EDITOR": "Name of preferred text editor/IDE",
                "TERM": "Terminal emulator of preference",
                "COLOR_SCHEME": "Favorite text color scheme",
                "CODE_COMPLETION": "Favorite code completion engine",
                "CODE_STYLE": "Preferred code style if applicable",
                "LANGUAGES": ["Language 1", "Language 2"],
                "TEST_SUITES": ["Test suite 1", "Test Suite 2"],
            }
        }


class SideProject(SQLModel, table=True):  # noqa: D101
    """Side project table and object model."""

    __table_args__ = (UniqueConstraint("title"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field()
    tagline: str
    link: str

    class Config:  # noqa: D106  # pylint: disable=too-few-public-methods
        """SideProject configuration."""

        schema_extra = {
            "example": {
                "title": "my_project",
                "tagline": "Useful description of the project",
                "link": "https://github.com/my_user/my_project",
            }
        }


class SocialLinkEnum(str, Enum):  # noqa: D101
    """Enum of available social links."""

    LinkedIn = "linkedin"  # pylint: disable=invalid-name
    Github = "github"  # pylint: disable=invalid-name
    Twitter = "twitter"  # pylint: disable=invalid-name
    Matrix_im = "matrix_im"  # pylint: disable=invalid-name
    Website = "website"  # pylint: disable=invalid-name
    Resume = "resume"  # pylint: disable=invalid-name
    Facebook = "facebook"  # pylint: disable=invalid-name


class SocialLink(SQLModel, table=True):  # noqa: D101
    """Social link table and object model."""

    __table_args__ = (UniqueConstraint("platform"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str = Field()
    link: str

    class Config:  # noqa: D106
        """SocialLink configuration."""

        schema_extra = {
            "platform": "linkedin",
            "link": "https://linkedin.com/in/my_user",
        }


class Skill(SQLModel, table=True):  # noqa: D101
    """Skill table and object model."""

    __table_args__ = (UniqueConstraint("skill"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    skill: str = Field()
    level: int

    class Config:  # noqa: D106
        """Skill configuration."""

        schema_extra = {"example": {"skill": "Git", "level": 75}}


class FullResume(BaseModel):  # noqa: D101
    """Full resume object model with all configured sections."""

    basic_info: BasicInfos
    certifications: List[Certification]
    competencies: List[str]
    education: List[Education]
    experience: List[Job]
    interests: Dict[InterestTypes, List[str]]
    preferences: Preferences
    side_projects: List[SideProject]
    skills: List[Skill]
    social_links: List[SocialLink]


def configure_engine(engine_echo: bool = False) -> Engine:
    """
    Generate the SQLAlchemy engine for use by the API.

    :param engine_echo: Whether to have the SQL output echo'd by the engine
    :type engine_echo: bool, optional
    :return: Engine used by SQLModel
    :rtype: sqlalchemy.engine.Engine
    """
    db_type = os.getenv("DB_TYPE", default="sqlite")
    db_host = os.getenv("DB_HOST", default="resumedb")
    db_name = os.getenv("DB_NAME", default="resume")
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")

    if db_type.lower() == "sqlite":
        logger.debug("sqlite configuration db type detected")
        default_path = Path(__file__).parent.parent
        sqlite_file = os.getenv(
            "SQLITE_DB_PATH", default=f"{default_path}/{db_name}.db"
        )
        logger.debug("attempting to use sqlite database stored at %s", sqlite_file)
        sql_engine = create_engine(f"sqlite:///{sqlite_file}", echo=engine_echo)
    elif db_type.lower() == "postgresql":
        logger.debug("postgresql configuration db type detected")
        db_port = os.getenv("DB_PORT", default="5432")
        sql_engine = create_engine(
            f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}",
            echo=engine_echo,
        )
    else:
        raise ValueError(
            f"Unsupported database type: {db_type}. Please use one of sqlite or"
            " postgres."
        )
    logger.debug("creating all tables that do not exist")
    SQLModel.metadata.create_all(sql_engine)
    logger.debug("finished creating tables")
    return sql_engine


engine = configure_engine()
