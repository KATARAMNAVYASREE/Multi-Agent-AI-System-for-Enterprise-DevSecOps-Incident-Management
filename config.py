"""
Configuration module for the Multi-Agent AI System.
Loads environment variables and provides centralized settings.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory paths
BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_BASE_DIR = BASE_DIR / "knowledge_base"
RUNBOOKS_DIR = KNOWLEDGE_BASE_DIR / "runbooks"
HISTORICAL_INCIDENTS_DIR = KNOWLEDGE_BASE_DIR / "historical_incidents"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
SQLITE_DB_PATH = BASE_DIR / "incident_management.db"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- Application ---
    APP_NAME: str = "Multi-Agent DevSecOps Incident Management"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- Google Gemini API ---
    GOOGLE_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_MODEL_ADVANCED: str = "gemini-2.0-flash"
    GEMINI_TEMPERATURE: float = 0.3
    GEMINI_MAX_TOKENS: int = 4096

    # --- Agent Settings ---
    AGENT_MAX_ITERATIONS: int = 6
    AGENT_VERBOSE: bool = True
    AGENT_MEMORY: bool = True

    # --- RAG Settings ---
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    RAG_TOP_K: int = 5

    # --- Database ---
    DATABASE_URL: str = f"sqlite+aiosqlite:///{SQLITE_DB_PATH}"

    # --- WebSocket ---
    WS_HEARTBEAT_INTERVAL: int = 30

    # --- Simulator ---
    SIMULATOR_TICK_INTERVAL: float = 2.0  # seconds between metric updates
    SIMULATOR_INCIDENT_PROBABILITY: float = 0.05  # probability of incident per tick

    # --- CORS ---
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton settings instance
settings = Settings()
