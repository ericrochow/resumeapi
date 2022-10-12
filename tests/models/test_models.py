#!/usr/bin/env python3
"""Test the models module."""

from resumeapi import models  # pylint: disable=import-error


def test_user_class_properties():
    """Test that all expected fields exist in User table."""
    props = ["id", "username", "password", "disabled"]
    assert all(prop in models.User.schema()["properties"].keys() for prop in props)


def test_users_class_properties():
    """Test the Users schema."""
    props = ["id", "username", "password", "disabled"]
    assert all(
        prop in models.Users.schema()["definitions"]["User"]["properties"].keys()
        for prop in props
    )


def test_token_class_properties():
    """Test the Token schema."""
    props = ["access_token", "token_type"]
    assert all(prop in models.Token.schema()["properties"].keys() for prop in props)


def test_basicinfos_class_properties():
    """Test that all expected fields exist in the BasicInfo table."""
    props = ["id", "fact", "value"]
    assert all(prop in models.BasicInfo.schema()["properties"].keys() for prop in props)


def test_education_class_properties():
    """Test that all expected fields exist in the Education table."""
    props = ["id", "institution", "degree", "graduation_date", "gpa"]
    assert all(prop in models.Education.schema()["properties"].keys() for prop in props)


def test_job_class_properties():
    """Test that all expected fields exist in the Job table."""
    props = [
        "id",
        "employer",
        "employer_summary",
        "location",
        "job_title",
        "job_summary",
        "time",
    ]
    assert all(prop in models.Job.schema()["properties"].keys() for prop in props)


def test_jobresponse_class_properties():
    """Test that all expected fields exist in the JobResponse schema."""
    props = [
        "id",
        "employer",
        "employer_summary",
        "job_title",
        "job_summary",
        "details",
        "highlights",
    ]
    assert all(
        prop in models.JobResponse.schema()["properties"].keys() for prop in props
    )


def test_jobhighlight_class_properties():
    """Test that all expected fields exist in the JobHighlight table."""
    props = ["id", "highlight", "job_id"]
    assert all(
        prop in models.JobHighlight.schema()["properties"].keys() for prop in props
    )


def test_jobdetail_class_properties():
    """Test that all expected fields exist in the JobDetail table."""
    props = ["id", "detail", "job_id"]
    assert all(prop in models.JobDetail.schema()["properties"].keys() for prop in props)


def test_certification_class_properties():
    """Test that all expected fields exist in the Certification table."""
    props = ["id", "cert", "full_name", "time", "valid", "progress"]
    assert all(
        prop in models.Certification.schema()["properties"].keys() for prop in props
    )


def test_competency_class_properties():
    """Test that all expected fields exist in the Competency table."""
    props = ["id", "competency"]
    assert all(
        prop in models.Competency.schema()["properties"].keys() for prop in props
    )


def test_interesttype_class_properties():
    """Test that all expected fields exist in the InterestType table."""
    props = ["id", "interest_type"]
    assert all(
        prop in models.InterestType.schema()["properties"].keys() for prop in props
    )


def test_interesttypes_enum():
    """Test that fields exist in the InterestTypes enum."""
    props = ["personal", "technical"]
    assert all(prop in dir(models.InterestTypes) for prop in props)


def test_interest_class_properties():
    """Test that all expected fields exist in the Interest table."""
    props = ["id", "interest_type_id", "interest"]
    assert all(prop in models.Interest.schema()["properties"].keys() for prop in props)


def test_interestsresponse_class_properties():
    """Test that all the expected fields exist in the InterestsResponse schema."""
    props = ["personal", "technical"]
    assert all(
        prop in models.InterestsResponse.schema()["properties"].keys() for prop in props
    )


def test_preference_class_properties():
    """Test that all the expected fields exist in the Preference table."""
    props = ["id", "preference", "value"]
    assert all(
        prop in models.Preference.schema()["properties"].keys() for prop in props
    )


def test_preferences_class_properties():
    """Test that all the expected fields exist in the Preferences schema."""
    props = [
        "OS",
        "EDITOR",
        "TERMINAL",
        "COLOR_THEME",
        "CODE_COMPLETION",
        "CODE_STYLE",
        "LANGUAGES",
        "TEST_SUITES",
    ]
    assert all(
        prop in models.Preferences.schema()["properties"].keys() for prop in props
    )
    assert all(
        prop in props for prop in models.Preferences.schema()["properties"].keys()
    )
