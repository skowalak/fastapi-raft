from typing import List

import structlog
from app.api.api_router import CustomApiRouter
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
consensus_router: APIRouter = CustomApiRouter()
