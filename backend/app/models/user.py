from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model for authentication"""

    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_staff = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    # Relationships - FIXED: Explicit foreign_keys
    organization_memberships = relationship(
        "OrganizationUser",
        back_populates="user",
        foreign_keys="[OrganizationUser.user_id]",  # FIXED: Specify which FK to use
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def full_name(self):
        """Return user's full name"""
        return f"{self.first_name} {self.last_name}".strip()
