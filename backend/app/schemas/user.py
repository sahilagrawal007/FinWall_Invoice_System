from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime
# from typing import Optional


class UserBase(BaseModel):
    """Base user schema"""

    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    """Schema for creating a user"""

    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user response"""

    id: UUID
    full_name: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema for user login"""

    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Schema for user registration"""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    organization_name: str = Field(..., min_length=1, max_length=255)
