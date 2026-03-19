# routes/payment.py
from flask import Blueprint, request, jsonify, current_app
from models import Payment
from extensions import db
from services.paystack import initialize_transaction, verify_transaction
from utils.security import verify_paystack_signature
from utils.decorators import admin_required
from flask import request, redirect, session, render_template

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
@admin_required
def get_payments():
    status = request.args.get("status")
    email = request.args.get("email")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = Payment.query

    if status:
        query = query.filter(Payment.status == status)

    if email:
        query = query.filter(Payment.email == email)

    if start_date and end_date:
        query = query.filter(
            Payment.created_at.between(start_date, end_date)
        )

    payments = query.order_by(Payment.id.desc()).all()

    return jsonify([p.to_dict() for p in payments])

@payment_bp.route("/dashboard")
@admin_required
def dashboard():

    return render_template("dashboard.html")


from werkzeug.security import check_password_hash
from models import Admin

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