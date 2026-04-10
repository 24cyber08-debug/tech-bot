import os
import requests

ABSTRACT_IP_URL = "https://ipgeolocation.abstractapi.com/v1/"
ABSTRACT_EMAIL_URL = "https://emailvalidation.abstractapi.com/v1/"
ABSTRACT_PHONE_URL = "https://phonevalidation.abstractapi.com/v1/"

def verify_ip(ip_address: str) -> dict:
    api_key = os.getenv("ABSTRACT_IP_KEY")
    if not api_key:
        raise ValueError("ABSTRACT_IP_KEY missing in environment variables.")
    
    resp = requests.get(ABSTRACT_IP_URL, params={"api_key": api_key, "ip_address": ip_address}, timeout=10)
    resp.raise_for_status()
    return resp.json()

def verify_email(email: str) -> dict:
    api_key = os.getenv("ABSTRACT_EMAIL_KEY")
    if not api_key:
        raise ValueError("ABSTRACT_EMAIL_KEY missing in environment variables.")
    
    resp = requests.get(ABSTRACT_EMAIL_URL, params={"api_key": api_key, "email": email}, timeout=10)
    resp.raise_for_status()
    return resp.json()

def verify_phone(phone: str) -> dict:
    api_key = os.getenv("ABSTRACT_PHONE_KEY")
    if not api_key:
        raise ValueError("ABSTRACT_PHONE_KEY missing in environment variables.")
    
    resp = requests.get(ABSTRACT_PHONE_URL, params={"api_key": api_key, "phone": phone}, timeout=10)
    resp.raise_for_status()
    return resp.json()

def run(action: str, **kwargs) -> dict:
    actions = {
        "verify_ip": verify_ip,
        "verify_email": verify_email,
        "verify_phone": verify_phone
    }
    if action not in actions:
        raise ValueError(f"AbstractTool: unknown action '{action}'")
    return actions[action](**kwargs)
