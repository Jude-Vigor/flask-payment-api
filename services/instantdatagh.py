import requests
from flask import current_app


def _headers():
    api_key = current_app.config.get("INSTANTDATAGH_API_KEY")
    if not api_key:
        raise RuntimeError("Missing INSTANTDATAGH_API_KEY in environment configuration.")

    return {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }


def create_order(network, phone_number, data_amount):
    url = f"{current_app.config['INSTANTDATAGH_BASE_URL'].rstrip('/')}/orders"
    payload = {
        "network": network,
        "phone_number": phone_number,
        "data_amount": str(data_amount),
    }

    response = requests.post(url, json=payload, headers=_headers(), timeout=30)
    return payload, response.json()
