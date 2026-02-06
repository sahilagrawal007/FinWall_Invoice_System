from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.core.dependencies import get_current_user, get_current_organization
from app.schemas.invoice import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceListResponse,
    InvoiceVoidRequest,
)
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["Invoices"])


@router.get("/", response_model=dict)
async def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get all invoices for the organization.

    - **skip**: Pagination offset
    - **limit**: Number of records
    - **status**: Filter by status (DRAFT, SENT, PAID, etc.)
    - **customer_id**: Filter by customer
    """

    invoices = await InvoiceService.get_invoices(
        db=db,
        organization=organization,
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
    )

    total = await InvoiceService.get_invoice_count(
        db=db, organization=organization, status=status, customer_id=customer_id
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [InvoiceListResponse.model_validate(i) for i in invoices],
    }


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new invoice.

    - Customer must exist in organization
    - At least one line item required
    - Calculations done server-side
    - Invoice number auto-generated
    - Status starts as DRAFT
    """

    invoice = await InvoiceService.create_invoice(
        db=db,
        organization=organization,
        invoice_data=invoice_data,
        current_user=current_user,
    )

    return InvoiceResponse.model_validate(invoice)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Get invoice details with all line items."""

    invoice = await InvoiceService.get_invoice_by_id(
        db=db, invoice_id=invoice_id, organization=organization
    )

    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/send", response_model=InvoiceResponse)
async def send_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Mark invoice as sent.

    - Changes status from DRAFT to SENT
    - Records sent_at timestamp
    - Cannot send if already PAID or VOID
    """

    invoice = await InvoiceService.get_invoice_by_id(
        db=db, invoice_id=invoice_id, organization=organization
    )

    invoice = await InvoiceService.send_invoice(db=db, invoice=invoice)

    return InvoiceResponse.model_validate(invoice)


@router.post("/{invoice_id}/void", response_model=InvoiceResponse)
async def void_invoice(
    invoice_id: str,
    void_request: InvoiceVoidRequest,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Void an invoice.

    - Requires a reason
    - Cannot void PAID invoices
    - Changes status to VOID
    - Records voided_at timestamp
    """

    invoice = await InvoiceService.get_invoice_by_id(
        db=db, invoice_id=invoice_id, organization=organization
    )

    invoice = await InvoiceService.void_invoice(
        db=db, invoice=invoice, void_request=void_request
    )

    return InvoiceResponse.model_validate(invoice)
