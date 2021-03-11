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


class Education(BaseModel):
    institution: str
    degree: str
    graduation_date: int
    gpa: float

    class Config:
        schema_extra = {
            "example": {
                "institution": "University of Oxford",
                "degree": "Bachelor of Fine Arts in Comma Usage",
                "graduation_date": 2001,
                "gpa": 4.0,
            }
        }


class EducationHistory(BaseModel):
    history: List[Education]


class Job(BaseModel):
    employer: str
    employer_summary: str
    job_title: str
    job_summary: str
    details: Optional[List[str]]
    highlights: Optional[List[str]]

    class Config:
        schema_extra = {
            "example": {
                "employer": "Acme, LLC",
                "employer_summary": "Acme, LLC makes or sells something I think",
                "job_title": "Chief Scotch Officer",
                "job_summary": "Report to my uncle the CEO and attend meetings",
                "details": ["Various duties as assigned"],
                "highlights": [
                    "I once made my chair swivel around 64 times without getting sick"
                ],
            }
        }


class JobHistory(BaseModel):
    experience: List[Job]


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


class Competencies(BaseModel):
    competencies: List[str]


class PersonalInterests(BaseModel):
    personal_interests: List[str]


class TechnicalInterests(BaseModel):
    technical_interests: List[str]


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


class SocialLinks(BaseModel):
    linkedin: Optional[HttpUrl]
    github: Optional[HttpUrl]
    twitter: Optional[HttpUrl]
    matrix_im: Optional[str]
    website: Optional[HttpUrl]
    resume: Optional[HttpUrl]

    class Config:
        schema_extra = {
            "example": {
                "linkedin": "https://linkedin.com/in/my_user",
                "github": "https://gibhub.com/my_user",
                "twitter": "https://twitter.com/my_user",
                # "matrix_im: "@my_user:matrix.homeserver.com",
                "website": "https://myawesmomewebsite.com",
                "resume": "https://myonlineresume.com",
            }
        }


class SocialLinkEnum(str, Enum):
    LinkedIn = "linkedin"
    Github = "github"
    Twitter = "twitter"
    Matrix_im = "matrix_im"
    Website = "website"
    Resume = "resume"


class FullResume(BaseModel):
    basic_info: BasicInfo
    experience: JobHistory
    education: EducationHistory
    side_projects: SideProjects
    technical_interests: TechnicalInterests
    personal_interests: PersonalInterests
    social_links: SocialLinks
    preferences: Preferences
