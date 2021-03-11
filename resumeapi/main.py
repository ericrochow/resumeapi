#!/usr/bin/env python3

from typing import Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse

import uvicorn

# from resumeapi import data
# import data

# from resumeapi.controller import ResumeController
from controller import ResumeController

# from resumeapi import schema
import schema

load_dotenv()
app = FastAPI()
resume = ResumeController()


# @app.get("/", response_model=schema.FullResume)
# async def get_full_resume() -> dict:
# """"""
# from pprint import pprint

# pprint(data.FULL_RESUME)
# return data.FULL_RESUME


@app.get("/basic_info", response_model=schema.BasicInfo, tags=["basic_info"])
async def get_basic_info() -> dict:
    """
    Fetches all basic info key/value pairs.

    Args:
        None
    Returns:
        A dict containing all basic info.
    """
    return resume.get_basic_info()


@app.get("/basic_info/{fact}", tags=["basic_info"])
async def get_basic_info_fact(fact: str) -> dict:
    """"""
    try:
        return resume.get_basic_info_item(fact)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": f"No basic info item {fact}"}
        )


@app.get("/education", response_model=schema.EducationHistory, tags=["education"])
async def get_education() -> dict:
    """"""
    # return {"history": data.EDUCATION}
    return {"history": resume.get_all_education_history()}


@app.get(
    "/education/{index}",
    response_model=schema.Education,
    responses={404: {"model": schema.Education}},
    tags=["education"],
)
async def get_education_item(index: int) -> dict:
    """"""
    try:
        return resume.get_education_item(index)
    except IndexError:
        return JSONResponse(
            status_code=404, content={"message": f"No education item {index}"}
        )


@app.get("/experience", response_model=schema.JobHistory, tags=["experience"])
async def get_experience() -> dict:
    """"""
    # return {"experience": data.EXPERIENCE}
    return {"experience": resume.get_experience()}


@app.get(
    "/experience/{index}",
    response_model=schema.Job,
    responses={404: {"model": schema.Job}},
    tags=["experience"],
)
async def get_experience_item(index: int) -> dict:
    """"""
    try:
        # return data.EXPERIENCE[index]
        return resume.get_experience_item(index)
    except IndexError:
        return JSONResponse(
            status_code=404, content={"message": f"No experience item {index}"}
        )


@app.get(
    "/certifications",
    response_model=schema.CertificationHistory,
    tags=["certifications"],
)
async def get_certification_history(
    valid_only: Optional[bool] = False,
) -> Dict[str, List[Dict[str, str]]]:
    certs = resume.get_certifications(valid_only=valid_only)
    return {"certification_history": certs}
    # return {"certification_history": data.CERTIFICATION_HISTORY}


@app.get(
    "/certifications/{certification}",
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


@app.get("/side_projects", response_model=schema.SideProjects, tags=["side_projects"])
async def get_side_projects() -> dict:
    """"""
    return {"projects": resume.get_side_projects()}


@app.get("/side_projects/{project}", tags=["side_projects"])
async def get_side_project(project: str) -> Dict[str, str]:
    """"""
    try:
        return resume.get_side_project(project)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": f"No side project {project}"}
        )


@app.get(
    "/professional_interests",
    response_model=schema.TechnicalInterests,
    tags=["interests"],
)
async def get_technical_interests() -> dict:
    """"""
    # return {"technical_interests": data.TECHNICAL_INTERESTS}
    return {"technical_interests": resume.get_technical_interests()}


@app.get(
    "/personal_interests", response_model=schema.PersonalInterests, tags=["interests"]
)
async def get_personal_interests() -> dict:
    """"""
    # return {"personal_interests": data.PERSONAL_INTERESTS}
    return {"personal_interests": resume.get_personal_interests()}


@app.get("/social_links", response_model=schema.SocialLinks, tags=["social"])
async def get_social_links() -> Dict[str, str]:
    """"""
    return resume.get_social_links()


@app.get("/social_links/{platform}", tags=["social"])
async def get_social_link_by_key(platform=schema.SocialLinkEnum) -> Dict[str, str]:
    """"""
    try:
        return resume.get_social_link(platform)
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": f"No link stored for {platform}"}
        )


if __name__ == "__main__":
    uvicorn.run("main:app")
