from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from bot import Ramen
from datetime import datetime, timedelta
import pyvolt
import jwt
import os
import secrets
import hashlib
from fastapi import APIRouter, Depends
from api.v1.dependencies.auth import get_current_user_id

router = APIRouter()
bot = Ramen()
db = bot.db
JWT_SECRET = os.getenv("JWT_SECRET")

# In-memory store for example purposes – consider persisting this.
code_store = {}

# Request and Response Models
class CodeRequest(BaseModel):
    user_id: str

class CodeResponse(BaseModel):
    message: str

class VerifyCodeRequest(BaseModel):
    user_id: str
    code: str

class UserResponse(BaseModel):
    user_id: str
    created_at: datetime
    expires_at: datetime

# Helpers
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

# Routes
@router.post("/generate-code", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    try:
        code = generate_6_digit_code()
        user: pyvolt.User = await bot.fetch_user(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Store code for verification later (simple store)
        code_store[request.user_id] = {
            "code_hash": hashlib.sha256(code.encode()).hexdigest(),
            "created_at": datetime.utcnow()
        }

        await user.send(f"Your verification code is: {code} ✅")
        return CodeResponse(message="Code sent successfully.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating code: {str(e)}")

@router.post("/verify-code", response_model=UserResponse)
async def verify_code(request: VerifyCodeRequest, response: Response):
    try:
        stored = code_store.get(request.user_id)
        if not stored:
            raise HTTPException(status_code=404, detail="No code found for user.")

        input_hash = hashlib.sha256(request.code.encode()).hexdigest()
        if input_hash != stored["code_hash"]:
            raise HTTPException(status_code=401, detail="Invalid verification code.")

        token = create_encrypted_token(request.user_id, request.code)
        response.set_cookie("auth_token", token, httponly=True)

        expires_at = datetime.utcnow() + timedelta(days=7)
        return UserResponse(
            user_id=request.user_id,
            created_at=stored["created_at"],
            expires_at=expires_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying code: {str(e)}")

@router.get("/auth/verify")
async def verify_token(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id}