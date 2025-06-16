from beanie import Document
from pydantic import Field

class Prefix(Document):
    id: str = Field(alias="_id")  # MongoDB _id field
    servername: str
    prefix: str

    class Settings:
        name = "prefixes"