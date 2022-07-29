import collections
import dataclasses
import enum
from typing import Generic, TypeVar

from app.api.models import ApiErrorResponse, ApiResponse
from app.config import get_settings
from pydantic import BaseModel, Field

settings = get_settings()
T = TypeVar("T")


class RaftMessageSchema(BaseModel):
    sender: str = Field(default=settings.HOSTNAME)
    term: int = Field(...)


class VoteRequestSchema(RaftMessageSchema):
    pass


class VoteResponseSchema(RaftMessageSchema):
    pass


class HeartbeatRequestSchema(RaftMessageSchema):
    pass


class HeartbeatResponseSchema(RaftMessageSchema):
    pass


class State(enum.Enum):
    FOLLOWER = "FOLLOWER"
    CANDIDATE = "CANDIDATE"
    LEADER = "LEADER"


class ReplicatedLog(collections.UserList):
    """
    The replicated log Raft uses for cluster consensus

    Inherits
    --------
    collections.UserList
        A fancy way to say inherit from list (which is not possible)
    """

    pass


@dataclasses.dataclass
class RaftStateException(Exception):
    id: str = "RAFT_STATE_EXCEPTION"


class RaftStatusResponseSchema(BaseModel):
    app_name: str
    id: str
    state: str
    term: int


class V1ApiResponse(ApiResponse[T], Generic[T]):
    api_version: str = Field(default="1.0", alias="apiVersion")


class V1ApiErrorResponse(ApiErrorResponse[T], Generic[T]):
    api_version: str = Field(default="1.0", alias="apiVersion")
