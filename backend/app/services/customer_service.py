from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from typing import List, Optional
from app.models.customer import Customer
from app.models.organization import Organization
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.core.exceptions import NotFoundException, DuplicateException


class CustomerService:
    """Service for customer business logic"""

    @staticmethod
    async def get_customers(
        db: AsyncSession,
        organization: Organization,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        customer_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> List[Customer]:
        """Get all customers for organization with filters"""

        query = select(Customer).where(
            and_(
                Customer.organization_id == organization.id,
                Customer.is_deleted == False,
            )
        )

        # Apply filters
        if search:
            query = query.where(
                or_(
                    Customer.name.ilike(f"%{search}%"),
                    Customer.email.ilike(f"%{search}%"),
                    Customer.phone.ilike(f"%{search}%"),
                )
            )

        if customer_type:
            query = query.where(Customer.customer_type == customer_type.upper())

        if is_active is not None:
            query = query.where(Customer.is_active == is_active)

        query = query.offset(skip).limit(limit).order_by(Customer.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_customer_count(
        db: AsyncSession,
        organization: Organization,
        search: Optional[str] = None,
        customer_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """Get total count of customers"""
        from sqlalchemy import func

        query = select(func.count(Customer.id)).where(
            and_(
                Customer.organization_id == organization.id,
                Customer.is_deleted == False,
            )
        )

        if search:
            query = query.where(
                or_(
                    Customer.name.ilike(f"%{search}%"),
                    Customer.email.ilike(f"%{search}%"),
                    Customer.phone.ilike(f"%{search}%"),
                )
            )

        if customer_type:
            query = query.where(Customer.customer_type == customer_type.upper())

        if is_active is not None:
            query = query.where(Customer.is_active == is_active)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_customer_by_id(
        db: AsyncSession, customer_id: str, organization: Organization
    ) -> Customer:
        """Get customer by ID"""

        result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.id == customer_id,
                    Customer.organization_id == organization.id,
                    Customer.is_deleted == False,
                )
            )
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise NotFoundException("Customer not found")

        return customer

    @staticmethod
    async def create_customer(
        db: AsyncSession, organization: Organization, customer_data: CustomerCreate
    ) -> Customer:
        """Create a new customer"""

        # Check for duplicate email in organization
        if customer_data.email:
            result = await db.execute(
                select(Customer).where(
                    and_(
                        Customer.organization_id == organization.id,
                        Customer.email == customer_data.email.lower(),
                        Customer.is_deleted == False,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                raise DuplicateException(
                    "Customer with this email already exists in your organization"
                )

        # Create customer
        customer = Customer(
            organization_id=organization.id,
            **customer_data.model_dump(exclude_unset=True),
        )

        # Lowercase email
        if customer.email:
            customer.email = customer.email.lower()

        db.add(customer)
        await db.commit()
        await db.refresh(customer)

        return customer

    @staticmethod
    async def update_customer(
        db: AsyncSession,
        customer: Customer,
        customer_data: CustomerUpdate,
        organization: Organization,
    ) -> Customer:
        """Update existing customer"""

        # Check for duplicate email if email is being updated
        if customer_data.email:
            result = await db.execute(
                select(Customer).where(
                    and_(
                        Customer.organization_id == organization.id,
                        Customer.email == customer_data.email.lower(),
                        Customer.id != customer.id,
                        Customer.is_deleted == False,
                    )
                )
            )
            existing = result.scalar_one_or_none()

            if existing:
                raise DuplicateException(
                    "Customer with this email already exists in your organization"
                )

        # Update fields
        update_data = customer_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if field == "email" and value:
                setattr(customer, field, value.lower())
            else:
                setattr(customer, field, value)

        await db.commit()
        await db.refresh(customer)

        return customer

    @staticmethod
    async def delete_customer(db: AsyncSession, customer: Customer):
        """Soft delete customer"""

        customer.is_deleted = True
        customer.is_active = False

        await db.commit()
