import json
import re
from datetime import datetime
from secrets import token_hex

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash

from extensions import db
from models import Admin, FulfillmentAttempt, Order, PaymentTransaction, Product
from services.instantdatagh import create_order as create_vendor_order
from services.paystack import initialize_transaction, verify_transaction
from utils.decorators import admin_required
from utils.security import verify_paystack_signature

payment_bp = Blueprint("payment", __name__)

PHONE_PATTERN = re.compile(r"^0\d{9}$")
VALID_NETWORKS = {"MTN", "AirtelTigo", "Telecel"}


def _json_error(message, status_code=400):
    return jsonify({"status": "error", "message": message}), status_code


def _generate_reference():
    return f"ORD-{token_hex(8).upper()}"


def _serialize(value):
    return json.dumps(value) if value is not None else None


def _validate_checkout_payload(payload):
    if not isinstance(payload, dict):
        return "Invalid JSON payload."

    if not payload.get("email"):
        return "Email is required."

    if not payload.get("phone_number"):
        return "phone_number is required."

    if not PHONE_PATTERN.match(payload["phone_number"]):
        return "phone_number must use the Ghana format 0XXXXXXXXX."

    if not payload.get("product_id"):
        return "product_id is required."

    return None


def _get_or_create_payment_transaction(order):
    transaction = PaymentTransaction.query.filter_by(reference=order.reference).first()
    if transaction:
        return transaction

    transaction = PaymentTransaction(
        order=order,
        reference=order.reference,
        status="INITIALIZED",
    )
    db.session.add(transaction)
    return transaction


def _mark_payment_paid(order, provider_response):
    order.payment_status = "PAID"
    order.paid_at = order.paid_at or datetime.utcnow()
    order.paystack_reference = order.reference

    transaction = _get_or_create_payment_transaction(order)
    transaction.status = "SUCCESS"
    transaction.provider_response = _serialize(provider_response)


def _mark_payment_failed(order, provider_response):
    order.payment_status = "FAILED"

    transaction = _get_or_create_payment_transaction(order)
    transaction.status = "FAILED"
    transaction.provider_response = _serialize(provider_response)


def _submit_fulfillment(order):
    if order.fulfillment_status in {"PROCESSING", "DELIVERED"}:
        return

    if order.product.network not in VALID_NETWORKS:
        raise ValueError("Unsupported network configured for product.")

    request_payload = {
        "network": order.product.network,
        "phone_number": order.phone_number,
        "data_amount": order.product.data_amount,
    }

    attempt = FulfillmentAttempt(
        order=order,
        status="PENDING",
        request_payload=_serialize(request_payload),
    )
    db.session.add(attempt)
    db.session.flush()

    try:
        _, response_payload = create_vendor_order(
            network=order.product.network,
            phone_number=order.phone_number,
            data_amount=order.product.data_amount,
        )
    except Exception as exc:
        attempt.status = "FAILED"
        attempt.error_message = str(exc)
        order.fulfillment_status = "FAILED"
        db.session.commit()
        raise

    attempt.response_payload = _serialize(response_payload)

    if response_payload.get("status") == "success":
        vendor_data = response_payload.get("data") or {}
        attempt.status = "ACCEPTED"
        order.fulfillment_status = "PROCESSING"
        order.vendor_order_id = vendor_data.get("order_id")
        order.vendor_status = vendor_data.get("status")
        order.vendor_response = _serialize(response_payload)
    else:
        attempt.status = "FAILED"
        attempt.error_message = response_payload.get("message", "Vendor fulfillment failed.")
        order.fulfillment_status = "FAILED"
        order.vendor_response = _serialize(response_payload)

    db.session.commit()


@payment_bp.route("/products", methods=["GET"])
def get_products():
    products = (
        Product.query.filter_by(is_active=True)
        .order_by(Product.network.asc(), Product.data_amount.asc())
        .all()
    )
    return jsonify([product.to_dict() for product in products])


@payment_bp.route("/checkout", methods=["POST"])
def checkout():
    payload = request.get_json(silent=True) or {}
    validation_error = _validate_checkout_payload(payload)
    if validation_error:
        return _json_error(validation_error)

    try:
        product_id = int(payload["product_id"])
    except (TypeError, ValueError):
        return _json_error("product_id must be an integer.")

    product = Product.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        return _json_error("Selected product is unavailable.", 404)

    reference = _generate_reference()
    order = Order(
        reference=reference,
        customer_email=payload["email"].strip(),
        phone_number=payload["phone_number"].strip(),
        amount=product.retail_price,
        product=product,
        paystack_reference=reference,
    )
    db.session.add(order)
    db.session.flush()

    payment_response = initialize_transaction(
        email=order.customer_email,
        amount=order.amount,
        reference=reference,
        metadata={
            "order_reference": reference,
            "product_id": product.id,
            "phone_number": order.phone_number,
        },
    )

    transaction = _get_or_create_payment_transaction(order)
    transaction.provider_response = _serialize(payment_response)

    if not payment_response.get("status"):
        transaction.status = "FAILED"
        order.payment_status = "FAILED"
        db.session.commit()
        return jsonify(payment_response), 400

    db.session.commit()

    return jsonify(
        {
            "status": "success",
            "message": "Checkout initialized successfully.",
            "reference": reference,
            "authorization_url": payment_response["data"]["authorization_url"],
            "order": order.to_dict(),
        }
    )


@payment_bp.route("/payments/verify", methods=["GET"])
def verify_payment():
    reference = request.args.get("reference")
    if not reference:
        return _json_error("reference is required.")

    order = Order.query.filter_by(reference=reference).first()
    if not order:
        return _json_error("Order not found.", 404)

    verification_response = verify_transaction(reference)
    verified_data = verification_response.get("data") or {}

    if verification_response.get("status") and verified_data.get("status") == "success":
        if order.payment_status != "PAID":
            _mark_payment_paid(order, verification_response)
            db.session.commit()

        if order.fulfillment_status == "PENDING":
            try:
                _submit_fulfillment(order)
            except Exception as exc:
                current_app.logger.exception("InstantDataGH fulfillment failed for %s", reference)
                return (
                    jsonify(
                        {
                            "status": "partial_success",
                            "message": "Payment verified but fulfillment submission failed.",
                            "error": str(exc),
                            "order": order.to_dict(),
                        }
                    ),
                    502,
                )
    else:
        _mark_payment_failed(order, verification_response)
        db.session.commit()

    return jsonify(
        {
            "status": "success",
            "payment_verification": verification_response,
            "order": order.to_dict(),
        }
    )


@payment_bp.route("/webhooks/paystack", methods=["POST"])
def paystack_webhook():
    secret = current_app.config["PAYSTACK_SECRET_KEY"]

    if not verify_paystack_signature(request, secret):
        return "Invalid signature", 400

    event = request.get_json(silent=True) or {}
    if event.get("event") != "charge.success":
        return "", 200

    data = event.get("data") or {}
    reference = data.get("reference")
    if not reference:
        return "", 200

    order = Order.query.filter_by(reference=reference).first()
    if not order:
        return "", 200

    if order.payment_status != "PAID":
        _mark_payment_paid(order, event)
        db.session.commit()

    if order.fulfillment_status == "PENDING":
        try:
            _submit_fulfillment(order)
        except Exception:
            current_app.logger.exception("InstantDataGH fulfillment failed for %s", reference)
            return "", 500

    return "", 200


@payment_bp.route("/orders/<reference>", methods=["GET"])
def get_order(reference):
    order = Order.query.filter_by(reference=reference).first()
    if not order:
        return _json_error("Order not found.", 404)

    return jsonify(order.to_dict())


@payment_bp.route("/payments", methods=["GET"])
@admin_required
def get_payments():
    status = request.args.get("status")
    email = request.args.get("email")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Order.query

    if status:
        query = query.filter(Order.payment_status == status)

    if email:
        query = query.filter(Order.customer_email == email)

    if start_date and end_date:
        query = query.filter(Order.created_at.between(start_date, end_date))

    orders = query.order_by(Order.id.desc()).all()
    return jsonify([order.to_dashboard_dict() for order in orders])


@payment_bp.route("/dashboard")
@admin_required
def dashboard():
    return render_template("dashboard.html")


@payment_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        admin = Admin.query.filter_by(email=email).first()

        if admin and check_password_hash(admin.password_hash, password):
            session["admin"] = admin.id
            return redirect("/api/dashboard")

        return "Invalid credentials"

    return render_template("login.html")


@payment_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/api/login")
