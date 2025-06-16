from beanie import Document
from pydantic import Field

class User(Document):
    id: str = Field(alias="_id")  # Use 'id' as the field name, alias to '_id'
    userid: str
    name: str
    token: str

    class Settings:
        name = "users"