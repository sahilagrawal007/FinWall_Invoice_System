from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
# from typing import List
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.core.dependencies import get_current_user, get_current_organization
from app.schemas.customer import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    CustomerListResponse,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/", response_model=dict)
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    customer_type: Optional[str] = Query(None, pattern="^(BUSINESS|INDIVIDUAL)$"),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get all customers for the organization.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **search**: Search by name, email, or phone
    - **customer_type**: Filter by BUSINESS or INDIVIDUAL
    - **is_active**: Filter by active status
    """

    customers = await CustomerService.get_customers(
        db=db,
        organization=organization,
        skip=skip,
        limit=limit,
        search=search,
        customer_type=customer_type,
        is_active=is_active,
    )

    total = await CustomerService.get_customer_count(
        db=db,
        organization=organization,
        search=search,
        customer_type=customer_type,
        is_active=is_active,
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [CustomerListResponse.model_validate(c) for c in customers],
    }


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new customer.

    - All address fields are optional
    - Email uniqueness is enforced per organization
    - Currency defaults to INR
    """

    customer = await CustomerService.create_customer(
        db=db, organization=organization, customer_data=customer_data
    )

    return CustomerResponse.model_validate(customer)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get customer details by ID.

    Returns 404 if customer not found or doesn't belong to organization.
    """

    customer = await CustomerService.get_customer_by_id(
        db=db, customer_id=customer_id, organization=organization
    )

    return CustomerResponse.model_validate(customer)


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: str,
    customer_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Update customer (partial update).

    - Only provided fields will be updated
    - Email uniqueness is validated if email is changed
    """

    customer = await CustomerService.get_customer_by_id(
        db=db, customer_id=customer_id, organization=organization
    )

    updated_customer = await CustomerService.update_customer(
        db=db, customer=customer, customer_data=customer_data, organization=organization
    )

    return CustomerResponse.model_validate(updated_customer)


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
async def delete_customer(
    customer_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete customer.

    - Customer is marked as deleted (not permanently removed)
    - Customer is also marked as inactive
    """

    customer = await CustomerService.get_customer_by_id(
        db=db, customer_id=customer_id, organization=organization
    )

    await CustomerService.delete_customer(db=db, customer=customer)

    return {"message": "Customer deleted successfully"}
