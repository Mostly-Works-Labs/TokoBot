from models.User import User
from models.ServerLogging import ServerLogging, Logs, LogConfig, LogCategory, MessageLogs, RoleLogs, ChannelLogs
from typing import Optional

# === USER FUNCTIONS ===

async def get_user(user_id: str) -> Optional[User]:
    return await User.find_one(User.id == user_id)

async def insert_user(user_id: str, user_name: str):
    if await get_user(user_id):
        return
    await User(id=user_id, name=user_name, servers=[]).insert()

async def ensure_user_exists(user_id: str, user_name: str):
    if not await get_user(user_id):
        await insert_user(user_id, user_name)

# === SERVER LOGGING CONFIG FUNCTIONS ===

async def get_logging_config(server_id: str) -> Optional[ServerLogging]:
    return await ServerLogging.find_one(ServerLogging.id == server_id)

async def insert_logging_config(server_id: str, server_name: str):
    if await get_logging_config(server_id):
        return

    new_config = ServerLogging(
        id=server_id,
        name=server_name,
        logs=Logs(
            moderation_logs=LogCategory(),
            message_logs=MessageLogs(),
            role_logs=RoleLogs(),
            channel_logs=ChannelLogs()
        )
    )
    await new_config.insert()

async def ensure_logging_config(server_id: str, server_name: str):
    if not await get_logging_config(server_id):
        await insert_logging_config(server_id, server_name)

async def get_log_channel(server_id: str, category: str, log_type: str) -> dict:
    config = await get_logging_config(server_id)
    if not config:
        return {"enabled": False, "channel_id": ""}

    log_config = getattr(getattr(config.logs, category, {}), log_type, None)
    return {
        "enabled": getattr(log_config, "enabled", False),
        "channel_id": getattr(log_config, "channel_id", "") or ""
    }

async def should_log(server_id: str, category: str, log_type: str) -> bool:
    config = await get_logging_config(server_id)
    if not config:
        return False

    log_config = getattr(getattr(config.logs, category, {}), log_type, None)
    return getattr(log_config, "enabled", False)

async def set_log(server_id: str, category: str, log_type: str, channel_id: str, enabled: bool = True):
    config = await get_logging_config(server_id)
    if not config:
        return

    log_cat = getattr(config.logs, category, None)
    if not log_cat or not hasattr(log_cat, log_type):
        return

    setattr(getattr(config.logs, category), log_type, LogConfig(enabled=enabled, channel_id=channel_id))
    await config.save()
