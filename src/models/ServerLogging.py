# models/server_logging.py
from beanie import Document
from typing import Optional, Dict
from pydantic import BaseModel


class LogConfig(BaseModel):
    enabled: bool = False
    channel_id: Optional[str] = None


class LogCategory(BaseModel):
    member_ban: LogConfig = LogConfig()
    member_unban: LogConfig = LogConfig()
    member_kick: LogConfig = LogConfig()


class MessageLogs(BaseModel):
    message_delete: LogConfig = LogConfig()
    message_edit: LogConfig = LogConfig()


class RoleLogs(BaseModel):
    role_create: LogConfig = LogConfig()
    role_delete: LogConfig = LogConfig()
    role_update: LogConfig = LogConfig()


class ChannelLogs(BaseModel):
    channel_create: LogConfig = LogConfig()
    channel_delete: LogConfig = LogConfig()
    channel_update: LogConfig = LogConfig()


class Logs(BaseModel):
    moderation_logs: LogCategory = LogCategory()
    message_logs: MessageLogs = MessageLogs()
    role_logs: RoleLogs = RoleLogs()
    channel_logs: ChannelLogs = ChannelLogs()


class ServerLogging(Document):
    id: str  # server ID (_id)
    name: str
    logs: Logs = Logs()

    class Settings:
        name = "server_logging"
