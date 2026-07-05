"""
PMS Engine Backend Configuration.
Uses environment variables with sensible defaults for local development.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    csv_path: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "final_institutional_scanner.csv",
    )

    # API server configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Application metadata
    app_name: str = "PMS Engine"
    app_version: str = "1.0.0"

    # Future: Database connection
    database_url: str = ""

    # Future: Authentication
    jwt_secret: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
