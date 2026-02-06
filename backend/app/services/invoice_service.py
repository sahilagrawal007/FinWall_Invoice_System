from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from app.models.invoice import Invoice, InvoiceItem
from app.models.customer import Customer
from app.models.item import Item
from app.models.tax import Tax
from app.models.organization import Organization
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoiceVoidRequest
from app.core.exceptions import NotFoundException, ValidationException


class InvoiceService:
    """Service for invoice business logic"""

    @staticmethod
    async def get_invoices(
        db: AsyncSession,
        organization: Organization,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> List[Invoice]:
        """Get all invoices for organization"""

        query = (
            select(Invoice)
            .options(joinedload(Invoice.customer), joinedload(Invoice.items))
            .where(
                and_(
                    Invoice.organization_id == organization.id,
                    Invoice.is_deleted == False,
                )
            )
        )

        if status:
            query = query.where(Invoice.status == status.upper())

        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)

        query = query.offset(skip).limit(limit).order_by(Invoice.created_at.desc())

        result = await db.execute(query)
        return result.unique().scalars().all()

    @staticmethod
    async def get_invoice_count(
        db: AsyncSession,
        organization: Organization,
        status: Optional[str] = None,
        customer_id: Optional[str] = None,
    ) -> int:
        """Get total count of invoices"""

        query = select(func.count(Invoice.id)).where(
            and_(
                Invoice.organization_id == organization.id, Invoice.is_deleted == False
            )
        )

        if status:
            query = query.where(Invoice.status == status.upper())

        if customer_id:
            query = query.where(Invoice.customer_id == customer_id)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def get_invoice_by_id(
        db: AsyncSession, invoice_id: str, organization: Organization
    ) -> Invoice:
        """Get invoice by ID with all relationships"""

        result = await db.execute(
            select(Invoice)
            .options(joinedload(Invoice.customer), joinedload(Invoice.items))
            .where(
                and_(
                    Invoice.id == invoice_id,
                    Invoice.organization_id == organization.id,
                    Invoice.is_deleted == False,
                )
            )
        )
        invoice = result.unique().scalar_one_or_none()

        if not invoice:
            raise NotFoundException("Invoice not found")

        return invoice

    @staticmethod
    async def _generate_invoice_number(
        db: AsyncSession, organization: Organization
    ) -> str:
        """Generate next invoice number for organization"""

        # Get the last invoice number
        result = await db.execute(
            select(Invoice.invoice_number)
            .where(Invoice.organization_id == organization.id)
            .order_by(Invoice.created_at.desc())
            .limit(1)
        )
        last_number = result.scalar_one_or_none()

        if last_number:
            # Extract number from "INV-00001"
            try:
                num = int(last_number.split("-")[1]) + 1
            except:
                num = 1
        else:
            num = 1

        return f"INV-{num:05d}"

    @staticmethod
    async def _calculate_line_item(
        quantity: Decimal, rate: Decimal, tax_rate: Decimal
    ) -> dict:
        """Calculate line item amounts"""

        # Round to 2 decimal places
        amount = (quantity * rate).quantize(Decimal("0.01"))
        tax_amount = (amount * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
        total = (amount + tax_amount).quantize(Decimal("0.01"))

        return {"amount": amount, "tax_amount": tax_amount, "total": total}

    @staticmethod
    async def create_invoice(
        db: AsyncSession,
        organization: Organization,
        invoice_data: InvoiceCreate,
        current_user: User,
    ) -> Invoice:
        """Create a new invoice with line items"""

        # 1. Validate customer
        result = await db.execute(
            select(Customer).where(
                and_(
                    Customer.id == invoice_data.customer_id,
                    Customer.organization_id == organization.id,
                    Customer.is_deleted == False,
                )
            )
        )
        customer = result.scalar_one_or_none()

        if not customer:
            raise NotFoundException("Customer not found")

        # 2. Validate dates
        if invoice_data.due_date < invoice_data.invoice_date:
            raise ValidationException("Due date cannot be before invoice date")

        # 3. Process line items and calculate totals
        calculated_items = []
        subtotal = Decimal("0")
        tax_total = Decimal("0")

        for idx, item_data in enumerate(invoice_data.items):
            # Get item details if item_id provided
            item_name = item_data.description
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
            calculations = await InvoiceService._calculate_line_item(
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

        # 4. Generate invoice number
        invoice_number = await InvoiceService._generate_invoice_number(db, organization)

        # 5. Create invoice and items in transaction
        async with db.begin_nested():
            invoice = Invoice(
                organization_id=organization.id,
                customer_id=customer.id,
                invoice_number=invoice_number,
                status="DRAFT",
                invoice_date=invoice_data.invoice_date,
                due_date=invoice_data.due_date,
                subtotal=subtotal,
                tax_total=tax_total,
                total=total,
                amount_paid=Decimal("0"),
                balance_due=total,
                currency_code=customer.currency_code,
                payment_terms_days=customer.payment_terms_days,
                notes=invoice_data.notes,
                internal_notes=invoice_data.internal_notes,
                terms_and_conditions=invoice_data.terms_and_conditions,
                created_by=current_user.id,
            )
            db.add(invoice)
            await db.flush()

            # Create invoice items
            for item_data in calculated_items:
                invoice_item = InvoiceItem(invoice_id=invoice.id, **item_data)
                db.add(invoice_item)

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

    @staticmethod
    async def send_invoice(db: AsyncSession, invoice: Invoice) -> Invoice:
        """Mark invoice as sent"""

        if invoice.status not in ["DRAFT", "SENT"]:
            raise ValidationException(
                f"Cannot send invoice with status {invoice.status}"
            )

        if invoice.status == "DRAFT":
            invoice.status = "SENT"
            invoice.sent_at = datetime.utcnow()

        await db.commit()
        await db.refresh(invoice)

        return invoice

    @staticmethod
    async def void_invoice(
        db: AsyncSession, invoice: Invoice, void_request: InvoiceVoidRequest
    ) -> Invoice:
        """Void an invoice"""

        if invoice.status == "VOID":
            raise ValidationException("Invoice is already void")

        if invoice.status == "PAID":
            raise ValidationException(
                "Cannot void a paid invoice. Please void the payments first."
            )

        invoice.status = "VOID"
        invoice.voided_at = datetime.utcnow()
        invoice.void_reason = void_request.reason

        await db.commit()
        await db.refresh(invoice)

        return invoice
