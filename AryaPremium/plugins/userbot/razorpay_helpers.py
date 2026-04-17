import razorpay
import requests
import asyncio
from config import Config

async def _create_rzp_link(amount_inr, description, txnid, name, email="none@telegram.user", phone="9876543210"):
    key = getattr(Config, 'RAZORPAY_KEY', '')
    secret = getattr(Config, 'RAZORPAY_SECRET', '')
    if not key or not secret:
        return None, None

    def do_create():
        client = razorpay.Client(auth=(key, secret))
        data = {
            "amount": int(float(amount_inr) * 100),
            "currency": "INR",
            "accept_partial": False,
            "description": description[:100],
            "customer": {
                "name": name or "User",
                "email": email,
                "contact": phone
            },
            "notify": {"sms": False, "email": False},
            "reminder_enable": False,
            "reference_id": txnid
        }
        return client.payment_link.create(data)

    try:
        res = await asyncio.to_thread(do_create)
        return res.get("short_url"), res.get("id")
    except Exception as e:
        print(f"Razorpay link error: {e}")
        return None, str(e)

async def _check_rzp_status(pl_id):
    key = getattr(Config, 'RAZORPAY_KEY', '')
    secret = getattr(Config, 'RAZORPAY_SECRET', '')
    if not key or not secret:
        return "failed"

    def do_fetch():
        client = razorpay.Client(auth=(key, secret))
        return client.payment_link.fetch(pl_id)

    try:
        res = await asyncio.to_thread(do_fetch)
        status = res.get("status")
        if status == "paid":
            return "paid"
        return status
    except Exception as e:
        print(f"Razorpay check error: {e}")
        return "failed"
