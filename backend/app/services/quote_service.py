from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime, date
from decimal import Decimal
from app.models.quote import Quote, QuoteItem
from app.models.invoice import Invoice, InvoiceItem
from app.models.customer import Customer
from app.models.item import Item
from app.models.tax import Tax
from app.models.organization import Organization
from app.models.user import User
from app.schemas.quote import (
    QuoteCreate,
    QuoteUpdate,
    QuoteAcceptRequest,
    QuoteRejectRequest,
)
from app.core.exceptions import NotFoundException, ValidationException


class QuoteService:
    """Service for quote business logic"""

    @staticmethod
    async def get_quotes(
        db: AsyncSession,
        organization: Organization,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> List[Quote]:
        """Get all quotes for organization"""

        query = (
            select(Quote)
            .options(joinedload(Quote.customer), joinedload(Quote.items))
            .where(
                and_(
                    Quote.organization_id == organization.id, Quote.is_deleted == False
                )
            )
        )

        if status:
            query = query.where(Quote.status == status.upper())

        if customer_id:
            query = query.where(Quote.customer_id == customer_id)

        query = query.offset(skip).limit(limit).order_by(Quote.created_at.desc())

        result = await db.execute(query)
        return result.unique().scalars().all()

    @staticmethod
    async def get_quote_count(
        db: AsyncSession,
        organization: Organization,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> int:
        """Get total count of quotes"""

        query = select(func.count(Quote.id)).where(
            and_(Quote.organization_id == organization.id, Quote.is_deleted == False)
        )

        if status:
            query = query.where(Quote.status == status.upper())

        if customer_id:
            query = query.where(Quote.customer_id == customer_id)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_quote_by_id(
        db: AsyncSession, quote_id: str, organization: Organization
    ) -> Quote:
        """Get quote by ID with all relationships"""

        result = await db.execute(
            select(Quote)
            .options(joinedload(Quote.customer), joinedload(Quote.items))
            .where(
                and_(
                    Quote.id == quote_id,
                    Quote.organization_id == organization.id,
                    Quote.is_deleted == False,
                )
            )
        )
        quote = result.unique().scalar_one_or_none()

        if not quote:
            raise NotFoundException("Quote not found")

        return quote

    @staticmethod
    async def _generate_quote_number(
        db: AsyncSession, organization: Organization
    ) -> str:
        """Generate next quote number for organization"""

        result = await db.execute(
            select(Quote.quote_number)
            .where(Quote.organization_id == organization.id)
            .order_by(Quote.created_at.desc())
            .limit(1)
        )
        last_number = result.scalar_one_or_none()

        if last_number:
            try:
                num = int(last_number.split("-")[1]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"QT-{num:05d}"

    @staticmethod
    async def _calculate_line_item(
        quantity: Decimal, rate: Decimal, tax_rate: Decimal
    ) -> dict:
        """Calculate line item amounts (same as invoice)"""

        amount = (quantity * rate).quantize(Decimal("0.01"))
        tax_amount = (amount * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        total = (amount + tax_amount).quantize(Decimal("0.01"))

        return {"amount": amount, "tax_amount": tax_amount, "total": total}

    @staticmethod
    async def create_quote(
        db: AsyncSession,
        organization: Organization,
        quote_data: QuoteCreate,
        current_user: User,
    ) -> Quote:
        """Create a new quote with line items"""

        # 1. Validate customer
        result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.id == quote_data.customer_id,
                    Customer.organization_id == organization.id,
                    Customer.is_deleted == False,
                )
            )
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise NotFoundException("Customer not found")

        # 2. Validate dates
        if quote_data.expiry_date < quote_data.quote_date:
            raise ValidationException("Expiry date cannot be before quote date")

        # 3. Process line items and calculate totals (same logic as invoice)
        calculated_items = []
        subtotal = Decimal("0")
        tax_total = Decimal("0")

        for idx, item_data in enumerate(quote_data.items):
            # Get item details if item_id provided
            if item_data.item_id:
                result = await db.execute(
                    select(Item).where(
                        and_(
                            Item.id == item_data.item_id,
                            Item.organization_id == organization.id,
                            Item.is_deleted == False,
                        )
                    )
                )
                item = result.scalar_one_or_none()
                if not item:
                    raise NotFoundException(f"Item {item_data.item_id} not found")

            # Get tax rate
            tax_rate = Decimal("0")
            tax_id = item_data.tax_id
            if tax_id:
                result = await db.execute(
                    select(Tax).where(
                        and_(
                            Tax.id == tax_id,
                            Tax.organization_id == organization.id,
                            Tax.is_deleted == False,
                        )
                    )
                )
                tax = result.scalar_one_or_none()
                if tax:
                    tax_rate = tax.rate
                else:
                    raise NotFoundException(f"Tax {tax_id} not found")

            # Calculate amounts
            calculations = await QuoteService._calculate_line_item(
                item_data.quantity, item_data.rate, tax_rate
            )

            calculated_items.append(
                {
                    "item_id": item_data.item_id,
                    "description": item_data.description,
                    "quantity": item_data.quantity,
                    "rate": item_data.rate,
                    "amount": calculations["amount"],
                    "tax_id": tax_id,
                    "tax_rate": tax_rate,
                    "tax_amount": calculations["tax_amount"],
                    "total": calculations["total"],
                    "sort_order": idx,
                }
            )

            subtotal += calculations["amount"]
            tax_total += calculations["tax_amount"]

        total = subtotal + tax_total

        # 4. Generate quote number
        quote_number = await QuoteService._generate_quote_number(db, organization)

        # 5. Create quote and items in transaction
        async with db.begin_nested():
            quote = Quote(
                organization_id=organization.id,
                customer_id=customer.id,
                quote_number=quote_number,
                status="DRAFT",
                quote_date=quote_data.quote_date,
                expiry_date=quote_data.expiry_date,
                subtotal=subtotal,
                tax_total=tax_total,
                total=total,
                currency_code=customer.currency_code,
                notes=quote_data.notes,
                terms_and_conditions=quote_data.terms_and_conditions,
                created_by=current_user.id,
            )
            db.add(quote)
            await db.flush()

            # Create quote items
            for item_data in calculated_items:
                quote_item = QuoteItem(quote_id=quote.id, **item_data)
                db.add(quote_item)

        await db.commit()
        await db.refresh(quote)

        # Load relationships
        result = await db.execute(
            select(Quote)
            .options(joinedload(Quote.customer), joinedload(Quote.items))
            .where(Quote.id == quote.id)
        )
        quote = result.unique().scalar_one()

        return quote

    @staticmethod
    async def send_quote(db: AsyncSession, quote: Quote) -> Quote:
        """Mark quote as sent"""

        if quote.status not in ["DRAFT", "SENT"]:
            raise ValidationException(f"Cannot send quote with status {quote.status}")

        if quote.status == "DRAFT":
            quote.status = "SENT"
            quote.sent_at = datetime.utcnow()

        await db.commit()
        await db.refresh(quote)

        return quote

    @staticmethod
    async def accept_quote(
        db: AsyncSession, quote: Quote, accept_request: QuoteAcceptRequest
    ) -> Quote:
        """Mark quote as accepted"""

        if quote.status not in ["SENT", "VIEWED"]:
            raise ValidationException(f"Cannot accept quote with status {quote.status}")

        # Check if expired
        if quote.expiry_date < date.today():
            raise ValidationException("Cannot accept expired quote")

        quote.status = "ACCEPTED"
        quote.accepted_at = datetime.utcnow()

        if accept_request.notes:
            quote.notes = (
                quote.notes or ""
            ) + f"\n\nAcceptance Notes: {accept_request.notes}"

        await db.commit()
        await db.refresh(quote)

        return quote

    @staticmethod
    async def reject_quote(
        db: AsyncSession, quote: Quote, reject_request: QuoteRejectRequest
    ) -> Quote:
        """Mark quote as rejected"""

        if quote.status not in ["SENT", "VIEWED"]:
            raise ValidationException(f"Cannot reject quote with status {quote.status}")

        quote.status = "REJECTED"
        quote.rejected_at = datetime.utcnow()
        quote.notes = (
            quote.notes or ""
        ) + f"\n\nRejection Reason: {reject_request.reason}"

        await db.commit()
        await db.refresh(quote)

        return quote

    @staticmethod
    async def convert_to_invoice(
        db: AsyncSession, quote: Quote, current_user: User
    ) -> Invoice:
        """Convert accepted quote to invoice"""

        if quote.status != "ACCEPTED":
            raise ValidationException(
                "Only accepted quotes can be converted to invoices"
            )

        if quote.converted_invoice_id:
            raise ValidationException("Quote has already been converted to invoice")

        # Get customer
        result = await db.execute(
            select(Customer).where(Customer.id == quote.customer_id)
        )
        customer = result.scalar_one()

        # Generate invoice number
        from app.services.invoice_service import InvoiceService

        invoice_number = await InvoiceService._generate_invoice_number(
            db, quote.organization
        )

        # Create invoice from quote
        async with db.begin_nested():
            invoice = Invoice(
                organization_id=quote.organization_id,
                customer_id=quote.customer_id,
                invoice_number=invoice_number,
                status="DRAFT",
                invoice_date=date.today(),
                due_date=date.today(),  # Will be updated by user
                subtotal=quote.subtotal,
                tax_total=quote.tax_total,
                total=quote.total,
                amount_paid=Decimal("0"),
                balance_due=quote.total,
                currency_code=quote.currency_code,
                payment_terms_days=customer.payment_terms_days,
                notes=quote.notes,
                terms_and_conditions=quote.terms_and_conditions,
                created_by=current_user.id,
            )
            db.add(invoice)
            await db.flush()

            # Copy quote items to invoice items
            result = await db.execute(
                select(QuoteItem).where(QuoteItem.quote_id == quote.id)
            )
            quote_items = result.scalars().all()

            for q_item in quote_items:
                invoice_item = InvoiceItem(
                    invoice_id=invoice.id,
                    item_id=q_item.item_id,
                    description=q_item.description,
                    quantity=q_item.quantity,
                    rate=q_item.rate,
                    amount=q_item.amount,
                    tax_id=q_item.tax_id,
                    tax_rate=q_item.tax_rate,
                    tax_amount=q_item.tax_amount,
                    total=q_item.total,
                    sort_order=q_item.sort_order,
                )
                db.add(invoice_item)

            # Update quote
            quote.status = "CONVERTED"
            quote.converted_at = datetime.utcnow()
            quote.converted_invoice_id = invoice.id

        await db.commit()
        await db.refresh(invoice)

        # Load relationships
        result = await db.execute(
            select(Invoice)
            .options(joinedload(Invoice.customer), joinedload(Invoice.items))
            .where(Invoice.id == invoice.id)
        )
        invoice = result.unique().scalar_one()

        return invoice
