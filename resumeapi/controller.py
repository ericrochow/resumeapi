#!/usr/bin/env python3

import bcrypt
from peewee import Model
import time
from typing import Dict

import jwt
from decouple import config

from .models import User


class Auth:
    def __init__(self) -> None:
        pass

    def create_user(self, email: str, password: str, is_active: bool = True) -> Model:
        """
        Creates a new user in the database.

        Args:
            email:
            password:
            is_active:
        Returns:
            None
        """
        user = User.create(
            email=email.lower(),
            pw_hash=bcrypt.hashpw(password.encode()),
            is_active=is_active,
        )
        return user

    def login(self, email: str, password: str) -> bool:
        """"""
        user = User.get(User.email == email.lower())
        if user.is_active:
            return bcrypt.checkpw(password.encode(), user.pw_hash)

    def deactivate_user(self, email: str) -> None:
        """"""
        user = User.get(User.email == email.lower())
        user.is_active = False


class TokenMgmt:
    JWT_SECRET = config("SECRET")
    JWT_ALGORITHM = config("ALGORITHM")

    def __init__(self) -> None:
        pass

    def token_response(self, token: str):
        return {"access_token": token}

    def sign_jwt(self, user_id: str) -> Dict[str, str]:
        payload = {"user_id": user_id, "expires": time.time() + 600}
        token = jwt.encode(payload, self.JWT_SECRET, algorithm=self.JWT_ALGORITHM)

        return self.token_response(token)

    def decode_jwt(self, token: str) -> dict:
        try:
            decoded_token = jwt.decode(
                token, self.JWT_SECRET, algorithms=[self.JWT_ALGORITHM]
            )
            return decoded_token if decoded_token["expires"] >= time.time() else None
        except Exception:
            return {}
