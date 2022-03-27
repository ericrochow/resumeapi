#!/usr/bin/env python3

import logging
import os
from pathlib import Path
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint, create_engine


logger = logging.getLogger(__name__)


class User(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("username"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field()
    password: str
    disabled: bool = Field(default=False)


class BasicInfo(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("fact"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    fact: str = Field()
    value: str


class Education(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    institution: str
    degree: str
    graduation_date: int
    gpa: float


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    employer: str
    employer_summary: str
    location: str
    job_title: str
    job_summary: str
    time: str


class JobHighlight(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    highlight: str
    job_id: Optional[int] = Field(default=None, foreign_key="job.id")


class JobDetail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    detail: str
    job_id: Optional[int] = Field(default=None, foreign_key="job.id")


class Certification(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("cert"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    cert: str = Field()
    full_name: str
    time: str
    valid: bool
    progress: int


class Competency(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("competency"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    competency: str = Field()


class PersonalInterest(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("interest"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    interest: str = Field()


class TechnicalInterest(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("interest"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    interest: str = Field()


class InterestType(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("interest_type"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    interest_type: str = Field(index=True)


class Interest(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("interest"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    interest_type_id: Optional[int] = Field(
        default=None, foreign_key="interesttype.id"
    )
    interest: str = Field()


class Preference(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("preference"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    preference: str = Field()
    value: str


class SideProject(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("title"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field()
    tagline: str
    link: str


class SocialLink(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("platform"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str = Field()
    link: str


class Skill(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("skill"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    skill: str = Field()
    level: int


def configure_engine(engine_echo: bool = False):
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
        engine = create_engine(f"sqlite:///{sqlite_file}", echo=engine_echo)
    elif db_type.lower() == "postgresql":
        logger.debug("postgresql configuration db type detected")
        db_port = os.getenv("DB_PORT", default=5432)
        engine = create_engine(
            f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}",
            echo=engine_echo,
        )
    else:
        raise ValueError(
            f"Unsupported database type: {db_type}. Please use one of sqlite or"
            " postgres."
        )
    logger.debug("creating all tables that do not exist")
    SQLModel.metadata.create_all(engine)
    logger.debug("finished creating tables")
    return engine


engine = configure_engine()
# session = Session(engine)
