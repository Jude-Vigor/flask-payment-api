import json
from datetime import datetime
from decimal import Decimal

from extensions import db


def _json_loads(value):
    if not value:
        return None

    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return None


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    network = db.Column(db.String(30), nullable=False)
    data_amount = db.Column(db.String(10), nullable=False)
    retail_price = db.Column(db.Numeric(10, 2), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    orders = db.relationship("Order", back_populates="product", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "network": self.network,
            "data_amount": self.data_amount,
            "retail_price": float(self.retail_price or Decimal("0.00")),
            "is_active": self.is_active,
        }


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(40), unique=True, nullable=False)
    customer_email = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(10), default="GHS", nullable=False)
    payment_status = db.Column(db.String(20), default="PENDING", nullable=False)
    fulfillment_status = db.Column(db.String(20), default="PENDING", nullable=False)
    vendor_order_id = db.Column(db.String(120), nullable=True)
    vendor_status = db.Column(db.String(50), nullable=True)
    vendor_response = db.Column(db.Text, nullable=True)
    paystack_reference = db.Column(db.String(120), unique=True, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    fulfilled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product = db.relationship("Product", back_populates="orders")

    payment_transactions = db.relationship(
        "PaymentTransaction",
        back_populates="order",
        lazy=True,
        cascade="all, delete-orphan",
    )
    fulfillment_attempts = db.relationship(
        "FulfillmentAttempt",
        back_populates="order",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "reference": self.reference,
            "customer_email": self.customer_email,
            "phone_number": self.phone_number,
            "amount": float(self.amount or Decimal("0.00")),
            "currency": self.currency,
            "payment_status": self.payment_status,
            "fulfillment_status": self.fulfillment_status,
            "vendor_order_id": self.vendor_order_id,
            "vendor_status": self.vendor_status,
            "vendor_response": _json_loads(self.vendor_response),
            "paystack_reference": self.paystack_reference,
            "paid_at": self.paid_at.isoformat() if self.paid_at else None,
            "fulfilled_at": self.fulfilled_at.isoformat() if self.fulfilled_at else None,
            "created_at": self.created_at.isoformat(),
            "product": self.product.to_dict() if self.product else None,
        }

    def to_dashboard_dict(self):
        return {
            "id": self.id,
            "email": self.customer_email,
            "amount": float(self.amount or Decimal("0.00")),
            "reference": self.reference,
            "status": self.payment_status,
            "fulfillment_status": self.fulfillment_status,
            "created_at": self.created_at.isoformat(),
        }


class PaymentTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(30), default="PAYSTACK", nullable=False)
    reference = db.Column(db.String(120), unique=True, nullable=False)
    status = db.Column(db.String(20), default="INITIALIZED", nullable=False)
    provider_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    order = db.relationship("Order", back_populates="payment_transactions")


class FulfillmentAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status = db.Column(db.String(20), default="PENDING", nullable=False)
    request_payload = db.Column(db.Text, nullable=True)
    response_payload = db.Column(db.Text, nullable=True)
    error_message = db.Column(db.String(255), nullable=True)
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    order = db.relationship("Order", back_populates="fulfillment_attempts")


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
