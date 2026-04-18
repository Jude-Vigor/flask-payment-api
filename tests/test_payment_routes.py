import hashlib
import hmac

from extensions import db
from models import Order, PaymentTransaction, Product


def test_get_products_returns_only_active_products(client, app):
    with app.app_context():
        db.session.add(
            Product(
                name="Inactive Product",
                network="MTN",
                data_amount="1",
                retail_price="4.70",
                is_active=False,
            )
        )
        db.session.add(
            Product(
                name="Active Product",
                network="MTN",
                data_amount="5",
                retail_price="23.40",
                is_active=True,
            )
        )
        db.session.commit()

    response = client.get("/api/products")

    assert response.status_code == 200
    payload = response.get_json()
    assert len(payload) == 1
    assert payload[0]["name"] == "Active Product"


def test_checkout_creates_order_and_payment_transaction(client, app, product, monkeypatch):
    def fake_initialize_transaction(email, amount, reference, metadata=None):
        return {
            "status": True,
            "data": {"authorization_url": "https://paystack.test/pay"},
        }

    monkeypatch.setattr("routes.payment.initialize_transaction", fake_initialize_transaction)

    response = client.post(
        "/api/checkout",
        json={
            "email": "buyer@example.com",
            "phone_number": "0501234567",
            "product_id": product.id,
        },
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "success"
    assert payload["authorization_url"] == "https://paystack.test/pay"

    with app.app_context():
        order = Order.query.filter_by(reference=payload["reference"]).first()
        transaction = PaymentTransaction.query.filter_by(reference=payload["reference"]).first()

        assert order is not None
        assert order.customer_email == "buyer@example.com"
        assert order.payment_status == "PENDING"
        assert transaction is not None
        assert transaction.status == "INITIALIZED"


def test_verify_payment_marks_order_paid_and_queues_fulfillment(client, app, product, monkeypatch):
    with app.app_context():
        order = Order(
            reference="ORD-VERIFY-001",
            customer_email="buyer@example.com",
            phone_number="0501234567",
            amount=product.retail_price,
            product_id=product.id,
            paystack_reference="ORD-VERIFY-001",
        )
        db.session.add(order)
        db.session.commit()

    def fake_verify_transaction(reference):
        return {
            "status": True,
            "data": {"status": "success"},
        }

    monkeypatch.setattr("routes.payment.verify_transaction", fake_verify_transaction)

    response = client.get(
        "/api/payments/verify?reference=ORD-VERIFY-001",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200

    with app.app_context():
        order = Order.query.filter_by(reference="ORD-VERIFY-001").first()
        assert order.payment_status == "PAID"
        assert order.fulfillment_status == "QUEUED"
        assert order.fulfillment_job is not None
        assert order.fulfillment_job.status == "PENDING"


def test_verify_payment_marks_order_failed_when_provider_rejects_payment(client, app, product, monkeypatch):
    with app.app_context():
        order = Order(
            reference="ORD-VERIFY-FAIL",
            customer_email="buyer@example.com",
            phone_number="0501234567",
            amount=product.retail_price,
            product_id=product.id,
            paystack_reference="ORD-VERIFY-FAIL",
        )
        db.session.add(order)
        db.session.commit()

    def fake_verify_transaction(reference):
        return {
            "status": False,
            "data": {"status": "failed"},
        }

    monkeypatch.setattr("routes.payment.verify_transaction", fake_verify_transaction)

    response = client.get(
        "/api/payments/verify?reference=ORD-VERIFY-FAIL",
        headers={"Accept": "application/json"},
    )

    assert response.status_code == 200

    with app.app_context():
        order = Order.query.filter_by(reference="ORD-VERIFY-FAIL").first()
        assert order.payment_status == "FAILED"
        assert order.fulfillment_job is None


def test_paystack_webhook_rejects_invalid_signature(client, paid_order):
    response = client.post(
        "/api/webhooks/paystack",
        json={
            "event": "charge.success",
            "data": {"reference": paid_order.reference},
        },
        headers={"x-paystack-signature": "invalid"},
    )

    assert response.status_code == 400
    assert response.get_data(as_text=True) == "Invalid signature"


def test_paystack_webhook_marks_order_paid_with_valid_signature(client, app, product):
    with app.app_context():
        order = Order(
            reference="ORD-WEBHOOK-001",
            customer_email="buyer@example.com",
            phone_number="0501234567",
            amount=product.retail_price,
            product_id=product.id,
            paystack_reference="ORD-WEBHOOK-001",
        )
        db.session.add(order)
        db.session.commit()

    body = b'{"event":"charge.success","data":{"reference":"ORD-WEBHOOK-001"}}'
    signature = hmac.new(
        b"test-paystack-secret",
        body,
        hashlib.sha512,
    ).hexdigest()

    response = client.post(
        "/api/webhooks/paystack",
        data=body,
        content_type="application/json",
        headers={"x-paystack-signature": signature},
    )

    assert response.status_code == 200

    with app.app_context():
        order = Order.query.filter_by(reference="ORD-WEBHOOK-001").first()
        assert order.payment_status == "PAID"
        assert order.fulfillment_status == "QUEUED"
        assert order.fulfillment_job is not None
