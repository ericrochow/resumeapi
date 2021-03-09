#!/usr/bin/env python3

from contextvars import ContextVar
import peewee


DATABASE_NAME = "../resume.db"
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


class User(peewee.Model):
    email = peewee.CharField(unique=True, index=True)
    pw_hash = peewee.CharField()
    is_active = peewee.BooleanField(default=True)

    class Meta:
        database = db


class BasicInfo(peewee.Model):
    fact = peewee.CharField(unique=True)
    value = peewee.CharField()

    class Meta:
        database = db


class Education(peewee.Model):
    institution = peewee.CharField()
    degree = peewee.CharField()
    graduation_date = peewee.IntegerField()
    gpa = peewee.FloatField()

    class Meta:
        database = db


class Job(peewee.Model):
    employer = peewee.CharField()
    employer_summary = peewee.CharField()
    job_title = peewee.CharField()
    job_summary = peewee.CharField()

    class Meta:
        database = db


class JobHighlight(peewee.Model):
    highlight = peewee.ForeignKeyField(Job, backref="highlights")

    class Meta:
        database = db


class JobDetail(peewee.Model):
    detail = peewee.ForeignKeyField(Job, backref="details")

    class Meta:
        database = db


class Certification(peewee.Model):
    cert = peewee.CharField()
    full_name = peewee.CharField()
    time = peewee.CharField()
    valid = peewee.BooleanField()
    progress = peewee.IntegerField()

    class Meta:
        database = db


class Competency(peewee.Model):
    competency = peewee.CharField()

    class Meta:
        database = db


class PersonalInterest(peewee.Model):
    interest = peewee.CharField()

    class Meta:
        database = db


class TechnicalInterest(peewee.Model):
    interest = peewee.CharField()

    class Meta:
        database = db


class Preference(peewee.Model):
    preference = peewee.CharField()
    value = peewee.CharField()

    class Meta:
        database = db


class SideProject(peewee.Model):
    title = peewee.CharField()
    tagline = peewee.CharField()
    link = peewee.CharField()

    class Meta:
        database = db


class SocialLink(peewee.Model):
    platform = peewee.CharField()
    link = peewee.CharField()

    class Meta:
        database = db


class Skill(peewee.Model):
    skill = peewee.CharField()
    level = peewee.IntegerField()

    class Meta:
        database = db
