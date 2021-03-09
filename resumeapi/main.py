#!/usr/bin/env python3

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import JSONResponse

import uvicorn

# import data
import schema

load_dotenv()
app = FastAPI()


# @app.get("/", response_model=schema.FullResume)
# async def get_full_resume() -> dict:
# """"""
# from pprint import pprint

# pprint(data.FULL_RESUME)
# return data.FULL_RESUME


@app.get("/basic_info", response_model=schema.BasicInfo)
async def get_basic_info() -> dict:
    """"""
    return data.BASIC_INFO


@app.get("/education", response_model=schema.EducationHistory)
async def get_education() -> dict:
    """"""
    return {"history": data.EDUCATION}


@app.get(
    "/education/{index}",
    response_model=schema.Education,
    responses={404: {"model": schema.Education}},
)
async def get_education_item(index: int) -> dict:
    """"""
    try:
        return data.EDUCATION[index]
    except IndexError:
        return JSONResponse(
            status_code=404, content={"message": f"No education item {index}"}
        )


@app.get("/experience", response_model=schema.JobHistory)
async def get_experience() -> dict:
    """"""
    return {"experience": data.EXPERIENCE}


@app.get(
    "/experience/{index}",
    response_model=schema.Job,
    responses={404: {"model": schema.Job}},
)
async def get_experience_item(index: int) -> dict:
    """"""
    try:
        return data.EXPERIENCE[index]
    except IndexError:
        return JSONResponse(
            status_code=404, content={"message": f"No experience item {index}"}
        )


@app.get("/certifications", response_model=schema.CertificationHistory)
async def get_certification_history() -> dict:
    return {"certification_history": data.CERTIFICATION_HISTORY}


@app.get(
    "/certifications/{index}",
    response_model=schema.Certification,
    responses={404: {"model": schema.Certification}},
)
async def get_certification_item(index: int) -> dict:
    try:
        return data.CERTIFICATION_HISTORY[index]
    except IndexError:
        return JSONResponse(
            status_code=404, content={"message": f"No certification item {index}"}
        )


@app.get("/side_projects", response_model=schema.SideProjects)
async def get_side_projects() -> dict:
    """"""
    return {"projects": data.SIDE_PROJECTS}


@app.get("/professional_interests", response_model=schema.TechnicalInterests)
async def get_professional_interests() -> dict:
    """"""
    return {"technical_interests": data.TECHNICAL_INTERESTS}


@app.get("/personal_interests", response_model=schema.PersonalInterests)
async def get_personal_interests() -> dict:
    """"""
    return {"personal_interests": data.PERSONAL_INTERESTS}


@app.get("/social_links", response_model=schema.SocialLinks)
async def get_social_links() -> dict:
    """"""
    return data.SOCIAL_LINKS


@app.get("/social_links/{platform}")
async def get_social_link_by_key(platform=schema.SocialLinkEnum) -> dict:
    """"""
    try:
        return {platform.value: data.SOCIAL_LINKS[platform]}
    except KeyError:
        return JSONResponse(
            status_code=404, content={"message": f"No link stored for {platform}"}
        )


if __name__ == "__main__":
    uvicorn.run("main:app")
