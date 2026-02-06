from fastapi import APIRouter
from app.api.v1 import (
    auth,
    customers,
    taxes,
    items,
    invoices,
    payments,
    quotes,
    expenses,
    reports,
)

api_router = APIRouter(prefix="/v1")

# Include all route modules
api_router.include_router(auth.router)
api_router.include_router(customers.router)
api_router.include_router(taxes.router)
api_router.include_router(items.router)
api_router.include_router(invoices.router)
api_router.include_router(payments.router)
api_router.include_router(quotes.router)
api_router.include_router(expenses.router)
api_router.include_router(reports.router)
