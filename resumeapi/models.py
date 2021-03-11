#!/usr/bin/env python3

from contextvars import ContextVar
import peewee


DATABASE_NAME = "resume.db"
db_state_default = {"closed": None, "conn": None, "ctx": None, "transactions": None}
db_state = ContextVar("db_state", default=db_state_default.copy())


class PeeweeConnectionState(peewee._ConnectionState):
    def __init__(self, **kwargs):
        super().__setattr__("_state", db_state)
        super().__init__(**kwargs)

    def __setattr__(self, name, value):
        self._state.get()[name] = value

    def __getattr__(self, name):
        return self._state.get()[name]


db = peewee.SqliteDatabase(DATABASE_NAME, check_same_thread=False)

db._state = PeeweeConnectionState()


class RerferenceModel(peewee.Model):
    class Meta:
        database = db


class User(RerferenceModel):
    email = peewee.CharField(unique=True, index=True)
    pw_hash = peewee.CharField()
    is_active = peewee.BooleanField(default=True)


class BasicInfo(RerferenceModel):
    fact = peewee.CharField(unique=True)
    value = peewee.CharField()


class Education(RerferenceModel):
    institution = peewee.CharField()
    degree = peewee.CharField()
    graduation_date = peewee.IntegerField()
    gpa = peewee.FloatField()


class Job(RerferenceModel):
    employer = peewee.CharField()
    employer_summary = peewee.CharField()
    location = peewee.CharField()
    job_title = peewee.CharField()
    job_summary = peewee.CharField()
    time = peewee.CharField()


class JobHighlight(RerferenceModel):
    highlight = peewee.CharField()
    job = peewee.ForeignKeyField(Job, backref="highlights")


class JobDetail(RerferenceModel):
    detail = peewee.CharField()
    job = peewee.ForeignKeyField(Job, backref="details")


class Certification(RerferenceModel):
    cert = peewee.CharField()
    full_name = peewee.CharField()
    time = peewee.CharField()
    valid = peewee.BooleanField()
    progress = peewee.IntegerField()


class Competency(RerferenceModel):
    competency = peewee.CharField()


class PersonalInterest(RerferenceModel):
    interest = peewee.CharField()


class TechnicalInterest(RerferenceModel):
    interest = peewee.CharField()


class Preference(RerferenceModel):
    preference = peewee.CharField()
    value = peewee.CharField()


class SideProject(RerferenceModel):
    title = peewee.CharField()
    tagline = peewee.CharField()
    link = peewee.CharField()


class SocialLink(RerferenceModel):
    platform = peewee.CharField()
    link = peewee.CharField()


class Skill(RerferenceModel):
    skill = peewee.CharField()
    level = peewee.IntegerField()
