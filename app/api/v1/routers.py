"""API v1 routers (ALTERNATIVE - Using Application Service).

This is an alternative implementation that uses an Application Service layer
to hide database/infrastructure concerns from the API layer.

Compare with the current routers.py to see the difference in approach.
"""

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.v1.schemas.auth import LoginRequest, TokenResponse
from app.api.v1.schemas.expense import ExpenseCreateCommand, ExpenseResponse
from app.api.v1.schemas.user import UserRegisterRequest, UserResponse
from app.application.services.expense_service import ExpenseApplicationService
from app.application.services.user_service import UserApplicationService
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user_id

router = APIRouter()


@router.get(
    "/",
    summary="API Welcome",
    tags=["Health"],
)
async def root():
    """Welcome endpoint for the API.

    Returns:
        Welcome message with API information.
    """
    return {
        "message": "Welcome to Aequatio API",
        "version": "1.0.0",
        "docs": "/docs",
    }


def get_user_service(db: Session = Depends(get_db)) -> UserApplicationService:
    """Dependency injection for UserApplicationService.

    This hides the database session from the API layer.
    The API only knows about the service, not the database.
    """
    return UserApplicationService(db)


def get_expense_service(db: Session = Depends(get_db)):
    """Dependency injection for ExpenseApplicationService.

    This hides the database session from the API layer.
    The API only knows about the service, not the database.
    """

    return ExpenseApplicationService(db)


@router.post(
    "/expense",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new expense",
    tags=["Expenses"],
)
async def create_expense(
    expense_data: ExpenseCreateCommand,
    expense_service: ExpenseApplicationService = Depends(get_expense_service),
    user_id: UUID = Depends(get_current_user_id),
) -> ExpenseResponse:
    """Create a new expense for the authenticated user.

    The user ID is automatically extracted from the JWT token.
    """
    expense = expense_service.create_expense(expense_data, user_id)
    return ExpenseResponse.model_validate(expense)


@router.post(
    "/users/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    tags=["Authentication"],
)
async def register_user(
    user_data: UserRegisterRequest,
    request: Request,
    user_service: UserApplicationService = Depends(get_user_service),  # ← Service, not DB!
):
    """Register a new user using application service.

    Notice: This endpoint doesn't know about database sessions or repositories.
    It only calls the application service which handles everything.

    Args:
        user_data: Registration request.
        request: FastAPI request for metadata.
        user_service: Injected application service (hides DB concerns).

    Returns:
        UserResponse with created user data.
    """
    # Extract metadata
    metadata = {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown"),
    }

    try:
        # Call application service (it handles domain, persistence, transaction)
        user = user_service.register_user(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
            metadata=metadata,
        )

        return UserResponse.model_validate(user)

    except ValueError as e:
        error_msg = str(e)

        if "already taken" in error_msg or "already registered" in error_msg:
            status_code = status.HTTP_409_CONFLICT
        else:
            status_code = status.HTTP_400_BAD_REQUEST

        raise HTTPException(status_code=status_code, detail=error_msg) from e

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}",
        ) from e


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login with email and password",
    tags=["Authentication"],
)
async def login(
    login_data: LoginRequest,
    user_service: UserApplicationService = Depends(get_user_service),
):
    """Authenticate user and return JWT access token.

    Args:
        login_data: Login credentials (email and password).
        user_service: Injected application service.

    Returns:
        TokenResponse with JWT access token.

    Raises:
        HTTPException: 401 if credentials are invalid or user is inactive.

    Example:
        POST /api/v1/auth/login
        {
            "email": "john@example.com",
            "password": "SecurePass123!"
        }

        Response:
        {
            "access_token": "eyJhbGc...",
            "token_type": "bearer"
        }
    """
    # Authenticate user
    user = user_service.authenticate_user(
        email=login_data.email,
        password=login_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create JWT token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires,
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get("/users/{user_id}", response_model=UserResponse, tags=["Users"])
async def get_user(user_id: UUID, user_service: UserApplicationService = Depends(get_user_service)):
    """Get user by ID.

    Args:
        user_id: User identifier (UUID).
        user_service: Injected application service.

    Returns:
        User data.

    Raises:
        HTTPException: 404 if user not found.
    """
    user = user_service.get_user_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {user_id} not found"
        )

    return UserResponse.model_validate(user)
