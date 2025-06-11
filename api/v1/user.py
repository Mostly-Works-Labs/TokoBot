
from fastapi import APIRouter, HTTPException, Request
from jose import jwt, JWTError
from pydantic import BaseModel
from bot import Ramen
import pyvolt, os
from fastapi import APIRouter, Depends
from api.v1.dependencies.auth import get_current_user_id

router = APIRouter()
bot = Ramen()
db = bot.db

class UserInfo(BaseModel):
    user_id: str
    username: str
    avatar_url: str
    
@router.get("/me/info", response_model=UserInfo)
async def get_user_info(user_id: str = Depends(get_current_user_id)):
    user = await bot.fetch_user(user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserInfo(
        user_id=user.id,
        username=user.name,
        avatar_url=user.avatar.url if user.avatar else None
    )
