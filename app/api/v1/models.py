from datetime import datetime
from typing import Generic, TypeVar, List
import uuid

from app.api.models import ApiErrorResponse, ApiResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


class V1ApiResponse(ApiResponse[T], Generic[T]):
    api_version: str = Field(default="1.0", alias="apiVersion")


class V1ApiErrorResponse(ApiErrorResponse[T], Generic[T]):
    api_version: str = Field(default="1.0", alias="apiVersion")
