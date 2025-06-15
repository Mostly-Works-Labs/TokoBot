from datetime import datetime, timedelta
import secrets, hashlib, os
import jwt

JWT_SECRET = os.getenv("JWT_SECRET")

# Temporary in-memory store
code_store = {}

def generate_6_digit_code() -> str:
    return f"{secrets.randbelow(900000) + 100000:06d}"

def create_encrypted_token(user_id: str, code: str) -> str:
    payload = {
        "user_id": user_id,
        "code_hash": hashlib.sha256(code.encode()).hexdigest(),
        "created_at": datetime.utcnow().isoformat(),
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")
