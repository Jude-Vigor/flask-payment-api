# routes/payment.py
from flask import Blueprint, request, jsonify, current_app
from models import Payment
from extensions import db
from services.paystack import initialize_transaction, verify_transaction
from utils.security import verify_paystack_signature

payment_bp = Blueprint("payment", __name__)


@payment_bp.route("/pay", methods=["POST"])
def pay():
    data = request.json
    email = data["email"]
    amount = data["amount"]

    response = initialize_transaction(email, amount)

    if not response["status"]:
        return jsonify(response), 400

    reference = response["data"]["reference"]

    payment = Payment(
        email=email,
        amount=amount,
        reference=reference
    )

    db.session.add(payment)
    db.session.commit()

    return jsonify({
        "authorization_url": response["data"]["authorization_url"],
        "reference": reference
    })


@payment_bp.route("/verify")
def verify():
    reference = request.args.get("reference")

    res = verify_transaction(reference)

    if res["data"]["status"] == "success":
        payment = Payment.query.filter_by(reference=reference).first()

        if payment:
            payment.status = "SUCCESS"
            db.session.commit()

    return jsonify(res)


@payment_bp.route("/webhook", methods=["POST"])
def webhook():
    secret = current_app.config["PAYSTACK_SECRET_KEY"]

    if not verify_paystack_signature(request, secret):
        return "Invalid signature", 400

    event = request.json

    if event["event"] == "charge.success":
        reference = event["data"]["reference"]

        payment = Payment.query.filter_by(reference=reference).first()

        if payment and payment.status != "SUCCESS":
            payment.status = "SUCCESS"
            db.session.commit()

    return "", 200

@payment_bp.route("/payments", methods=["GET"])
def get_payments():
    payments = Payment.query.all()
    # payments = Payment.query.filter_by(status="SUCCESS").all()
    result = []
    for p in payments:
        result.append({
            "id": p.id,
            "email": p.email,
            "amount": p.amount,
            "reference": p.reference,
            "status": p.status,
            "created_at": p.created_at
        })

    return jsonify(result)