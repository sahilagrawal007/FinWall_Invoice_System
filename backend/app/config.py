from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "FinWall Technologies Invoicing Platform"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:8000"

    # Indian Market Settings
    DEFAULT_CURRENCY: str = "INR"
    CURRENCY_SYMBOL: str = "₹"
    TIMEZONE: str = "Asia/Kolkata"
    FISCAL_YEAR_END_MONTH: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_allowed_origins(self) -> List[str]:
        """Convert comma-separated origins to list"""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

settings = Settings()