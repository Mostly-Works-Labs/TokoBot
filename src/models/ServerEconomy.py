from beanie import Document
from pydantic import BaseModel, Field
from typing import Dict, Optional

class UserEconomy(BaseModel):
    wallet: int = 0
    bank: int = 0
    last_daily: Optional[str] = None
    job: Optional[str] = None

class ServerEconomy(Document):
    id: str  = Field(alias="_id")
    enabled: bool = True
    users: Dict[str, UserEconomy] = Field(default_factory=dict)

    class Settings:
        name = "server_economy"
