"""
Organization Model

Represents a business entity with users and associated data.
"""

from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from app.models.base import UUIDMixin, TimestampMixin


class Organization(Base, UUIDMixin, TimestampMixin):
    """Organization model representing a business entity"""

    __tablename__ = "organizations"

    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)

    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)

    # Address
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), default="India")

    # Tax and Financial
    tax_id = Column(String(50), nullable=True)  # GST Number
    currency_code = Column(String(3), default="INR", nullable=False)
    fiscal_year_end_month = Column(
        Integer, default=3, nullable=False
    )  # March = 3 (Indian FY)

    logo_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    memberships = relationship(
        "OrganizationUser",
        back_populates="organization",
        foreign_keys="[OrganizationUser.organization_id]",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Organization {self.name}>"


class OrganizationUser(Base, TimestampMixin):
    """Junction table linking users to organizations with roles"""

    __tablename__ = "organization_users"

    id = Column(Integer, primary_key=True, autoincrement=True)

    organization_id = Column(
        String(36),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    role = Column(String(20), nullable=False, default="VIEWER")
    is_active = Column(Boolean, default=True, nullable=False)

    invited_by = Column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    joined_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    organization = relationship(
        "Organization",
        back_populates="memberships",
        foreign_keys=[organization_id],
    )

    user = relationship(
        "User",
        back_populates="organization_memberships",
        foreign_keys=[user_id],
    )

    inviter = relationship(
        "User",
        foreign_keys=[invited_by],
    )

    def __repr__(self):
        return (
            f"<OrganizationUser {self.user_id} - {self.organization_id} ({self.role})>"
        )
