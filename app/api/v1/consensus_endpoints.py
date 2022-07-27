from typing import List

import structlog
from app.api.auth import User
from app.api.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    NotImplementedException,
)
from app.api.v1.models import (
    V1ApiErrorResponse,
    V1ApiResponse,
)
from fastapi import APIRouter, Depends, Response

logger: structlog.stdlib.AsyncBoundLogger = structlog.get_logger(__name__)
consensus_router: APIRouter = APIRouter()


@consensus_router.post("/vote")
def vote():
    return V1ApiResponse(data={})
