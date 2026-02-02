"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AuthServiceDep
from app.core.exceptions import AlreadyExistsError, InvalidCredentialsError
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User created successfully"},
        409: {"description": "User already exists"},
    },
)
async def register(
    data: RegisterRequest,
    auth_service: AuthServiceDep,
) -> UserResponse:
    """
    Register a new user.

    - **login**: Unique username (3-100 characters)
    - **password**: Strong password (min 8 characters)
    - **repeat_password**: Must match password
    - **email**: Optional email address
    """
    try:
        user = await auth_service.register(data)
        return UserResponse.model_validate(user)
    except AlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        ) from e


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login to get access token",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    },
)
async def login(
    data: LoginRequest,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    """
    Authenticate and get a JWT access token.

    - **login**: User's login
    - **password**: User's password

    Returns a JWT token valid for 1 hour.
    """
    try:
        return await auth_service.login(data)
    except InvalidCredentialsError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
