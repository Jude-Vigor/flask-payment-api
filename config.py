from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///app.db")
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
