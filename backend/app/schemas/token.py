from pydantic import BaseModel
from typing import List
from app.schemas.user import UserResponse
from app.schemas.organization import OrganizationUserResponse
# from app.schemas.organization import OrganizationResponse

class Token(BaseModel):
    """Schema for JWT token"""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data"""

    user_id: str
    organization_id: str


class AuthResponse(BaseModel):
    """Schema for authentication response"""

    access_token: str
    token_type: str
    user: UserResponse
    current_organization: OrganizationUserResponse
    organizations: List[OrganizationUserResponse]
