from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv("SECRET_KEY")
    PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
    BASE_URL = os.getenv("BASE_URL")

    if not SECRET_KEY:
        raise ValueError("Missing SECRET_KEY in .env")

    if not PAYSTACK_SECRET_KEY:
        raise ValueError("Missing PAYSTACK_SECRET_KEY in .env")
