from typing import Dict, Generic, TypeVar

from app.api.models import ApiErrorResponse, ApiResponse
from app.config import get_settings
from pydantic import BaseModel, Field


settings = get_settings()
T = TypeVar("T")


class RaftMessageSchema(BaseModel):
    sender_id: str = Field(default=settings.HOSTNAME)
    term: int = Field(...)


class VoteRequestSchema(RaftMessageSchema):
    pass


class VoteResponseSchema(RaftMessageSchema):
    pass


class AppendLogRequestSchema(RaftMessageSchema):
    pass


class AppendLogResponseSchema(RaftMessageSchema):
    pass


class V1ApiResponse(ApiResponse[T], Generic[T]):
    api_version: str = Field(default="1.0", alias="apiVersion")


class V1ApiErrorResponse(ApiErrorResponse[T], Generic[T]):
    api_version: str = Field(default="1.0", alias="apiVersion")
