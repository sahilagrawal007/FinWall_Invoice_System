from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
# from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.organization import Organization, OrganizationUser
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token"""

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode token
        token = credentials.credentials
        payload = decode_access_token(token)
        user_id: str = payload.get("user_id")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User account is disabled"
        )

    return user


async def get_current_organization(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Organization:
    """Get current organization from JWT token"""

    try:
        # Decode token
        token = credentials.credentials
        payload = decode_access_token(token)
        organization_id: str = payload.get("organization_id")

        if organization_id is None:
            raise UnauthorizedException("Organization ID not found in token")

    except JWTError:
        raise UnauthorizedException("Invalid token")

    # Verify user has access to this organization
    result = await db.execute(
        select(OrganizationUser)
        .where(OrganizationUser.user_id == current_user.id)
        .where(OrganizationUser.organization_id == organization_id)
        .where(OrganizationUser.is_active == True)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise UnauthorizedException("User does not have access to this organization")

    # Get organization
    result = await db.execute(
        select(Organization).where(Organization.id == organization_id)
    )
    organization = result.scalar_one_or_none()

    if not organization:
        raise UnauthorizedException("Organization not found")

    if not organization.is_active:
        raise UnauthorizedException("Organization is inactive")

    return organization
