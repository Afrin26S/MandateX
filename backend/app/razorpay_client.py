"""
Thin wrapper around the Razorpay SDK. Keeps all Razorpay-specific code in
one place so main.py doesn't need to know SDK details.
"""

import os
import time
from dotenv import load_dotenv
import razorpay

load_dotenv()

_client = None


def get_client():
    global _client
    if _client is None:
        key_id = os.getenv("RAZORPAY_KEY_ID")
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        if not key_id or not key_secret:
            raise RuntimeError(
                "Razorpay keys not found. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to your .env file."
            )
        _client = razorpay.Client(auth=(key_id, key_secret))
    return _client


def create_test_order(amount_rupees: int, receipt: str, retries: int = 1):
    """Razorpay wants amount in paise (1 rupee = 100 paise), not rupees.

    Retries once on a transient network error (e.g. a dropped keep-alive
    connection) before giving up, so a one-off hiccup doesn't surface as
    a failed demo.
    """
    client = get_client()
    order_data = {
        "amount": amount_rupees * 100,
        "currency": "INR",
        "receipt": receipt,
        "payment_capture": 1,
    }
    last_error = None
    for attempt in range(retries + 1):
        try:
            return client.order.create(order_data)
        except Exception as e:
            last_error = e
            if attempt < retries:
                time.sleep(1)
                continue
    raise last_error