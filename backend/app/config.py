"""Application configuration - loads environment variables"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings from environment variables"""

    # Google Gemini
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # Elasticsearch
    ELASTIC_URL: str = os.getenv("ELASTIC_URL", "http://localhost:9200")
    ELASTIC_USERNAME: str = os.getenv("ELASTIC_USERNAME", "elastic")
    ELASTIC_PASSWORD: str = os.getenv("ELASTIC_PASSWORD", "changeme")

    # Qdrant
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")

    # App
    APP_ENV: str = os.getenv("APP_ENV", "development")
    FRONTEND_DIST: str = os.getenv(
        "FRONTEND_DIST",
        os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"),
    )
    IMAGES_DIR: str = os.path.join(
        os.path.dirname(__file__), "..", "database", "images"
    )


settings = Settings()
