"""
Configuration management using Pydantic Settings.

Loads configuration from environment variables with sensible defaults.
Supports both SQLite (development) and PostgreSQL (production).
"""

from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Environment variables:
    - DATABASE_URL: Database connection string
    - CORS_ORIGINS: Comma-separated list of allowed origins
    - DEBUG: Enable debug mode
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    APP_NAME: str = "Quant Lab API"
    APP_VERSION: str = "0.1.0"
    debug: bool = False

    # Database
    database_type: str = "sqlite"
    database_url: str = "sqlite:///./quant_lab.db"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "quantlab"
    postgres_password: str = "quantlab"
    postgres_db: str = "quantlab"

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Data paths
    csv_data_dir: str = "./data"
    fundamentals_file: str = "./data/fundamentals.csv"

    def __init__(self, **kwargs):
        """Initialize settings and compute database URL if using PostgreSQL."""
        super().__init__(**kwargs)

        # Override database_url if using PostgreSQL
        if self.database_type == "postgresql":
            self.database_url = (
                f"postgresql://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
    
    @property
    def is_sqlite(self) -> bool:
        """Check if using SQLite database."""
        return self.database_url.startswith("sqlite")
    
    @property
    def is_postgresql(self) -> bool:
        """Check if using PostgreSQL database."""
        return self.database_url.startswith("postgresql")


# Global settings instance
settings = Settings()
