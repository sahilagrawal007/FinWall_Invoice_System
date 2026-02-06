from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.core.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
    DuplicateException,
)
from app.api.v1 import api_router

# Create FastAPI app
app = FastAPI(
    title="Invoicing Platform API",
    description="FastAPI backend for invoicing and billing system",
    version="1.0.0",
)

# Configure CORS - UPDATED
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost",
        "http://127.0.0.1",
        "null",  # For file:// protocol
        "*",  # Allow all origins (for development only)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


# Exception handlers
@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(DuplicateException)
async def duplicate_exception_handler(request: Request, exc: DuplicateException):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Invoicing Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Startup event
@app.on_event("startup")
async def startup_event():
    print(f"Starting {settings.APP_NAME}")
    print("API Documentation: http://127.0.0.1:8000/docs")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    print(f"👋 Shutting down {settings.APP_NAME}")
