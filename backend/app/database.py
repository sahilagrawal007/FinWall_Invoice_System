"""
Database Configuration for FinWall Invoice Platform

Uses MySQL (XAMPP) with async support via aiomysql.
Automatically creates/updates database schema on startup.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text, inspect
from app.config import settings
from app.utils.logger import log_startup, log_error, get_system_logger

# Create async engine for MySQL
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def get_db():
    """Dependency to get database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def check_database_connection() -> bool:
    """
    Check if the database connection is working.
    Returns True if connection successful, False otherwise.
    """
    logger = get_system_logger()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection verified successfully")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


async def init_db():
    """
    Initialize database - create all tables if they don't exist.
    This uses SQLAlchemy's create_all which:
    - Creates tables that don't exist
    - Adds new columns to existing tables (with some caveats)
    - Does NOT drop columns or tables
    - Preserves existing data
    """
    logger = get_system_logger()
    
    try:
        # First, check database connection
        if not await check_database_connection():
            raise Exception("Cannot connect to database. Please ensure MySQL is running.")
        
        log_startup("Initializing database schema...")
        
        # Import all models to ensure they're registered with Base
        from app.models import (
            User, Organization, OrganizationUser, Customer, Tax,
            Item, Invoice, InvoiceItem, Payment, Quote, QuoteItem, Expense
        )
        
        # Get existing tables for logging
        async with engine.connect() as conn:
            existing_tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        
        log_startup(f"Existing tables in database: {existing_tables or 'None'}")
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Get tables after creation
        async with engine.connect() as conn:
            new_tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        
        # Determine what was created
        created_tables = set(new_tables) - set(existing_tables)
        if created_tables:
            log_startup(f"Created new tables: {list(created_tables)}")
        else:
            log_startup("All tables already exist. Schema is up to date.")
        
        log_startup("Database initialization complete!", {
            "total_tables": len(new_tables),
            "tables": new_tables
        })
        
        return True
        
    except Exception as e:
        log_error(
            user_email=None,
            error=f"Database initialization failed: {str(e)}",
            exc_info=True
        )
        raise


async def close_db():
    """
    Close database connections gracefully.
    Called during application shutdown.
    """
    logger = get_system_logger()
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")
