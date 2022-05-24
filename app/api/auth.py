from datetime import datetime, timedelta
import logging
import uuid
from enum import Enum
from typing import Any, Dict, List, Set

import structlog
from jose import JWTError, jwt
from app.api.exceptions import (
    ApiException,
    ForbiddenException,
    UnauthorizedException,
)
from app.config import get_settings
from app.api.api_router import CustomApiRouter
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field, parse_obj_as, ValidationError, Json


logger: structlog.stdlib.AsyncBoundLogger = structlog.get_logger(__name__)
stdlogger = logging.getLogger(__name__)


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    id: uuid.UUID
    email: str | None
    full_name: str | None

    @staticmethod
    def from_token(token: Json):
        user_id = token["sub"]
        return User(id=user_id)


settings = get_settings()
mock_users = {
    settings.FASTAPI_EMAIL: User(
        id=uuid.uuid4(), email=settings.FASTAPI_EMAIL, full_name=settings.FASTAPI_MAINT
    ),
}
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token",
    auto_error=False,
)


def authenticate_user(mock_db: Dict[str, User], username: str, password: str) -> User:
    # this is for demo purposes only, in a real app there should be a db and
    # hashing
    return mock_db[username]


def create_token(data: Dict, expires: timedelta | None = timedelta(minutes=30)):
    data = data.copy()
    expire = datetime.utcnow() + expires
    data.update({"exp": expire})
    return jwt.encode(data, secret_key, settings.SECRET_KEY, algorithm="HS256")


async def get_auth(
    token: str = Depends(oauth2_scheme),
) -> Json:
    """
    Parameters
    ----------
    token
        The Bearer token of the current request.

    Returns
    -------
    Json
        Verified and decoded token.

    Raises
    ------
    UnauthorizedException
        If the token could not be validated and verified.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])

    except Exception as e:
        raise UnauthorizedException(details={"domain": "access_control"}) from e


async def get_user(
    token: Json = Depends(get_auth),
) -> User:
    """
    Load and verify user by their JWT and fill in organization information such
    as roles held by the user.

    Parameters
    ----------
    token : Json, optional
        Decoded and verified Bearer Token of the request, by default Depends(get_auth)

    Returns
    -------
    User
        The current user.

    """
    return User.from_token(token)
