from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class OrganizationBase(BaseModel):
    """Base organization schema"""

    name: str
    legal_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: str = "India"
    currency_code: str = "INR"


class OrganizationResponse(OrganizationBase):
    """Schema for organization response"""

    id: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class OrganizationUserResponse(BaseModel):
    """Schema for organization membership response"""

    id: str
    name: str
    role: str

    class Config:
        from_attributes = True
