from dotenv import load_dotenv
import os

load_dotenv()


def _database_uri():
    database_url = os.getenv("DATABASE_URL", "sqlite:///app.db")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return database_url


class Config:
    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    AUTO_CREATE_TABLES = os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true"

    SECRET_KEY = os.getenv("SECRET_KEY")
    PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
    BASE_URL = os.getenv("BASE_URL")
    INSTANTDATAGH_BASE_URL = os.getenv("INSTANTDATAGH_BASE_URL", "https://instantdatagh.com/api.php")
    INSTANTDATAGH_API_KEY = os.getenv("INSTANTDATAGH_API_KEY")

    if not SECRET_KEY:
        raise ValueError("Missing SECRET_KEY in .env")

    if not PAYSTACK_SECRET_KEY:
        raise ValueError("Missing PAYSTACK_SECRET_KEY in .env")

    if not BASE_URL:
        raise ValueError("Missing BASE_URL in .env")
