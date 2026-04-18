import hashlib
import hmac
from types import SimpleNamespace

from extensions import db
from models import Product
from services.product_seed import seed_products
from utils.security import verify_paystack_signature


def test_seed_products_creates_defaults_and_deactivates_old_products(app):
    with app.app_context():
        db.session.add(
            Product(
                name="Old Product",
                network="Telecel",
                data_amount="999",
                retail_price="99.99",
                is_active=True,
            )
        )
        db.session.commit()

        seed_products()

        old_product = Product.query.filter_by(data_amount="999").first()
        seeded_product = Product.query.filter_by(network="MTN", data_amount="5").first()

        assert seeded_product is not None
        assert seeded_product.is_active is True
        assert old_product.is_active is False


def test_verify_paystack_signature_returns_true_for_valid_signature():
    body = b'{"event":"charge.success"}'
    secret = "test-secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()
    request = SimpleNamespace(
        data=body,
        headers={"x-paystack-signature": signature},
    )

    assert verify_paystack_signature(request, secret) is True


def test_verify_paystack_signature_returns_false_for_invalid_signature():
    request = SimpleNamespace(
        data=b'{"event":"charge.success"}',
        headers={"x-paystack-signature": "invalid"},
    )

    assert verify_paystack_signature(request, "test-secret") is False
