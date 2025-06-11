from fastapi import Request, HTTPException
from jose import jwt, JWTError
import os

JWT_SECRET = os.getenv("JWT_SECRET")

def get_current_user_id(request: Request) -> str:
    print("🔍 Received cookies in /auth/verify:", request.cookies)
    token = request.cookies.get("auth_token")

    # Optional: support Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
