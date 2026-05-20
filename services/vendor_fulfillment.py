import requests
from flask import current_app


def _headers():
    api_key = current_app.config.get("VENDOR_API_KEY")
    if not api_key:
        raise RuntimeError("Missing VENDOR_API_KEY in environment configuration.")

    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }


def create_order(network, phone_number, data_amount):
    base_url = current_app.config.get("VENDOR_BASE_URL")
    if not base_url:
        raise RuntimeError("Missing VENDOR_BASE_URL in environment configuration.")

    url = f"{base_url.rstrip('/')}/orders"
    payload = {
        "network": network,
        "phone_number": phone_number,
        "data_amount": str(data_amount),
    }

    response = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return payload, response.json()
