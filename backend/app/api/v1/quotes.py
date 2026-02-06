from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.models.organization import Organization
from app.models.user import User
from app.core.dependencies import get_current_user, get_current_organization
from app.schemas.quote import (
    QuoteCreate,
    QuoteResponse,
    QuoteListResponse,
    QuoteAcceptRequest,
    QuoteRejectRequest,
)
from app.schemas.invoice import InvoiceResponse
from app.services.quote_service import QuoteService

router = APIRouter(prefix="/quotes", tags=["Quotes"])


@router.get("/", response_model=dict)
async def list_quotes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Get all quotes for the organization.

    - **skip**: Pagination offset
    - **limit**: Number of records
    - **status**: Filter by status (DRAFT, SENT, ACCEPTED, etc.)
    - **customer_id**: Filter by customer
    """

    quotes = await QuoteService.get_quotes(
        db=db,
        organization=organization,
        skip=skip,
        limit=limit,
        status=status,
        customer_id=customer_id,
    )

    total = await QuoteService.get_quote_count(
        db=db, organization=organization, status=status, customer_id=customer_id
    )

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "data": [QuoteListResponse.model_validate(q) for q in quotes],
    }


@router.post("/", response_model=QuoteResponse, status_code=status.HTTP_201_CREATED)
async def create_quote(
    quote_data: QuoteCreate,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new quote.

    - Customer must exist
    - At least one line item required
    - Calculations done server-side
    - Quote number auto-generated
    - Status starts as DRAFT
    """

    quote = await QuoteService.create_quote(
        db=db,
        organization=organization,
        quote_data=quote_data,
        current_user=current_user,
    )

    return QuoteResponse.model_validate(quote)


@router.get("/{quote_id}", response_model=QuoteResponse)
async def get_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """Get quote details with all line items."""

    quote = await QuoteService.get_quote_by_id(
        db=db, quote_id=quote_id, organization=organization
    )

    return QuoteResponse.model_validate(quote)


@router.post("/{quote_id}/send", response_model=QuoteResponse)
async def send_quote(
    quote_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Mark quote as sent.

    - Changes status from DRAFT to SENT
    - Records sent_at timestamp
    """

    quote = await QuoteService.get_quote_by_id(
        db=db, quote_id=quote_id, organization=organization
    )

    quote = await QuoteService.send_quote(db=db, quote=quote)

    return QuoteResponse.model_validate(quote)


@router.post("/{quote_id}/accept", response_model=QuoteResponse)
async def accept_quote(
    quote_id: str,
    accept_request: QuoteAcceptRequest,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Mark quote as accepted.

    - Quote must be SENT or VIEWED
    - Cannot accept expired quotes
    - Changes status to ACCEPTED
    """

    quote = await QuoteService.get_quote_by_id(
        db=db, quote_id=quote_id, organization=organization
    )

    quote = await QuoteService.accept_quote(
        db=db, quote=quote, accept_request=accept_request
    )

    return QuoteResponse.model_validate(quote)


@router.post("/{quote_id}/reject", response_model=QuoteResponse)
async def reject_quote(
    quote_id: str,
    reject_request: QuoteRejectRequest,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Mark quote as rejected.

    - Requires a reason
    - Changes status to REJECTED
    """

    quote = await QuoteService.get_quote_by_id(
        db=db, quote_id=quote_id, organization=organization
    )

    quote = await QuoteService.reject_quote(
        db=db, quote=quote, reject_request=reject_request
    )

    return QuoteResponse.model_validate(quote)


@router.post("/{quote_id}/convert", response_model=InvoiceResponse)
async def convert_quote_to_invoice(
    quote_id: str,
    db: AsyncSession = Depends(get_db),
    organization: Organization = Depends(get_current_organization),
    current_user: User = Depends(get_current_user),
):
    """
    Convert accepted quote to invoice.

    - Quote must be ACCEPTED
    - Creates new invoice with same line items
    - Invoice starts as DRAFT
    - Quote status changes to CONVERTED
    - Link preserved between quote and invoice
    """

    quote = await QuoteService.get_quote_by_id(
        db=db, quote_id=quote_id, organization=organization
    )

    invoice = await QuoteService.convert_to_invoice(
        db=db, quote=quote, current_user=current_user
    )

    return InvoiceResponse.model_validate(invoice)
