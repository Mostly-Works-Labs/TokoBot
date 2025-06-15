from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from datetime import datetime, timedelta
from bot import Toko
import pyvolt, os, secrets, hashlib
from fastapi import Depends
from api.v1.dependencies.auth import get_current_user_id
from api.v1.utils import generate_6_digit_code, create_encrypted_token, code_store

router = APIRouter()
bot = Toko()

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

@router.post("/generate-code", response_model=CodeResponse)
async def generate_code(request: CodeRequest):
    try:
        code = generate_6_digit_code()
        user: pyvolt.User = await bot.fetch_user(request.user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        code_store[request.user_id] = {
            "code_hash": hashlib.sha256(code.encode()).hexdigest(),
            "created_at": datetime.utcnow()
        }

        em = [pyvolt.SendableEmbed(
            title="🔐 This code is private. Do not share it.",
            description=f"""**Your login code is:** **`{code}`**

               This code expires in 10 minutes.
               For security reasons, please do not share this code with anyone.

               *If you did not request this code, please ignore this message.*""",
               color="#242424"
        )]

        await user.send(embeds=em)
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

        is_production = os.getenv("ENVIRONMENT") == "production"
        response.set_cookie(
            key="auth_token",
            value=token,
            httponly=True,
            secure=is_production,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/",
        )

        expires_at = datetime.utcnow() + timedelta(days=7)
        del code_store[request.user_id]

        return UserResponse(
            user_id=request.user_id,
            created_at=stored["created_at"],
            expires_at=expires_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error verifying code: {str(e)}")

@router.get("/auth/verify")
async def verify_token(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id, "authenticated": True}

@router.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie(key="auth_token", path="/")
    return {"message": "Logged out successfully"}
