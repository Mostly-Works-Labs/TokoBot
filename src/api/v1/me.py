from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from api.v1.dependencies.auth import get_current_user_id
from bot import Toko
import pyvolt

router = APIRouter()
bot = Toko()

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

@router.get("/me/servers")
async def get_user_servers(user_id: str = Depends(get_current_user_id)):
    user = await bot.fetch_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    servers = []
    for server in bot.servers:
        if user in server.members:
            
            servers.append({
                "server_id": server.id,
                "server_name": server.name,
                "avatar_url": server.avatar.url if server.avatar else None
            })

    return {"servers": servers}
