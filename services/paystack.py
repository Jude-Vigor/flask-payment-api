from decimal import Decimal, ROUND_HALF_UP

import requests
from flask import current_app


def _headers():
    return {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json",
    }


def _to_subunit_amount(amount):
    decimal_amount = Decimal(str(amount))
    return int((decimal_amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def initialize_transaction(email, amount, reference, metadata=None):
    url = "https://api.paystack.co/transaction/initialize"
    payload = {
        "email": email,
        "amount": _to_subunit_amount(amount),
        "reference": reference,
        "callback_url": f"{current_app.config['BASE_URL']}/api/payments/verify",
    }

    if metadata:
        payload["metadata"] = metadata

    response = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return response.json()


def verify_transaction(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    response = requests.get(url, headers=_headers(), timeout=30)
    return response.json()
