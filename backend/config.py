# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)


def _build_database_uri() -> str:
    raw = os.getenv("DATABASE_URL")
    if not raw:
        return f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}"

    # Normalize relative sqlite paths to absolute to avoid runtime resolution issues.
    if raw.startswith("sqlite:///") and not raw.startswith("sqlite:////"):
        sqlite_path = raw.replace("sqlite:///", "", 1)
        if not os.path.isabs(sqlite_path):
            sqlite_path = os.path.abspath(os.path.join(PROJECT_ROOT, sqlite_path))
        return f"sqlite:///{sqlite_path}"

    return raw


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-this-jwt-secret-in-production")
    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@12345")

    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", 5000))
    USE_ML = os.getenv("USE_ML", "false").lower() == "true"
    # Path to intents relative to backend package
    BASE_DIR = BASE_DIR
    INTENTS_PATH = os.path.join(BASE_DIR, "nlp", "intents.json")
    # ml model paths (optional)
    ML_MODEL_PATH = os.path.join(PROJECT_ROOT, "ml", "model", "chatbot_model.pth")
    ML_DIMENSIONS_PATH = os.path.join(PROJECT_ROOT, "ml", "model", "dimensions.json")
