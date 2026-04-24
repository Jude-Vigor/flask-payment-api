from decimal import Decimal

from extensions import db
from models import Product


DEFAULT_PRODUCTS = [
    {"name": "MTN 1GB", "network": "MTN", "data_amount": "1", "retail_price": "4.70"},
    {"name": "MTN 2GB", "network": "MTN", "data_amount": "2", "retail_price": "9.40"},
    {"name": "MTN 3GB", "network": "MTN", "data_amount": "3", "retail_price": "14.00"},
    {"name": "MTN 4GB", "network": "MTN", "data_amount": "4", "retail_price": "18.70"},
    {"name": "MTN 5GB", "network": "MTN", "data_amount": "5", "retail_price": "23.40"},
    {"name": "MTN 6GB", "network": "MTN", "data_amount": "6", "retail_price": "28.10"},
    {"name": "MTN 7GB", "network": "MTN", "data_amount": "7", "retail_price": "32.80"},
    {"name": "MTN 8GB", "network": "MTN", "data_amount": "8", "retail_price": "37.40"},
    {"name": "MTN 10GB", "network": "MTN", "data_amount": "10", "retail_price": "45.60"},
    {"name": "MTN 15GB", "network": "MTN", "data_amount": "15", "retail_price": "68.40"},
    {"name": "MTN 20GB", "network": "MTN", "data_amount": "20", "retail_price": "85.10"},
    {"name": "MTN 25GB", "network": "MTN", "data_amount": "25", "retail_price": "106.40"},
    {"name": "MTN 30GB", "network": "MTN", "data_amount": "30", "retail_price": "127.70"},
    {"name": "MTN 40GB", "network": "MTN", "data_amount": "40", "retail_price": "170.20"},
    {"name": "MTN 50GB", "network": "MTN", "data_amount": "50", "retail_price": "208.70"},
    {"name": "MTN 100GB", "network": "MTN", "data_amount": "100", "retail_price": "369.20"},
    {"name": "Telecel 10GB", "network": "Telecel", "data_amount": "10", "retail_price": "41.00"},
    {"name": "Telecel 15GB", "network": "Telecel", "data_amount": "15", "retail_price": "60.00"},
    {"name": "Telecel 20GB", "network": "Telecel", "data_amount": "20", "retail_price": "80.00"},
    {"name": "Telecel 25GB", "network": "Telecel", "data_amount": "25", "retail_price": "99.00"},
    {"name": "Telecel 30GB", "network": "Telecel", "data_amount": "30", "retail_price": "117.00"},
    {"name": "Telecel 35GB", "network": "Telecel", "data_amount": "35", "retail_price": "136.00"},
    {"name": "Telecel 40GB", "network": "Telecel", "data_amount": "40", "retail_price": "156.00"},
    {"name": "Telecel 45GB", "network": "Telecel", "data_amount": "45", "retail_price": "175.00"},
    {"name": "Telecel 50GB", "network": "Telecel", "data_amount": "50", "retail_price": "194.00"},
    {"name": "Telecel 100GB", "network": "Telecel", "data_amount": "100", "retail_price": "390.00"},
]


def seed_products():
    existing_products = {
        (product.network, product.data_amount): product
        for product in Product.query.all()
    }
    seeded_keys = set()

    for item in DEFAULT_PRODUCTS:
        key = (item["network"], item["data_amount"])
        seeded_keys.add(key)
        product = existing_products.get(key)

        if product is None:
            product = Product(
                name=item["name"],
                network=item["network"],
                data_amount=item["data_amount"],
            )
            db.session.add(product)

        product.name = item["name"]
        product.retail_price = Decimal(item["retail_price"])
        product.is_active = True

    for key, product in existing_products.items():
        if key not in seeded_keys:
            product.is_active = False

    db.session.commit()
