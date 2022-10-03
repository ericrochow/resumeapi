#!/usr/bin/env python3

import os

from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError
import uvicorn

from resumeapi.controller import AuthController

if __name__ == "__main__":
    load_dotenv()
    try:
        username = os.getenv("EMAIL")
        password = os.getenv("PLAINPASS")
        if username and password:
            auth_controller = AuthController()
            auth_controller.create_user(username, password)
        del username, password
    except IntegrityError:
        print("Admin user already exists")
    host = os.getenv("API_HOST", default="127.0.0.1")
    port = os.getenv("API_PORT", default=8000)
    log_level = os.getenv("API_LOG_LEVEL", default="error")
    reload_on_change = (
        os.getenv("API_RELOAD_ON_CHANGE", default="False").title() == "True"
    )
    uvicorn.run(
        "main:app",
        host=host,
        port=int(port),
        log_level=log_level,
        reload=reload_on_change,
    )
