#!/usr/bin/env python3

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, EmailStr, HttpUrl


class BasicInfo(BaseModel):
    name: str
    pronouns: str
    email: EmailStr
    phone: str
    about: str

    class Config:
        schema_extra = {
            "example": {
                "name": "John Jacobs",
                "pronouns": "['they', 'them']",
                "email": "email@domain.tld",
                "phone": "+1 (555) 555-5555",
                "about": "I am job.",
            }
        }


class BasicInfoItem(BaseModel):
    fact: str
    value: str

    class Config:
        schema_extra = {
            "example": {
                "fact": "name",
                "value": "John Jacobs",
            }
        }


class Education(BaseModel):
    id: Optional[int]
    institution: str
    degree: str
    graduation_date: int
    gpa: float

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "institution": "University of Oxford",
                "degree": "Bachelor of Fine Arts in Comma Usage",
                "graduation_date": 2001,
                "gpa": 4.0,
            }
        }


class EducationHistory(BaseModel):
    history: List[Education]

    class Config:
        schema_extra = {
            "example": [
                {
                    "institution": "University of Oxford",
                    "degree": "Bachelor of Fine Arts in Comma Usage",
                    "graduation_date": 2001,
                    "gpa": 4.0,
                }
            ]
        }


class JobDetail(BaseModel):
    id: Optional[int]
    job: int
    job_detail: str


class JobHighlight(BaseModel):
    id: Optional[int]
    job: int
    job_highlight: str


class Job(BaseModel):
    id: Optional[int]
    employer: str
    employer_summary: str
    job_title: str
    job_summary: str
    details: Optional[List[str]]
    highlights: Optional[List[str]]

    class Config:
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


class JobHistory(BaseModel):
    experience: List[Job]

    class Config:
        schema_extra = {
            "example": [
                {
                    "id": 1,
                    "employer": "Acme, LLC",
                    "employer_summary": "Acme, LLC makes or sells something I think",
                    "job_title": "Chief Scotch Officer",
                    "job_summary": "Report to my uncle the CEO and attend meetings",
                    "details": ["Various duties as assigned"],
                    "highlights": [
                        "I once made my chair swivel around 64 times without getting"
                        " sick"
                    ],
                }
            ]
        }


class Certification(BaseModel):
    cert: str
    full_name: str
    time: str
    valid: bool
    progress: int

    class Config:
        schema_extra = {
            "example": {
                "cert": "CCIE",
                "full_name": "Cisco Certified Internetwork Expert",
                "time": "2001 - Present",
                "valid": True,
                "progress": 100,
            }
        }


class CertificationHistory(BaseModel):
    certification_history: List[Certification]

    class Config:
        schema_extra = {
            "example": [
                {
                    "cert": "CCIE",
                    "full_name": "Cisco Certified Internetwork Expert",
                    "time": "2001 - Present",
                    "valid": True,
                    "progress": 100,
                }
            ]
        }


class Competencies(BaseModel):
    competencies: List[str]

    class Config:
        schema_extra = {
            "example": {"competencies": ["synergy", "agility", "team player"]}
        }


class Interests(BaseModel):
    personal: List[str]
    technical: List[str]

    class Config:
        schema_extra = {
            "example": {
                "personal": ["Movies", "Sports", "Books"],
                "technical": ["Python", "Rust", "Routing"],
            }
        }


class PersonalInterests(BaseModel):
    personal: List[str]

    class Config:
        schema_extra = {"example": {"personal": ["Movies", "Sports", "Books"]}}


class TechnicalInterests(BaseModel):
    technical: List[str]

    class Config:
        schema_extra = {"example": {"technical": ["Python", "Rust", "Routing"]}}


class Preferences(BaseModel):
    OS: List[str]
    EDITOR: str
    TERM: str
    COLOR_THEME: Optional[str]
    CODE_COMPLETION: Optional[str]
    CODE_STYLE: Optional[str]
    LANGUAGES: List[str]
    TEST_SUITES: List[str]

    class Config:
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


class SideProject(BaseModel):
    title: str
    tagline: str
    link: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "title": "my_project",
                "tagline": "Useful description of the project",
                "link": "https://github.com/my_user/my_project",
            }
        }


class SideProjects(BaseModel):
    projects: List[SideProject]


class SocialLink(BaseModel):
    platform: str
    link: HttpUrl

    class Config:
        schema_extra = {
            "platform": "linkedin",
            "link": "https://linkedin.com/in/my_user",
        }


class SocialLinkEnum(str, Enum):
    LinkedIn = "linkedin"
    Github = "github"
    Twitter = "twitter"
    Matrix_im = "matrix_im"
    Website = "website"
    Resume = "resume"
    Facebook = "facebook"


class SocialLinks(BaseModel):

    social_links: List[SocialLink]

    class Config:
        schema_extra = {
            "example": {
                "social_links": [
                    {
                        "platform": "linkedin",
                        "link": "https://linkedin.com/in/my_user",
                    },
                    {"platform": "github", "link": "https://gibhub.com/my_user"},
                    {"platform": "twitter", "link": "https://twitter.com/my_user"},
                    {"platform": "website", "link": "https://myawesmomewebsite.com"},
                    {"platform": "resume", "link": "https://myonlineresume.com"},
                ]
            }
        }


class Skill(BaseModel):
    skill: str
    level: int

    class Config:
        schema_extra = {"exampe": {"skill": "Git", "level": 75}}


class Skills(BaseModel):
    skills: List[Skill]

    class Config:
        schema_extra = {
            "example": {
                "skills": [
                    {"skill": "Git", "level": 75},
                    {"skill": "Python", "level": 42},
                ]
            }
        }


class FullResume(BaseModel):
    basic_info: BasicInfo
    experience: JobHistory
    education: EducationHistory
    side_projects: SideProjects
    technical_interests: TechnicalInterests
    personal_interests: PersonalInterests
    social_links: SocialLinks
    preferences: Preferences


class User(BaseModel):
    username: str
    disabled: Optional[bool] = None

    class Config:
        schema_extra = {"example": {"username": "leeroy", "disabled": True}}


class Users(BaseModel):
    users: List[User]

    class Config:
        schema_extra = {
            "example": {
                "users": [
                    {"username": "leeroy", "disabled": True},
                    {"username": "jenkins", "disabled": False},
                ]
            }
        }


class Token(BaseModel):
    access_token: str
    token_type: str

    class Config:
        schema_extra = {
            "example": {
                "access_token": "long_bearer_token_here",
                "token_type": "bearer",
            }
        }
