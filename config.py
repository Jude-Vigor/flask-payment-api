from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
    BASE_URL = os.getenv("BASE_URL")

    if not PAYSTACK_SECRET_KEY:
        raise ValueError("Missing PAYSTACK_SECRET_KEY in .env")