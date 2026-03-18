# services/paystack.py
import requests
from flask import current_app

def headers():
    return {
        "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
        "Content-Type": "application/json"
    }

def initialize_transaction(email, amount):
    url = "https://api.paystack.co/transaction/initialize"

    payload = {
        "email": email,
        "amount": amount * 100,
        "callback_url": f"{current_app.config['BASE_URL']}/api/verify"
    }

    res = requests.post(url, json=payload, headers=headers())
    return res.json()


def verify_transaction(reference):
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    res = requests.get(url, headers=headers())
    return res.json()