"""
In this module: All exceptions that extend ApiException.
"""
from dataclasses import asdict
from typing import Any, Dict

from pydantic import Field
from pydantic.dataclasses import dataclass
from starlette import status


@dataclass
class ApiException(Exception):
    """Exception base class, defines the error response model."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    id: str = "API_EXCEPTION"
    message: str | None = None
    details: Dict[str, Any] = Field(default_factory=dict)
    headers: Dict[str, Any] = Field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """return dataclass as dict"""
        return asdict(self)


@dataclass
class NotImplementedException(ApiException):
    """Thrown to mark a function as not yet implemented."""

    status_code: int = status.HTTP_501_NOT_IMPLEMENTED
    id: str = "NOT_IMPLEMENTED"
    message: str = "Function implementation does not exist."


@dataclass
class BadRequestException(ApiException):
    """Thrown if a request was rejected due to incorrect format or content."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    id: str = "BAD_REQUEST"
    message: str = "Malformed request."
