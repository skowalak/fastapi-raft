"""
In this module: global settings for the APIRouter.
"""
from fastapi.routing import APIRouter

from app.api.auth import mock_users, User, authenticate_user, create_token, Token
from app.api.exceptions import UnauthorizedException
from app.api.v1.consensus_endpoints import consensus_router
from app.api.v1.health_endpoints import health_router


api_router = APIRouter()
"""
Global API Router, parent to all version-specific routers under it.
"""

api_router.include_router(consensus_router, prefix="/v1/elect", tags=["elect", "v1"])
api_router.include_router(health_router, prefix="/v1/health", tags=["health", "v1"])
