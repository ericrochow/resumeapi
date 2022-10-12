#!/usr/bin/env python3
"""Provides API methods served by FastAPI."""
# pylint: disable=too-many-lines

from datetime import timedelta
import os
import logging
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt  # noqa
import uvicorn

from resumeapi import __version__
from resumeapi.controller import AuthController, ResumeController
from resumeapi import models

load_dotenv()
app = FastAPI(title="Resume API", version=__version__.__version__)
resume = ResumeController()
auth_control = AuthController()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
logger = logging.getLogger(__name__)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validate a JWT token and identifies the currently-authenticated user.

    :param  token: A string containing a full JWT token.
    :type token: str
    :return: A string containing the username authenticated user.
    :rtype: str
    :raises HttpException: Could not validate credentials.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")]
        )
        username: str = payload.get("sub")
        if not username:
            raise credentials_exception
    except JWTError as exc:
        raise credentials_exception from exc
    user = auth_control.get_user(username)
    if not user:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: models.User = Depends(get_current_user),
):
    """
    Determine whether the currently-authenticated user is disabled or active.

    :param current_user: The user to check for disabled status
    :type current_user: models.User
    :return: The same object passed in
    :rtype: models.User
    :raises HttpException: The currently-active user is disabled.
    """
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


@app.post(
    "/token",
    summary="Create an API token",
    description="Log into the API to generate a token",
    response_description="Token info",
    response_model=models.Token,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": models.Token}},
    status_code=status.HTTP_201_CREATED,
    tags=["Authentication"],
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> models.Token:
    """
    Authenticate a user with Basic Auth and passes back a Bearer token.

    :param form_data: An OAuth2PasswordRequest object containing Basic Auth credentials
    :type form_data: OAuth2PasswordRequestForm
    :return: The access token and token_type of "bearer".
    :rtype: dict
    :raises HttpException: Incorrect username or password.
    """
    logger.debug("Attempting to log in as user %s", form_data.username)
    valid_user = auth_control.authenticate_user(form_data.username, form_data.password)
    if not valid_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    max_token_expiration = int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES", default="5"))
    access_token_expires = timedelta(minutes=max_token_expiration)
    access_token = auth_control.create_access_token(
        data={"sub": valid_user.username}, expires_delta=access_token_expires
    )
    response = models.Token(  # nosec: B106 - "bearer" is the type not the value
        access_token=access_token, token_type="bearer"
    )
    return response


# GET methods for read-only operations
@app.get(
    "/users",
    summary="List all users",
    response_description="All users",
    response_model=models.Users,
    tags=["Users"],
)
async def get_all_users(
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """List all users and wheter the user is active."""
    return resume.get_all_users()


@app.get(
    "/users/me",
    summary="Current user info",
    response_description="User info",
    response_model=models.User,
    tags=["Users"],
)
async def read_users_me(
    current_user: models.User = Depends(get_current_active_user),
):
    """Return info about the currently-authenticated user."""
    return {"username": current_user.username, "disabled": current_user.disabled}


@app.get(
    "/",
    summary="Full resume in JSON format",
    response_description="Full resume in JSON format",
    response_model=models.FullResume,
    tags=["Full Resume"],
)
async def get_full_resume() -> models.FullResume:
    """Request a JSON representation of my full resume."""
    return resume.get_full_resume()


@app.get(
    "/pdf",
    summary="Request PDF of my full resume",
    status_code=status.HTTP_200_OK,
    tags=["Full Resume"],
)
async def get_resume_pdf() -> FileResponse:
    """Request PDF of my full resume."""
    pdf = "ericrochowresume.pdf"
    try:
        return FileResponse(pdf)
    except RuntimeError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No file at this location",
        )


@app.get(
    "/html",
    summary="Request HTML rendering of my resume",
    response_description="HTML rendering of resume",
    responses={status.HTTP_404_NOT_FOUND: {"models": RedirectResponse}},
    status_code=status.HTTP_301_MOVED_PERMANENTLY,
    tags=["Full Resume"],
)
async def get_resume_html() -> RedirectResponse:
    """Request HTML rendering of my resume."""
    return RedirectResponse("https://resume.ericroc.how")


@app.get(
    "/basic_info",
    summary="Request basic info about me",
    response_description="About Me",
    response_model=models.BasicInfos,
    status_code=status.HTTP_200_OK,
    tags=["Basic Info"],
)
async def get_basic_info() -> models.BasicInfos:
    """Gather basic details about me, such as contact info, pronouns, etc."""
    return resume.get_basic_info()


@app.get(
    "/basic_info/{fact}",
    summary="Request a single basic info fact",
    response_description="Basic info fact",
    response_model=models.BasicInfo,
    responses={status.HTTP_404_NOT_FOUND: {"models": models.BasicInfo}},
    status_code=status.HTTP_200_OK,
    tags=["Basic Info"],
)
async def get_basic_info_fact(fact: str) -> models.BasicInfo:
    """Find a single basic fact about me based on the specified fact key."""
    try:
        return resume.get_basic_info_item(fact)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No basic info item {fact}",
        )


@app.get(
    "/education",
    summary="Request my full education history",
    response_description="Education history",
    response_model=List[models.Education],
    status_code=status.HTTP_200_OK,
    tags=["Education"],
)
async def get_education() -> List[models.Education]:
    """Find my full education history."""
    return resume.get_all_education_history()


@app.get(
    "/education/{index}",
    summary="Request a single education history item",
    response_description="Education history item",
    response_model=models.Education,
    responses={status.HTTP_404_NOT_FOUND: {"model": models.Education}},
    status_code=status.HTTP_200_OK,
    tags=["Education"],
)
async def get_education_item(index: int) -> models.Education:
    """
    Request a single education history item based on its ID.

    - **index**: ID of the education history item
    """
    try:
        return resume.get_education_item(index)
    except IndexError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No education item {index}",
        )


@app.get(
    "/experience",
    summary="Request full job history",
    response_description="Job history",
    response_model=List[models.JobResponse],
    status_code=status.HTTP_200_OK,
    tags=["Experience"],
)
async def get_experience() -> List[models.JobResponse]:
    """Request my full post-graduate job history."""
    return resume.get_experience()


@app.get(
    "/experience/{index}",
    summary="Job history item",
    response_description="Job history item",
    response_model=models.JobResponse,
    responses={status.HTTP_404_NOT_FOUND: {"model": models.JobResponse}},
    status_code=status.HTTP_200_OK,
    tags=["Experience"],
)
async def get_experience_item(index: int) -> models.JobResponse:
    """
    Find a single job history items specified by ID.

    - **index**: The ID of the job whose info to return
    """
    try:
        results = resume.get_experience_item(index)
        return results
        # return resume.get_experience_item(index)
    except IndexError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No experience item {index}",
        )


@app.get(
    "/certifications",
    summary="Certification list",
    response_description="Certifications",
    response_model=List[models.Certification],
    status_code=status.HTTP_200_OK,
    tags=["Certifications"],
)
async def get_certification_history(
    valid_only: Optional[bool] = False,
) -> List[models.Certification]:
    """
    Find my full list of current, previous, and in-progress certifications.

    - **valid_only**: Only include current certifications excluding expired ones
        (optional, defaults to False)
    """
    certs = resume.get_certifications(valid_only=valid_only)
    return certs


@app.get(
    "/certifications/{certification}",
    summary="Single certification",
    response_description="Certification",
    response_model=models.Certification,
    responses={status.HTTP_404_NOT_FOUND: {"model": models.Certification}},
    status_code=status.HTTP_200_OK,
    tags=["Certifications"],
)
async def get_certification_item(
    certification: str,
) -> models.Certification:
    """
    Find information about a single certification specified in the path.

    - **certification**: Case-sensitive certification name
    """
    try:
        return resume.get_certification_by_name(certification)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No certification item {certification}",
        )


@app.get(
    "/side_projects",
    summary="Side projects",
    response_description="Side projects",
    response_model=List[models.SideProject],
    status_code=status.HTTP_200_OK,
    tags=["Side Projects"],
)
async def get_side_projects() -> List[models.SideProject]:
    """Find a list of my highlighted side projects."""
    return resume.get_side_projects()


@app.get(
    "/side_projects/{project}",
    summary="Single side project",
    response_description="Side project",
    responses={status.HTTP_404_NOT_FOUND: {"models": models.SideProject}},
    status_code=status.HTTP_200_OK,
    tags=["Side Projects"],
)
async def get_side_project(project: str) -> models.SideProject:
    """
    Find a single side project specified by name.

    - **project**: The name of the project whose info to return.
    """
    try:
        return resume.get_side_project(project)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No side project {project}",
        )


@app.get(
    "/interests",
    summary="Interests",
    response_description="Interests",
    response_model=models.InterestsResponse,
    status_code=status.HTTP_200_OK,
    tags=["Interests"],
)
async def get_all_interests() -> models.InterestsResponse:
    """Find all personal and technical/professional interests."""
    return resume.get_all_interests()


@app.get(
    "/interests/{category}",
    summary="Interests for the requested category",
    response_description="Interests",
    response_model=List[models.Interest],
    response_model_exclude_none=True,
    status_code=status.HTTP_200_OK,
    tags=["Interests"],
)
async def get_interests_by_category(
    category: models.InterestTypes,
) -> List[models.Interest]:
    """
    Find all interests for the requested category.

    - **category**: Either personal or professional
    """
    return resume.get_interests_by_category(category)


@app.get(
    "/social_links",
    summary="Social links",
    response_description="Social links",
    response_model=List[models.SocialLink],
    status_code=status.HTTP_200_OK,
    tags=["Social"],
)
async def get_social_links() -> List[models.SocialLink]:
    """Find a list of links to me on the web."""
    return resume.get_social_links()


@app.get(
    "/social_links/{platform}",
    summary="Social link",
    response_description="Social link",
    responses={status.HTTP_404_NOT_FOUND: {"models": models.SocialLink}},
    status_code=status.HTTP_200_OK,
    tags=["Social"],
)
async def get_social_link_by_key(
    platform=models.SocialLinkEnum,
) -> models.SocialLink:
    """
    Find the social link specified in the path.

    - **platform**: Name of the social media platform whose link to return
    """
    try:
        return resume.get_social_link(platform)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No link stored for {platform}",
        )


@app.get(
    "/skills",
    summary="Skills",
    response_description="Skills",
    response_model=List[models.Skill],
    status_code=status.HTTP_200_OK,
    tags=["Skills"],
)
async def get_skills() -> List[models.Skill]:
    """Find a (non-comprehensive) list of skills and info about them."""
    return resume.get_skills()


@app.get(
    "/skills/{skill}",
    summary="Skill",
    response_description="Skill",
    response_model=models.Skill,
    responses={status.HTTP_404_NOT_FOUND: {"model": models.Skill}},
    status_code=status.HTTP_200_OK,
    tags=["Skills"],
)
async def get_skill(skill: str) -> models.Skill:
    """
    Find the skill specified in the path.

    - **skill**: Name of the skill to look up
    """
    try:
        return resume.get_skill(skill)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"The requested skill {skill} does not exist (yet!)",
        )


@app.get(
    "/competencies",
    summary="Competencies",
    description="",
    response_description="Competencies",
    response_model=List[models.Competency],
    status_code=status.HTTP_200_OK,
    tags=["Skills"],
)
async def get_competencies() -> List[models.Competency]:
    """Find a list of general technical and non-technical skills."""
    return resume.get_competencies()


# PUT methods for create and update operations
@app.put(
    "/basic_info",
    summary="Create or update an existing fact",
    response_description="The body of the new or updated fact",
    status_code=status.HTTP_201_CREATED,
    tags=["Basic Info"],
)
async def add_or_update_fact(
    basic_fact: models.BasicInfo = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.BasicInfo:
    """
    Create or update an existing fact.

    - **fact**: The name of the fact
    - **value**: The value of the fact
    """
    return resume.upsert_basic_info_item(basic_fact)


@app.put(
    "/education",
    summary="Create or update an education item",
    description="",
    response_description="ID of the new or updated education item",
    status_code=status.HTTP_201_CREATED,
    tags=["Education"],
)
async def add_or_update_education(
    education_item: models.Education = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Education:
    """
    Create or update an education item.

    - **id**: The internal ID of the education record (only used to update)
    - **institution**: The school issuing the degree
    - **degree**: The type or name of degree issued on completion of instruction
    - **graduation_date**: The year graduated from the institution
    - **gpa**: The grade point average on completion of the degree
    """
    return resume.upsert_education_item(education_item)


@app.put(
    "/experience",
    summary="Create or update an experience item",
    response_description="ID of the new or updated experience item",
    status_code=status.HTTP_201_CREATED,
    tags=["Experience"],
)
async def add_or_update_experience(
    experience_item: models.Job = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Job:
    """
    Create or update an experience item.

    - **id**: The internal ID of the job (only used to update existing)
    - **employer**: The name of the employer
    - **employer_summary**: A brief description of the employer (industry, etc.)
    - **location**: The primary work location
    - **job_title**: The job title held
    - **job_summary**: A brief description of the job
    """
    return resume.upsert_experience_item(experience_item)


@app.put(
    "/experience/detail",
    summary="Create or update a job detail",
    response_description="New or udpated job detail",
    response_model=models.JobDetail,
    status_code=status.HTTP_201_CREATED,
    tags=["Experience"],
)
async def add_or_update_experience_detail(
    experience_detail_item: models.JobDetail = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.JobDetail:
    """
    Create or update a job detail.

    - **id**: The internal ID of the job detail (only used to update existing)
    - **detail**: A detail to include for the job specified by ID
    - **job_id**: The internal ID of the job associated with this detail
    """
    return resume.upsert_job_detail(experience_detail_item)


@app.put(
    "/experience/highlight",
    summary="Create or update a job highlight",
    response_description="New or updated job highlight",
    response_model=models.JobHighlight,
    status_code=status.HTTP_201_CREATED,
    tags=["Experience"],
)
async def add_or_update_experience_highlight(
    experience_highlight_item: models.JobHighlight = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.JobHighlight:
    """
    Create or update a job highlight.

    - **id**: The internal ID of the job highlight (only used to update existing)
    - **highlight**: A highlight to include for the job specified by ID
    - **job_id**: The internal ID of the job associated with this highlight
    """
    return resume.upsert_job_highlight(experience_highlight_item)


@app.put(
    "/certifications",
    summary="Create or update a certification",
    response_description="ID of the new or updated certification",
    response_model=models.Certification,
    status_code=status.HTTP_201_CREATED,
    tags=["Certifications"],
)
async def add_or_update_certification(
    certification: models.Certification = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Certification:
    """
    Create or update a certification.

    - **cert**: The well-known name of the certification
    - **full_name**: The full name of the certification
    - **time**: The year range the certification has been valid
    - **valid**: Whether the certification is currently valid (unexpired)
    - **progress**: How much progress has been made toward attaining the certification
    """
    return resume.upsert_certification(certification)


@app.put(
    "/side_projects",
    summary="Create or update a side project",
    response_description="ID of the new or updated side project",
    response_model=models.SideProject,
    status_code=status.HTTP_201_CREATED,
    tags=["Side Projects"],
)
async def add_or_update_side_project(
    side_project: models.SideProject = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.SideProject:
    """
    Create or update a side project.

    - **title**: The title of the project
    - **tagline**: A one-sentance description of the project
    - **link**: A URL link to the project to get more details
    """
    return resume.upsert_side_project(side_project)


@app.put(
    "/interests/{category}",
    summary="Create or update an interest",
    response_description="ID of the new or updated interest",
    response_model=models.Interest,
    status_code=status.HTTP_201_CREATED,
    tags=["Interests"],
)
async def add_or_update_interest(
    category: models.InterestTypes,
    interest: models.Interest = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Interest:
    """
    Create or update an interest.

    - **category**: personal or professional
    - **interest**: Interest to add to the list
    """
    return resume.upsert_interest(category, interest.interest)


@app.put(
    "/social_links",
    summary="Create or update a social link",
    response_description="The new or udpated social link",
    response_model=models.SocialLink,
    status_code=status.HTTP_201_CREATED,
    tags=["Social"],
)
async def add_or_create_social_link(
    social_link: models.SocialLink,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.SocialLink:
    """
    Create or update a social link.

    - **platform**: The social platform to configure
    - **link**: A URL to the social profile associated with the platform
    """
    return resume.upsert_social_link(social_link)


@app.put(
    "/skills",
    summary="Create or update a skill",
    response_description="The new or updated skill",
    status_code=status.HTTP_201_CREATED,
    tags=["Skills"],
)
async def add_or_update_skill(
    skill: models.Skill = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Skill:
    """
    Create or update a skill.

    - **skill**: The name of the skill to configure
    - **level**: Skill level out of 100
    """
    return resume.upsert_skill(skill)


@app.put(
    "/competencies/{competency}",
    summary="Create or update a competency",
    response_description="New or updated competency",
    status_code=status.HTTP_201_CREATED,
    tags=["Skills"],
)
async def add_or_update_competency(
    # competency: models.Competencies = Body(...),
    competency: str,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Competency:
    """
    Create or update a competency.

    - **competency**: The competency to add to the list
    """
    return resume.upsert_competency(competency)


@app.put(
    "/preferences",
    summary="Create or udpate a preference,",
    response_description="New or updated preference",
    status_code=status.HTTP_201_CREATED,
    tags=["Preferences"],
)
async def add_or_update_preference(
    preference: models.Preference = Body(...),
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
) -> models.Preference:
    """
    Create or update a preference.

    - **preference**: The type of preference
    - **value**: The value of the preference
    """
    return resume.upsert_preference(preference)


# DELETE methods for delete operations
@app.delete(
    "/basic_info/{fact}",
    summary="Delete an existing fact",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Basic Info"],
)
async def delete_fact(
    fact: str,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing fact.

    - **fact**: The key of the fact to remove (e.g. name)
    """
    try:
        resume.delete_basic_info_item(fact)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No such fact '{fact}'",
        )


@app.delete(
    "/education/{index}",
    summary="Delete an existing education history item",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Education"],
)
async def delete_education_item(
    index: int,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing education history item.

    - **id**: The internal ID of the education history item to delete
    """
    try:
        resume.delete_education_item(index)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such eduction item exists",
        )


@app.delete(
    "/experience/{index}",
    summary="Delete an existing job history item",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Experience"],
)
async def delete_experience_item(
    index: int,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing job history item.

    - **index**: The internal ID of the job to delete
    """
    try:
        resume.delete_experience_item(index)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such job history item exists",
        )


@app.delete(
    "/experience/detail/{index}",
    summary="Delete a job detail",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Experience"],
)
async def delete_experience_detail_item(
    index: int,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete a job detail.

    - **index**: The internal ID of the job detail to delete
    """
    try:
        resume.delete_job_detail(index)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such job detail item exists",
        )


@app.delete(
    "/experience/highlight/{index}",
    summary="Delete a job highlight",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Experience"],
)
async def delete_experience_highlight_item(
    index: int,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete a job highlight.

    - **index**: The internal ID of the job highlight to delete
    """
    try:
        resume.delete_job_highlight(index)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such job highlight item exists",
        )


@app.delete(
    "/certifications/{certification}",
    summary="Delete an existing certification",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Certifications"],
)
async def delete_certification(
    certification: str,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing certification.

    - **certification**: The case-sensitive, well-known name of the certification
    """
    try:
        resume.delete_certification(certification)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such certification exists",
        )


@app.delete(
    "/side_projects/{project}",
    summary="Delete an existing side project",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Side Projects"],
)
async def delete_side_project(
    project: str,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing side project.

    - **project**: The name of the project to delete
    """
    try:
        resume.delete_side_project(project)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such side project exists",
        )


@app.delete(
    "/interests/{interest}",
    summary="Delete an existing interest",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Interests"],
)
async def delete_interest(
    interest: str,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing interest.

    - **interest**: The interest to remove from the list
    """
    try:
        resume.delete_interest(interest)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such interest exists",
        )


@app.delete(
    "/social_links/{platform}",
    summary="Delete an existing social link",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Social"],
)
async def delete_social_link(
    platform: str,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing social link by platform.

    - **platform**: The name of the platform whose link to delete
    """
    try:
        resume.delete_social_link(platform)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such social link exists",
        )


@app.delete(
    "/skills/{skill}",
    summary="Delete an existing skill",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Skills"],
)
async def delete_skill(
    skill: str,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing skill.

    - **skill**: The skill to delete
    """
    try:
        resume.delete_skill(skill)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such skill exists",
        )


@app.delete(
    "/competencies/{competency}",
    summary="Delete an existing competency",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Skills"],
)
async def delete_competency(
    competency: str,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing competency.

    - **competency**: The competency to delete
    """
    try:
        resume.delete_competency(competency)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such competency exists",
        )


@app.delete(
    "/preferences/{preference}",
    summary="Delete a prefeerence",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Preferences"],
)
async def delete_preference(
    preference: str,
    current_user: models.User = Depends(  # pylint: disable=unused-argument
        get_current_active_user
    ),
):
    """
    Delete an existing preference.

    - **preference**: The preference to delete.
    """
    try:
        resume.delete_preference(preference)
    except KeyError:
        raise HTTPException(  # pylint: disable=raise-missing-from
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such preference exists",
        )


if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    port = os.getenv("API_PORT", "8000")
    log_level = os.getenv("API_LOG_LEVEL", "error")
    reload_on_change = os.getenv("API_RELOAD_ON_CHANGE", default="False").title()
    uvicorn.run(
        "main:app",
        host=host,
        port=int(port),
        log_level=log_level,
        reload=(reload_on_change == "True"),
    )
