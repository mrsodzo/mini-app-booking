import hashlib
import hmac
import json
import os
from typing import Optional, Dict, Any
from bot.config import settings


def validate_webapp_data(init_data: str) -> Optional[Dict[str, Any]]:
    try:
        data = parse_init_data(init_data)
        if not data:
            return None
        
        hash_str = data.pop("hash", "")
        if not hash_str:
            return None
        
        data_check_string = "\n".join(
            f"{k}={v}" for k, v in sorted(data.items())
        )
        
        secret_key = hmac.new(
            b"WebAppData",
            settings.bot_token.encode(),
            hashlib.sha256,
        ).digest()
        
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256,
        ).hexdigest()
        
        if not hmac.compare_digest(calculated_hash, hash_str):
            return None
        
        return data
    except Exception:
        return None


def parse_init_data(init_data: str) -> Dict[str, str]:
    result = {}
    for param in init_data.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            result[key] = value
    return result


def get_webapp_user(init_data: str) -> Optional[Dict[str, Any]]:
    data = validate_webapp_data(init_data)
    if not data:
        return None
    
    user_json = data.get("user")
    if not user_json:
        return None
    
    try:
        return json.loads(user_json)
    except json.JSONDecodeError:
        return None