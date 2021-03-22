#!/usr/bin/env python3

from datetime import timedelta
import os
import logging
from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import uvicorn

from controller import AuthController, ResumeController

import schema

load_dotenv()
app = FastAPI()
resume = ResumeController()
auth_control = AuthController()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
logger = logging.getLogger(__name__)


async def get_current_user(token: str = Depends(oauth2_scheme)):
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
    current_user: schema.User = Depends(get_current_user),
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post(
    "/token",
    summary="Create an API token",
    description="Logs into the API to generate a token",
    response_description="Token info",
    response_model=schema.Token,
    tags=["authentication"],
)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.debug("Attempting to log in as user %s", form_data.username)
    # valid_user = auth_control.login(form_data.username, form_data.password)
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


@app.get(
    "/users",
    summary="List all users",
    description="Lists all users and whether the user is active",
    response_description="All users",
    response_model=schema.Users,
    tags=["users"],
)
async def get_all_users(current_user: schema.User = Depends(get_current_active_user)):
    return resume.get_all_users()


@app.get(
    "/users/me",
    summary="Current user info",
    description="Returns info about the currently-authenticated user",
    response_description="User info",
    response_model=schema.User,
    tags=["users"],
)
async def read_users_me(current_user: schema.User = Depends(get_current_active_user)):
    return {"username": current_user.username, "disabled": current_user.disabled}


@app.get(
    "/basic_info",
    summary="Basic info about me",
    description="Gathers basic details about me, such as contact info, pronouns, etc",
    response_description="About Me",
    response_model=schema.BasicInfo,
    tags=["basic_info"],
)
async def get_basic_info() -> Dict[str, List[Dict[str, str]]]:
    return resume.get_basic_info()


@app.get(
    "/basic_info/{fact}",
    summary="Single basic info fact",
    description="Finds a single basic info fact about me based on the specified path",
    response_description="Requested basic info fact",
    tags=["basic_info"],
)
async def get_basic_info_fact(fact: str) -> Dict[str, str]:
    try:
        return resume.get_basic_info_item(fact)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": f"No basic info item {fact}"}
        )


@app.put(
    "/basic_info",
    summary="Creates or updates an existing fact",
    # description="",
    # response_description="",
    tags=["basic_info"],
)
async def add_or_update_fact(
    basic_fact: schema.BasicInfoItem = Body(...),
    current_user: schema.User = Depends(get_current_active_user),
):
    return resume.upsert_basic_info_item(basic_fact)


@app.delete(
    "/basic_info/{fact}",
    summary="Deletes an existing fact",
    tags=["basic_info"],
    status_code=204,
)
async def delete_fact(
    fact: str, current_user: schema.User = Depends(get_current_active_user)
):
    try:
        resume.delete_basic_info_item(fact)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": f"No such fact '{fact}'"}
        )


@app.get(
    "/education",
    summary="Education history",
    description="Finds my full education history",
    response_description="Education history",
    response_model=schema.EducationHistory,
    tags=["education"],
)
async def get_education() -> Dict[str, List[Dict[str, str]]]:
    return {"history": resume.get_all_education_history()}


@app.get(
    "/education/{index}",
    summary="Single education history item",
    description="Finds a single education history item specified in the path",
    response_description="Education history item",
    response_model=schema.Education,
    responses={404: {"model": schema.Education}},
    tags=["education"],
)
async def get_education_item(index: int) -> Dict[str, str]:
    try:
        return resume.get_education_item(index)
    except IndexError:
        return JSONResponse(
            status_code=404, content={"message": f"No education item {index}"}
        )


@app.get(
    "/experience",
    summary="Full job history",
    description="Finds my full post-undergrad job history",
    response_description="Job history",
    response_model=schema.JobHistory,
    tags=["experience"],
)
async def get_experience() -> dict:
    return {"experience": resume.get_experience()}


@app.get(
    "/experience/{index}",
    summary="Job history item",
    description="Finds a single job history item specified in the path",
    response_description="Job history item",
    response_model=schema.Job,
    responses={404: {"model": schema.Job}},
    tags=["experience"],
)
async def get_experience_item(index: int) -> dict:
    try:
        return resume.get_experience_item(index)
    except IndexError:
        return JSONResponse(
            status_code=404, content={"message": f"No experience item {index}"}
        )


@app.get(
    "/certifications",
    summary="Certification list",
    description=(
        "Finds my full list of current, previous, and in-progress certifications"
    ),
    response_description="Certifications",
    response_model=schema.CertificationHistory,
    tags=["certifications"],
)
async def get_certification_history(
    valid_only: Optional[bool] = False,
) -> Dict[str, List[Dict[str, str]]]:
    certs = resume.get_certifications(valid_only=valid_only)
    return {"certification_history": certs}


@app.get(
    "/certifications/{certification}",
    summary="Single certification",
    description=(
        "Finds information about a single certification specified in the path (case"
        " sensitive)"
    ),
    response_description="Certification",
    response_model=schema.Certification,
    responses={404: {"model": schema.Certification}},
    tags=["certifications"],
)
async def get_certification_item(certification: str) -> dict:
    try:
        return resume.get_certification_by_name(certification)
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"message": f"No certification item {certification}"},
        )


@app.get(
    "/side_projects",
    summary="Side projects",
    description="Finds a list of my highlighted side projects",
    response_description="Side projects",
    response_model=schema.SideProjects,
    tags=["side_projects"],
)
async def get_side_projects() -> dict:
    return {"projects": resume.get_side_projects()}


@app.get(
    "/side_projects/{project}",
    summary="Single side project",
    description="Finds a single side side project specified in the path",
    response_description="Side project",
    tags=["side_projects"],
)
async def get_side_project(project: str) -> Dict[str, str]:
    try:
        return resume.get_side_project(project)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": f"No side project {project}"}
        )


@app.get(
    "/interests",
    summary="",
    description="",
    response_description="",
    response_model=schema.Interests,
    tags=["interests"],
)
async def get_all_interests() -> dict:
    return resume.get_all_interests()


@app.get(
    # "/technical_interests",
    "/interests/technical",
    summary="Technical interests",
    description="Finds a list of career-related topics of interest to me",
    response_description="Technical interests",
    response_model=schema.TechnicalInterests,
    tags=["interests"],
)
async def get_technical_interests() -> dict:
    # return {"technical_interests": resume.get_technical_interests()}
    return resume.get_technical_interests()


@app.get(
    # "/personal_interests",
    "/interests/personal",
    summary="Personal interests",
    description="Finds a list of non-career-related topics of interest to me",
    response_description="Personal interests",
    response_model=schema.PersonalInterests,
    tags=["interests"],
)
async def get_personal_interests() -> dict:
    # return {"personal_interests": resume.get_personal_interests()}
    return resume.get_personal_interests()


@app.get(
    "/social_links",
    summary="Social links",
    description="Finds a list of links to me on the web",
    response_description="Social links",
    response_model=schema.SocialLinks,
    tags=["social"],
)
async def get_social_links() -> Dict[str, str]:
    return resume.get_social_links()


@app.get(
    "/social_links/{platform}",
    summary="Social link",
    description="Finds the social link specified in the path",
    response_description="Social link",
    tags=["social"],
)
async def get_social_link_by_key(platform=schema.SocialLinkEnum) -> Dict[str, str]:
    try:
        return resume.get_social_link(platform)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": f"No link stored for {platform}"}
        )


@app.get(
    "/skills",
    summary="Skills",
    description="Finds a (non-comprehensive) list of skills and info about them",
    response_description="Skills",
    response_model=schema.Skills,
    tags=["skills"],
)
async def get_skills() -> Dict[str, List[str]]:
    return resume.get_skills()


@app.get(
    "/skills/{skill}",
    summary="Skill",
    description="Finds the skill specified in the path",
    response_description="Skill",
    response_model=schema.Skill,
    tags=["skills"],
)
async def get_skill(skill: str) -> dict:
    try:
        return resume.get_skill(skill)
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"message": f"The requested skill {skill} does not exist (yet!)"},
        )


@app.get(
    "/competencies",
    summary="Competencies",
    description="Finds a list of general technical and non-technical skills",
    response_description="Competencies",
    response_model=schema.Competencies,
    tags=["skills"],
)
async def get_competencies() -> Dict[str, List[str]]:
    return resume.get_competencies()


# @app.get(
# "/",
# summary="",
# description="",
# response_description="",
# response_model=schema.FullResume,
# )
# async def get_full_resume() -> dict:
# """"""
# from pprint import pprint

# pprint(data.FULL_RESUME)
# return data.FULL_RESUME


@app.get("/pdf", summary="", description="", response_description="", tags=["media"])
async def get_resume_pdf() -> FileResponse:
    pdf = "ericrochowresume.pdf"
    try:
        return FileResponse(pdf)
    except RuntimeError:
        return JSONResponse(
            status_code=404, content={"message": "No file at this location"}
        )


@app.get("/html", summary="", description="", response_description="", tags=["media"])
async def get_resume_html() -> RedirectResponse:
    return RedirectResponse("https://resume.ericroc.how")


if __name__ == "__main__":
    uvicorn.run("main:app", log_level="info", reload=True)
