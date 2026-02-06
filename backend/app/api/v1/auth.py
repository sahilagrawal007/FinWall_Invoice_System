from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.user import RegisterRequest, UserLogin, UserResponse
from app.schemas.token import AuthResponse
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(register_data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Register a new user and create organization.

    - Creates user account
    - Creates organization
    - Links user as OWNER
    - Returns JWT token
    """
    auth_response = await AuthService.register_user(db, register_data)

    # Wrap in data field for frontend
    return {
        "success": True,
        "data": {
            "access_token": auth_response.access_token,
            "token_type": auth_response.token_type,
            "user": {
                "id": str(auth_response.user.id),
                "email": auth_response.user.email,
                "first_name": auth_response.user.first_name,
                "last_name": auth_response.user.last_name,
                "full_name": auth_response.user.full_name,
                "is_active": auth_response.user.is_active,
                "created_at": auth_response.user.created_at.isoformat(),
            },
            "current_organization": {
                "id": str(auth_response.current_organization.id),
                "name": auth_response.current_organization.name,
                "role": auth_response.current_organization.role,
            },
            "organizations": [
                {"id": str(org.id), "name": org.name, "role": org.role}
                for org in auth_response.organizations
            ],
        },
    }


@router.post("/login")
async def login(login_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """
    Login user and return JWT token.

    - Validates credentials
    - Returns user info and organizations
    - Returns JWT access token
    """
    auth_response = await AuthService.authenticate_user(
        db, login_data.email, login_data.password
    )

    # Wrap in data field for frontend
    return {
        "success": True,
        "data": {
            "access_token": auth_response.access_token,
            "token_type": auth_response.token_type,
            "user": {
                "id": str(auth_response.user.id),
                "email": auth_response.user.email,
                "first_name": auth_response.user.first_name,
                "last_name": auth_response.user.last_name,
                "full_name": auth_response.user.full_name,
                "is_active": auth_response.user.is_active,
                "created_at": auth_response.user.created_at.isoformat(),
            },
            "current_organization": {
                "id": str(auth_response.current_organization.id),
                "name": auth_response.current_organization.name,
                "role": auth_response.current_organization.role,
            },
            "organizations": [
                {"id": str(org.id), "name": org.name, "role": org.role}
                for org in auth_response.organizations
            ],
        },
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.

    Requires: Bearer token in Authorization header
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
