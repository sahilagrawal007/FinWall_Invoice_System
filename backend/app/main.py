"""
FinWall Invoice Platform - Main Application

This is the entry point for the FastAPI application.
Handles:
- App initialization
- Database auto-setup on startup
- Middleware configuration
- Exception handlers
- API routing
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.core.exceptions import (
    NotFoundException,
    UnauthorizedException,
    ValidationException,
    DuplicateException,
)
from app.api.v1 import api_router
from app.database import init_db, close_db
from app.middleware import RequestLoggingMiddleware
from app.utils.logger import log_startup, log_shutdown, log_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # === STARTUP ===
    log_startup(f"Starting {settings.APP_NAME}")
    log_startup(f"Debug mode: {settings.DEBUG}")
    log_startup(f"Database URL: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'configured'}")
    
    try:
        # Initialize database - creates tables if they don't exist
        await init_db()
        log_startup("Database initialized successfully")
    except Exception as e:
        log_error(
            user_email=None,
            error=f"Failed to initialize database: {str(e)}",
            exc_info=True
        )
        # Re-raise to prevent app from starting with broken DB
        raise
    
    log_startup("API Documentation: http://127.0.0.1:8000/docs")
    log_startup("Application startup complete!")
    
    yield  # Application runs here
    
    # === SHUTDOWN ===
    log_shutdown(f"Shutting down {settings.APP_NAME}")
    await close_db()
    log_shutdown("Application shutdown complete")


# Create FastAPI app with lifespan handler
app = FastAPI(
    title="FinWall Invoicing Platform API",
    description="FastAPI backend for invoicing and billing system",
    version="1.0.0",
    lifespan=lifespan,
)

# Add logging middleware (must be added before CORS middleware)
app.add_middleware(RequestLoggingMiddleware)

# Configure CORS
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


# ==================== Exception Handlers ====================

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


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler for unhandled errors"""
    log_error(
        user_email=getattr(request.state, 'user_email', None),
        error=str(exc),
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred"}
    )


# ==================== Root Endpoints ====================

@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "FinWall Invoicing Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
