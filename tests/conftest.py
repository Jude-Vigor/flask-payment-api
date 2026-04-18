import os
from decimal import Decimal

import pytest


os.environ["SECRET_KEY"] = "test-secret"
os.environ["PAYSTACK_SECRET_KEY"] = "test-paystack-secret"
os.environ["BASE_URL"] = "http://localhost:5000"
os.environ["DATABASE_URL"] = "sqlite:///test_app.db"
os.environ["AUTO_CREATE_TABLES"] = "false"
os.environ["INSTANTDATAGH_API_KEY"] = "test-vendor-key"
os.environ["INSTANTDATAGH_BASE_URL"] = "https://example.com"

from app import create_app
from extensions import db
from models import Admin, Order, Product
from werkzeug.security import generate_password_hash


@pytest.fixture()
def app():
    app = create_app()
    app.config.update(TESTING=True)

    with app.app_context():
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def product(app):
    with app.app_context():
        product = Product(
            name="MTN 5GB",
            network="MTN",
            data_amount="5",
            retail_price=Decimal("23.40"),
            is_active=True,
        )
        db.session.add(product)
        db.session.commit()
        db.session.refresh(product)
        return product


@pytest.fixture()
def paid_order(app, product):
    with app.app_context():
        order = Order(
            reference="ORD-PAID-001",
            customer_email="buyer@example.com",
            phone_number="0501234567",
            amount=product.retail_price,
            product_id=product.id,
            payment_status="PAID",
            fulfillment_status="PENDING",
            paystack_reference="ORD-PAID-001",
        )
        db.session.add(order)
        db.session.commit()
        db.session.refresh(order)
        return order


@pytest.fixture()
def admin_user(app):
    with app.app_context():
        admin = Admin(
            email="admin@example.com",
            password_hash=generate_password_hash("password123"),
        )
        db.session.add(admin)
        db.session.commit()
        db.session.refresh(admin)
        return admin
