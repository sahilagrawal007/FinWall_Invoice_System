from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.core.dependencies import get_current_user, get_current_organization
from app.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    PaymentVoidRequest,
)
from app.services.payment_service import PaymentService

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/", response_model=dict)
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    invoice_id: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    is_voided: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get all payments for the organization.

    - **skip**: Pagination offset
    - **limit**: Number of records
    - **invoice_id**: Filter by invoice
    - **customer_id**: Filter by customer
    - **is_voided**: Filter voided/active payments
    """

    payments = await PaymentService.get_payments(
        db=db,
        organization=organization,
        skip=skip,
        limit=limit,
        invoice_id=invoice_id,
        customer_id=customer_id,
        is_voided=is_voided,
    )

    total = await PaymentService.get_payment_count(
        db=db,
        organization=organization,
        invoice_id=invoice_id,
        customer_id=customer_id,
        is_voided=is_voided,
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [PaymentListResponse.model_validate(p) for p in payments],
    }


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def record_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Record a manual payment.

    - Invoice must exist and not be void
    - Amount cannot exceed balance due
    - Payment method: CASH, BANK_TRANSFER, UPI, CHEQUE, etc.
    - Invoice balance updated automatically
    - Invoice status updated automatically
    """

    payment = await PaymentService.record_payment(
        db=db,
        organization=organization,
        payment_data=payment_data,
        current_user=current_user,
    )

    return PaymentResponse.model_validate(payment)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Get payment details by ID."""

    payment = await PaymentService.get_payment_by_id(
        db=db, payment_id=payment_id, organization=organization
    )

    return PaymentResponse.model_validate(payment)


@router.post("/{payment_id}/void", response_model=PaymentResponse)
async def void_payment(
    payment_id: str,
    void_request: PaymentVoidRequest,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Void a payment.

    - Requires a reason
    - Reverses invoice balance
    - Recalculates invoice status
    - Payment record preserved (not deleted)
    """

    payment = await PaymentService.get_payment_by_id(
        db=db, payment_id=payment_id, organization=organization
    )

    payment = await PaymentService.void_payment(
        db=db, payment=payment, void_request=void_request, current_user=current_user
    )

    return PaymentResponse.model_validate(payment)
