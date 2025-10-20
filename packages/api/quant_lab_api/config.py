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
    database_url: str = "sqlite:///./quant_lab.db"
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def CORS_ORIGINS(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    # Data paths (default to Docker paths, can be overridden with env vars)
    csv_data_dir: str = "/app/data"
    fundamentals_file: str = "/app/data/fundamentals.csv"
    
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
