import hashlib
import json
import requests
import asyncio
from config import Config
import time

async def _create_easebuzz_link(amount_inr, description, txnid, name, email="none@telegram.user", phone="9876543210"):
    key = getattr(Config, 'EASEBUZZ_KEY', '')
    salt = getattr(Config, 'EASEBUZZ_SALT', '')
    env = getattr(Config, 'EASEBUZZ_ENV', 'test')  # 'test' or 'prod'
    if not key or not salt:
        return None, None

    amount_str = f"{float(amount_inr):.2f}"
    data = {
        "key": key,
        "txnid": txnid,
        "amount": amount_str,
        "productinfo": description[:100],
        "firstname": name[:50] or "User",
        "email": email,
        "phone": phone,
        "surl": "https://sliceurl.app",
        "furl": "https://sliceurl.app",
    }
    
    hash_seq = f"{key}|{txnid}|{amount_str}|{data['productinfo']}|{data['firstname']}|{email}|||||||||||{salt}"
    data["hash"] = hashlib.sha512(hash_seq.encode('utf-8')).hexdigest()

    base_url = "https://pay.easebuzz.in" if env == "prod" else "https://testpay.easebuzz.in"
    
    def do_create():
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        return requests.post(f"{base_url}/payment/initiateLink", data=data, headers=headers).json()
        
    try:
        res = await asyncio.to_thread(do_create)
        if res.get("status") == 1:
            access_key = res.get("data")
            payment_url = f"{base_url}/pay/{access_key}"
            return payment_url, txnid
        else:
            print(f"Easebuzz Link Error: {res}")
            return None, str(res)
    except Exception as e:
        print(f"Easebuzz request error: {e}")
        return None, str(e)


async def _check_easebuzz_status(txnid, amount_inr, email="none@telegram.user", phone="9876543210"):
    key = getattr(Config, 'EASEBUZZ_KEY', '')
    salt = getattr(Config, 'EASEBUZZ_SALT', '')
    env = getattr(Config, 'EASEBUZZ_ENV', 'test')
    if not key or not salt:
        return "failed"

    amount_str = f"{float(amount_inr):.2f}"
    hash_seq = f"{key}|{txnid}|{amount_str}|{email}|{phone}|{salt}"
    hash_val = hashlib.sha512(hash_seq.encode('utf-8')).hexdigest()

    data = {
        "key": key,
        "txnid": txnid,
        "amount": amount_str,
        "email": email,
        "phone": phone,
        "hash": hash_val
    }
    
    # The transaction retrieve API domain
    status_url = "https://dashboard.easebuzz.in/transaction/v1/retrieve" if env == "prod" else "https://testdashboard.easebuzz.in/transaction/v1/retrieve"

    def do_fetch():
        headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
        return requests.post(status_url, data=data, headers=headers).json()
        
    try:
        res = await asyncio.to_thread(do_fetch)
        if res.get("status") == True:
            msg = res.get("msg", {})
            # Easebuzz status is usually "success" or "userCancelled" or "bounced"
            st = msg.get("status", "").lower()
            if st == "success":
                return "paid"
            return st
        return "failed"
    except Exception as e:
        print(f"Easebuzz fetch error: {e}")
        return "failed"
