from typing import Any, Dict, ForwardRef, TypeVar, Generic, List, Optional
from pydantic import BaseModel, validator, Field
from pydantic.generics import GenericModel

from app.api.exceptions import ApiException

T = TypeVar("T")


class ApiResponse(GenericModel, Generic[T]):
    """
    Defines the base response, which encapsulates all other response types.
    """

    api_version: str = Field(default="", alias="apiVersion")
    context: Optional[str] = None
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    data: T | List[T] = None


class ApiErrorResponse(GenericModel, Generic[T]):
    """
    Defines the base error response, which encapsulates all other response types.
    """

    api_version: str = Field(default="", alias="apiVersion")
    context: Optional[str] = None
    id: Optional[str] = None
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    error: T | List[T] = None
