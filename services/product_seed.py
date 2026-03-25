from decimal import Decimal

from extensions import db
from models import Product


DEFAULT_PRODUCTS = [
    {"name": "MTN 1GB", "network": "MTN", "data_amount": "1", "retail_price": "7.00"},
    {"name": "MTN 5GB", "network": "MTN", "data_amount": "5", "retail_price": "24.00"},
    {"name": "Telecel 2GB", "network": "Telecel", "data_amount": "2", "retail_price": "11.00"},
    {"name": "Telecel 10GB", "network": "Telecel", "data_amount": "10", "retail_price": "44.00"},
    {"name": "AirtelTigo 3GB", "network": "AirtelTigo", "data_amount": "3", "retail_price": "15.00"},
    {"name": "AirtelTigo 8GB", "network": "AirtelTigo", "data_amount": "8", "retail_price": "34.00"},
]


def seed_products():
    if Product.query.first():
        return

    for item in DEFAULT_PRODUCTS:
        db.session.add(
            Product(
                name=item["name"],
                network=item["network"],
                data_amount=item["data_amount"],
                retail_price=Decimal(item["retail_price"]),
                is_active=True,
            )
        )

    db.session.commit()
