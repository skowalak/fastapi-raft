"""Messaging models and Raft-specific datastructures"""

import dataclasses
from typing import Generic, TypeVar

from pydantic import BaseModel, Field
from fastapi.applications import State as FastAPIState

from app.api.models import ApiErrorResponse, ApiResponse

T = TypeVar("T")


class RaftMessageSchema(BaseModel):
    """Validation model for all Raft messages between nodes."""

    id: str
    sender: str
    term: int

    @classmethod
    def from_state_object(cls, state: FastAPIState) -> "RaftMessageSchema":
        """Factory method creates RaftMessageSchmema from state.

        Parameters
        ----------
        state : FastAPIState
            global state object

        Returns
        -------
        RaftMessageSchema
            new message schema
        """
        return RaftMessageSchema(id=state.id, sender=state.app_name, term=state.term)


class RaftStatusResponseSchema(BaseModel):
    """Response Model for the Monitor status page"""

    app_name: str
    id: str
    state: str
    term: int


@dataclasses.dataclass
class RaftStateException(Exception):
    """Gets thrown if a state can no longer be held."""

    id: str = "RAFT_STATE_EXCEPTION"


class V1ApiResponse(ApiResponse[T], Generic[T]):
    """ApiResponse specific to the first version of the API"""

    api_version: str = Field(default="1.0", alias="apiVersion")


class V1ApiErrorResponse(ApiErrorResponse[T], Generic[T]):
    """ApiErrorResponse specific to the first version of the API"""

    api_version: str = Field(default="1.0", alias="apiVersion")
