from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# from datetime import timedelta
# from typing import Optional
from app.models.user import User
from app.models.organization import Organization, OrganizationUser
from app.schemas.user import RegisterRequest
from app.schemas.token import AuthResponse
from app.core.security import verify_password, get_password_hash, create_access_token
from app.core.exceptions import UnauthorizedException, DuplicateException
# from app.config import settings


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    async def register_user(
        db: AsyncSession, register_data: RegisterRequest
    ) -> AuthResponse:
        """Register a new user and create organization"""

        # Check if user already exists
        result = await db.execute(
            select(User).where(User.email == register_data.email.lower())
        )
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise DuplicateException("User with this email already exists")

        # Create user
        user = User(
            email=register_data.email.lower(),
            hashed_password=get_password_hash(register_data.password),
            first_name=register_data.first_name,
            last_name=register_data.last_name,
            is_active=True,
        )
        db.add(user)
        await db.flush()  # Get user.id

        # Create organization
        organization = Organization(
            name=register_data.organization_name, email=register_data.email.lower()
        )
        db.add(organization)
        await db.flush()  # Get organization.id

        # Link user to organization as OWNER
        org_user = OrganizationUser(
            user_id=user.id,
            organization_id=organization.id,
            role="OWNER",
            is_active=True,
        )
        db.add(org_user)

        await db.commit()
        await db.refresh(user)
        await db.refresh(organization)

        # Generate access token
        access_token = create_access_token(
            data={
                "user_id": str(user.id),
                "organization_id": str(organization.id),
                "email": user.email,
            }
        )

        # Prepare response
        from app.schemas.user import UserResponse
        from app.schemas.organization import OrganizationUserResponse

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at,
            ),
            current_organization=OrganizationUserResponse(
                id=organization.id, name=organization.name, role="OWNER"
            ),
            organizations=[
                OrganizationUserResponse(
                    id=organization.id, name=organization.name, role="OWNER"
                )
            ],
        )

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, email: str, password: str
    ) -> AuthResponse:
        """Authenticate user and return tokens"""

        # Find user by email
        result = await db.execute(select(User).where(User.email == email.lower()))
        user = result.scalar_one_or_none()

        if not user:
            raise UnauthorizedException("Invalid email or password")

        # Verify password
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedException("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            raise UnauthorizedException("User account is disabled")

        # Get user's organizations
        result = await db.execute(
            select(OrganizationUser)
            .where(OrganizationUser.user_id == user.id)
            .where(OrganizationUser.is_active == True)
        )
        memberships = result.scalars().all()

        if not memberships:
            raise UnauthorizedException("User has no active organizations")

        # Get first organization (user can switch later)
        first_membership = memberships[0]

        # Load organization
        result = await db.execute(
            select(Organization).where(
                Organization.id == first_membership.organization_id
            )
        )
        organization = result.scalar_one()

        # Generate access token
        access_token = create_access_token(
            data={
                "user_id": str(user.id),
                "organization_id": str(organization.id),
                "email": user.email,
            }
        )

        # Prepare organizations list
        organizations_list = []
        for membership in memberships:
            result = await db.execute(
                select(Organization).where(
                    Organization.id == membership.organization_id
                )
            )
            org = result.scalar_one()

            from app.schemas.organization import OrganizationUserResponse

            organizations_list.append(
                OrganizationUserResponse(id=org.id, name=org.name, role=membership.role)
            )

        # Prepare response
        from app.schemas.user import UserResponse
        from app.schemas.organization import OrganizationUserResponse

        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at,
            ),
            current_organization=OrganizationUserResponse(
                id=organization.id, name=organization.name, role=first_membership.role
            ),
            organizations=organizations_list,
        )
