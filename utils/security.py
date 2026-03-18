# utils/security.py
import hmac
import hashlib

def verify_paystack_signature(request, secret):
    signature = request.headers.get("x-paystack-signature")
    body = request.data

    computed = hmac.new(
        secret.encode(),
        body,
        hashlib.sha512
    ).hexdigest()

    return computed == signature