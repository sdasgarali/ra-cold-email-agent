"""Core configuration settings loaded from environment variables."""
from functools import lru_cache
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Core
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "Exzelon RA Cold-Email Automation"
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Data Storage Mode
    DATA_STORAGE: Literal["database", "files"] = "database"
    JOB_REQUIREMENTS_PATH: str = "./data/Job_requirements.xlsx"
    EXPORT_PATH: str = "./data/exports"

    # MySQL Database
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "ra_agent"
    DB_USER: str = "ra_user"
    DB_PASSWORD: str = "change_me"

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Contact Discovery Providers
    CONTACT_PROVIDER: Literal["apollo", "seamless", "mock"] = "mock"
    APOLLO_API_KEY: str = ""
    SEAMLESS_API_KEY: str = ""

    # Email Validation Providers
    EMAIL_VALIDATION_PROVIDER: Literal["neverbounce", "zerobounce", "hunter", "clearout", "mock"] = "mock"
    NEVERBOUNCE_API_KEY: str = ""
    ZEROBOUNCE_API_KEY: str = ""
    HUNTER_API_KEY: str = ""
    CLEAROUT_API_KEY: str = ""

    # Email Sending
    EMAIL_SEND_MODE: Literal["mailmerge", "smtp", "m365", "gmail", "api"] = "mailmerge"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Business Rules
    DAILY_SEND_LIMIT: int = 30
    COOLDOWN_DAYS: int = 10
    MAX_CONTACTS_PER_COMPANY_PER_JOB: int = 4
    MIN_SALARY_THRESHOLD: int = 40000

    # Industries (Non-IT only)
    TARGET_INDUSTRIES: list[str] = [
        "Healthcare", "Manufacturing", "Logistics", "Retail", "BFSI",
        "Education", "Engineering", "Automotive", "Construction", "Energy",
        "Oil & Gas", "Food & Beverage", "Hospitality", "Real Estate",
        "Legal", "Insurance", "Financial Services", "Industrial", "Skilled Trades"
    ]

    # Excluded patterns
    EXCLUDE_IT_KEYWORDS: list[str] = [
        "software", "developer", "engineer", "IT", "technology",
        "programmer", "coding", "tech", "data scientist", "devops"
    ]
    EXCLUDE_STAFFING_KEYWORDS: list[str] = [
        "staffing", "recruiting", "recruitment agency", "talent acquisition agency"
    ]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
