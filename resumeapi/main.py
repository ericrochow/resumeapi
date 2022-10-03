#!/usr/bin/env python3

from datetime import timedelta
import os
import logging
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt  # noqa
import uvicorn

from controller import AuthController, ResumeController

import models

load_dotenv()
app = FastAPI(title="Resume API", version="0.2.0")
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
    except JWTError:
        raise credentials_exception
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
    :type current_user: models.py.bak.User
    :return: The same object passed in
    :rtype: models.py.bak.User
    :raises HttpException: The currently-active user is disabled.
    """
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post(
    "/token",
    summary="Create an API token",
    description="Log into the API to generate a token",
    response_description="Token info",
    response_model=models.Token,
    tags=["Authentication"],
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Dict[str, str]:
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
            status_code=400,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    max_token_expiration = int(os.getenv("ACCESS_TOKEN_EXPIRES_MINUTES"))
    access_token_expires = timedelta(minutes=max_token_expiration)
    access_token = auth_control.create_access_token(
        data={"sub": valid_user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


# GET methods for read-only operations
@app.get(
    "/users",
    summary="List all users",
    description="List all users and whether the user is active",
    response_description="All users",
    response_model=models.Users,
    tags=["Users"],
)
async def get_all_users(current_user: models.User = Depends(get_current_active_user)):
    return resume.get_all_users()


@app.get(
    "/users/me",
    summary="Current user info",
    description="Return info about the currently-authenticated user",
    response_description="User info",
    response_model=models.User,
    tags=["Users"],
)
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return {"username": current_user.username, "disabled": current_user.disabled}


@app.get(
    "/",
    summary="",
    description="",
    response_description="",
    response_model=models.FullResume,
    tags=["Full Resume"],
)
async def get_full_resume() -> models.FullResume:
    """"""
    return resume.get_full_resume()


@app.get(
    "/pdf", summary="", description="", response_description="", tags=["Full Resume"]
)
async def get_resume_pdf() -> FileResponse:
    pdf = "ericrochowresume.pdf"
    try:
        return FileResponse(pdf)
    except RuntimeError:
        return JSONResponse(  # noqa
            status_code=404, content={"message": "No file at this location"}
        )


@app.get(
    "/html", summary="", description="", response_description="", tags=["Full Resume"]
)
async def get_resume_html() -> RedirectResponse:
    return RedirectResponse("https://resume.ericroc.how")


@app.get(
    "/basic_info",
    summary="Basic info about me",
    description="Gather basic details about me, such as contact info, pronouns, etc",
    response_description="About Me",
    response_model=models.BasicInfos,
    tags=["Basic Info"],
)
async def get_basic_info() -> models.BasicInfos:
    return resume.get_basic_info()


@app.get(
    "/basic_info/{fact}",
    summary="Single basic info fact",
    description="Find a single basic info fact about me based on the specified path",
    response_description="Basic info fact",
    response_model=models.BasicInfo,
    tags=["Basic Info"],
)
async def get_basic_info_fact(fact: str) -> models.BasicInfo:
    try:
        return resume.get_basic_info_item(fact)
    except KeyError:
        return JSONResponse(  # noqa
            status_code=404, content={"message": f"No basic info item {fact}"}
        )


@app.get(
    "/education",
    summary="Education history",
    description="Find my full education history",
    response_description="Education history",
    response_model=List[models.Education],
    tags=["Education"],
)
async def get_education() -> List[models.Education]:
    return resume.get_all_education_history()


@app.get(
    "/education/{index}",
    summary="Single education history item",
    description="Find a single education history item specified in the path",
    response_description="Education history item",
    response_model=models.Education,
    responses={404: {"model": models.Education}},
    tags=["Education"],
)
async def get_education_item(index: int) -> models.Education:
    try:
        return resume.get_education_item(index)
    except IndexError:
        return JSONResponse(  # noqa
            status_code=404, content={"message": f"No education item {index}"}
        )


@app.get(
    "/experience",
    summary="Full job history",
    description="Find my full post-undergrad job history",
    response_description="Job history",
    response_model=List[models.Job],
    tags=["Experience"],
)
async def get_experience() -> List[models.Job]:
    return resume.get_experience()


@app.get(
    "/experience/{index}",
    summary="Job history item",
    description="Find a single job history item specified in the path",
    response_description="Job history item",
    response_model=models.Job,
    responses={404: {"model": models.Job}},
    tags=["Experience"],
)
async def get_experience_item(index: int) -> models.Job:
    try:
        return resume.get_experience_item(index)
    except IndexError:
        return JSONResponse(  # noqa
            status_code=404, content={"message": f"No experience item {index}"}
        )


@app.get(
    "/certifications",
    summary="Certification list",
    description=(
        "Find my full list of current, previous, and in-progress certifications"
    ),
    response_description="Certifications",
    response_model=List[models.Certification],
    # response_model=List[models.Certification],
    tags=["Certifications"],
)
async def get_certification_history(
    valid_only: Optional[bool] = False,
) -> List[models.Certification]:
    certs = resume.get_certifications(valid_only=valid_only)
    return certs


@app.get(
    "/certifications/{certification}",
    summary="Single certification",
    description=(
        "Find information about a single certification specified in the path (case"
        " sensitive)"
    ),
    response_description="Certification",
    response_model=models.Certification,
    responses={404: {"model": models.Certification}},
    tags=["Certifications"],
)
async def get_certification_item(certification: str) -> models.Certification:
    try:
        return resume.get_certification_by_name(certification)
    except KeyError:
        return JSONResponse(  # noqa
            status_code=404,
            content={"message": f"No certification item {certification}"},
        )


@app.get(
    "/side_projects",
    summary="Side projects",
    description="Find a list of my highlighted side projects",
    response_description="Side projects",
    response_model=List[models.SideProject],
    tags=["Side Projects"],
)
async def get_side_projects() -> List[models.SideProject]:
    return resume.get_side_projects()


@app.get(
    "/side_projects/{project}",
    summary="Single side project",
    description="Find a single side side project specified in the path",
    response_description="Side project",
    tags=["Side Projects"],
)
async def get_side_project(project: str) -> models.SideProject:
    try:
        return resume.get_side_project(project)
    except KeyError:
        return JSONResponse(  # noqa
            status_code=404, content={"message": f"No side project {project}"}
        )


@app.get(
    "/interests",
    summary="Interests",
    description="Find all personal and technical/professional interests",
    response_description="Interests",
    response_model=models.InterestsResponse,
    tags=["Interests"],
)
async def get_all_interests() -> models.InterestsResponse:
    return resume.get_all_interests()


@app.get(
    "/interests/{category}",
    summary="Interests for the requested category",
    description="Find all interests for the requested categories",
    response_description="Interests",
    response_model=List[models.Interest],
    response_model_exclude_none=True,
    tags=["Interests"],
)
async def get_interests_by_category(
    category: models.InterestTypes,
) -> List[models.Interest]:
    return resume.get_interests_by_category(category)


@app.get(
    "/social_links",
    summary="Social links",
    description="Find a list of links to me on the web",
    response_description="Social links",
    response_model=List[models.SocialLink],
    tags=["Social"],
)
async def get_social_links() -> List[models.SocialLink]:
    return resume.get_social_links()


@app.get(
    "/social_links/{platform}",
    summary="Social link",
    description="Find the social link specified in the path",
    response_description="Social link",
    tags=["Social"],
)
async def get_social_link_by_key(platform=models.SocialLinkEnum) -> models.SocialLink:
    try:
        return resume.get_social_link(platform)
    except KeyError:
        return JSONResponse(  # noqa
            status_code=404, content={"message": f"No link stored for {platform}"}
        )


@app.get(
    "/skills",
    summary="Skills",
    description="Find a (non-comprehensive) list of skills and info about them",
    response_description="Skills",
    response_model=List[models.Skill],
    tags=["Skills"],
)
async def get_skills() -> List[models.Skill]:
    return resume.get_skills()


@app.get(
    "/skills/{skill}",
    summary="Skill",
    description="Find the skill specified in the path",
    response_description="Skill",
    response_model=models.Skill,
    tags=["Skills"],
)
async def get_skill(skill: str) -> models.Skill:
    try:
        return resume.get_skill(skill)
    except KeyError:
        return JSONResponse(  # noqa
            status_code=404,
            content={"message": f"The requested skill {skill} does not exist (yet!)"},
        )


@app.get(
    "/competencies",
    summary="Competencies",
    description="Find a list of general technical and non-technical skills",
    response_description="Competencies",
    response_model=List[models.Competency],
    tags=["Skills"],
)
async def get_competencies() -> List[models.Competency]:
    return resume.get_competencies()


# PUT methods for create and update operations
@app.put(
    "/basic_info",
    summary="Create or update an existing fact",
    description="",
    response_description="The body of the new or updated fact",
    tags=["Basic Info"],
)
async def add_or_update_fact(
    basic_fact: models.BasicInfo = Body(...),
    current_user: models.User = Depends(get_current_active_user),
) -> models.BasicInfo:
    return resume.upsert_basic_info_item(basic_fact)


@app.put(
    "/education",
    summary="Create or update an education item",
    description="",
    response_description="ID of the new or updated education item",
    tags=["Education"],
)
async def add_or_update_education(
    education_item: models.Education = Body(...),
    current_user: models.User = Depends(get_current_active_user),
) -> models.Education:
    return resume.upsert_education_item(education_item)


@app.put(
    "/experience",
    summary="Create or update an experience item",
    description="",
    response_description="ID of the new or updated experience item",
    tags=["Experience"],
)
async def add_or_update_experience(
    experience_item: models.Job = Body(...),
    current_user: models.User = Depends(get_current_active_user),
) -> models.Job:
    return resume.upsert_experience_item(experience_item)


@app.put(
    "/certifications",
    summary="Create or update a certification",
    description="",
    response_description="ID of the new or updated certification",
    tags=["Certifications"],
)
async def add_or_update_certification(
    certification: models.Certification = Body(...),
    current_user: models.User = Depends(get_current_active_user),
) -> models.Certification:
    return resume.upsert_certification(certification)


@app.put(
    "/side_projects",
    summary="Create or update a side project",
    description="",
    response_description="ID of the new or updated side project",
    tags=["Side Projects"],
)
async def add_or_update_side_project(
    side_project: models.SideProject = Body(...),
    current_user: models.User = Depends(get_current_active_user),
) -> models.SideProject:
    return resume.upsert_side_project(side_project)


@app.put(
    "/interests/{category}",
    summary="Create or update an interest",
    description="",
    response_description="ID of the new or updated interest",
    tags=["Interests"],
)
async def add_or_update_interest(
    category: models.InterestTypes,
    interest: models.Interest = Body(...),
    current_user: models.User = Depends(get_current_active_user),
) -> models.Interest:
    return resume.upsert_interest(category, interest.interest)


@app.put(
    "/social_links",
    summary="Create or update a social link",
    description="",
    response_description="",
    tags=["Social"],
)
async def add_or_create_social_link(
    social_link: models.SocialLink,
    current_user: models.User = Depends(get_current_active_user),
) -> models.SocialLink:
    return resume.upsert_social_link(social_link)


@app.put(
    "/skills",
    summary="Create or update a skill",
    description="",
    response_description="ID of the new or updated skill",
    tags=["Skills"],
)
async def add_or_update_skill(
    skill: models.Skill = Body(...),
    current_user: models.User = Depends(get_current_active_user),
) -> models.Skill:
    return resume.upsert_skill(skill)


@app.put(
    "/competencies/{competency}",
    summary="Create or update a competency",
    description="",
    response_description="ID of the new or updated competency",
    tags=["Skills"],
)
async def add_or_update_competency(
    # competency: models.Competencies = Body(...),
    competency: str,
    current_user: models.User = Depends(get_current_active_user),
) -> models.Competency:
    return resume.upsert_competency(competency)


# DELETE methods for delete operations
@app.delete(
    "/basic_info/{fact}",
    summary="Delete an existing fact",
    tags=["Basic Info"],
    status_code=204,
)
async def delete_fact(
    fact: str, current_user: models.User = Depends(get_current_active_user)
):
    try:
        resume.delete_basic_info_item(fact)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": f"No such fact '{fact}'"}
        )


@app.delete(
    "/education/{index}",
    summary="Delete an existing education history item",
    tags=["Education"],
    status_code=204,
)
async def delete_education_item(
    index: int, current_user: models.User = Depends(get_current_active_user)
):
    try:
        resume.delete_education_item(index)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": "No such eduction item exists"}
        )


@app.delete(
    "/experience/{index}",
    summary="Delete an existing job history item",
    tags=["Experience"],
    status_code=204,
)
async def delete_experience_item(
    index: int, current_user: models.User = Depends(get_current_active_user)
):
    try:
        resume.delete_experience_item(index)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": "No such job history item exists"}
        )


@app.delete(
    "/certifications/{certification}",
    summary="Delete an existing certification",
    tags=["Certifications"],
    status_code=204,
)
async def delete_certification(
    certification: str, current_user: models.User = Depends(get_current_active_user)
):
    try:
        resume.delete_certification(certification)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": "No such certification exists"}
        )


@app.delete(
    "/side_projects/{project}",
    summary="Delete an existing side project",
    tags=["Side Projects"],
    status_code=204,
)
async def delete_side_project(
    project: str, current_user: models.User = Depends(get_current_active_user)
):
    try:
        resume.delete_side_project(project)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": "No such side project exists"}
        )


@app.delete(
    "/interests/{interest}",
    summary="Delete an existing interest",
    tags=["Interests"],
    status_code=204,
)
async def delete_interest(
    interest: str, current_user: models.User = Depends(get_current_active_user)
):
    try:
        resume.delete_interest(interest)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": "No such interest exists"}
        )


@app.delete(
    "/social_links/{platform}",
    summary="Delete an existing social link",
    tags=["Social"],
    status_code=204,
)
async def delete_social_link(
    platform: str, current_user: models.User = Depends(get_current_active_user)
):
    try:
        resume.delete_social_link(platform)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": "No such social link exists"}
        )


@app.delete(
    "/skills/{skill}",
    summary="Delete an existing skill",
    tags=["Skills"],
    status_code=204,
)
async def delete_skill(
    skill: str, current_user: models.User = Depends(get_current_active_user)
):
    try:
        resume.delete_skill(skill)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": "No such skill exists"}
        )


@app.delete(
    "/competencies/{competency}",
    summary="Delete an existing competency",
    tags=["Skills"],
    status_code=204,
)
async def delete_competency(
    competency: str, current_user: models.User = Depends(get_current_active_user)
):
    try:
        resume.delete_competency(competency)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": "No such competency exists"}
        )

# TODO: Add methods for preferences

if __name__ == "__main__":
    host = os.getenv("API_HOST", "127.0.0.1")
    port = os.getenv("API_PORT", "8000")
    log_level = os.getenv("API_LOG_LEVEL", "error")
    reload_on_change = os.getenv("API_RELOAD_ON_CHANGE")
    uvicorn.run(
        "main:app",
        host=host,
        port=int(port),
        log_level=log_level,
        reload=(reload_on_change.title() == "True"),
    )
