"""
In this module: All exceptions that extend ApiException.
"""
import dataclasses
from typing import Dict, Any
from pydantic.dataclasses import dataclass
from dataclasses import asdict, field
from starlette import status
from pydantic import Field


@dataclass
class ApiException(Exception):
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    id: str = "API_EXCEPTION"
    message: str | None = None
    details: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class NotImplementedException(ApiException):
    status_code: int = status.HTTP_501_NOT_IMPLEMENTED
    id: str = "NOT_IMPLEMENTED"
    message: str = "Function implementation does not exist."


@dataclass
class BadRequestException(ApiException):
    status_code: int = status.HTTP_400_BAD_REQUEST
    id: str = "BAD_REQUEST"
    message: str = "Malformed request."


@dataclass
class UnauthorizedException(ApiException):
    status_code: int = status.HTTP_401_UNAUTHORIZED
    id: str = "UNAUTHORIZED"
    message: str = "Unauthorized access."
    headers: Dict[str, Any] = field(
        default_factory=lambda: ({"WWW-Authenticate": "Bearer"})
    )


@dataclass
class ForbiddenException(ApiException):
    status_code: int = status.HTTP_403_FORBIDDEN
    id: str = "FORBIDDEN"
    message: str = "Access to this resource is forbidden."


@dataclass
class NotFoundException(ApiException):
    status_code: int = status.HTTP_404_NOT_FOUND
    id: str = "NOT_FOUND"
    message: str = "Resource not found."


exception_code_dict = {
    status.HTTP_400_BAD_REQUEST: BadRequestException,
    status.HTTP_401_UNAUTHORIZED: UnauthorizedException,
    status.HTTP_403_FORBIDDEN: ForbiddenException,
    status.HTTP_404_NOT_FOUND: NotFoundException,
}
