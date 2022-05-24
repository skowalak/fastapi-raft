"""
In this module: global settings for the APIRouter.
"""
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.api_router import CustomApiRouter
from app.api.auth import mock_users, User, authenticate_user, create_token, Token
from app.api.exceptions import UnauthorizedException
from app.api.v1.consensus_endpoints import consensus_router
from app.api.v1.health_endpoints import health_router


api_router = CustomApiRouter()
"""
Global API Router, parent to all version-specific routers under it.
"""

api_router.include_router(consensus_router, prefix="/v1/elect", tags=["elect", "v1"])
api_router.include_router(health_router, prefix="/v1/health", tags=["health", "v1"])


@api_router.post("/token", response_model=Token)
async def get_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Endpoint for getting a new Bearer Token

    Parameters
    ----------
    form_data
        FastAPI Request Form Data.

    Returns
    -------
    JSONResponse
        Response with new access token.

    Raises
    ------
    UnauthorizedException
        User does not exist or invalid credentials
    """
    try:
        user = authenticate_user(mock_users, form_data.username, form_data.password)
    except KeyError:
        raise UnauthorizedException()

    access_token = create_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
