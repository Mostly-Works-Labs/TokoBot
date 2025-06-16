<<<<<<< HEAD
from utils.mongodb import TokoDatabase

db = TokoDatabase()

def getLoggingConfig(server_id: str) -> dict | None:
    """Fetch a logging config for a server from the database."""
    return db.servers_logging.find_one({"_id": server_id})

def insertLoggingConfig(server_id: str, server_name: str) -> None:
    """Insert logging config for a server if it doesn't already exist."""
    if db.servers_logging.find_one({"_id": server_id}):
        return

    db.servers_logging.insert_one({
        "_id": server_id,
        "name": server_name,
        "logs": {
            "moderation_logs": {
                k: {"enabled": False, "channel_id": None}
                for k in ["member_ban", "member_unban", "member_kick"]
            },
            "message_logs": {
                k: {"enabled": False, "channel_id": None}
                for k in ["message_delete", "message_edit"]
            },
            "role_logs": {
                k: {"enabled": False, "channel_id": None}
                for k in ["role_create", "role_delete", "role_update"]
            },
            "channel_logs": {
                k: {"enabled": False, "channel_id": None}
                for k in ["channel_create", "channel_delete", "channel_update"]
            }
        }
    })


def ensure_logging_config(server_id: str, server_name: str) -> None:
    if not getLoggingConfig(server_id):
        insertLoggingConfig(server_id, server_name)

def getUser(user_id: str) -> dict | None:
    """Fetch a user from the database."""
    return db.user.find_one({"_id": user_id})

def insertUser(user_id: str, user_name: str) -> None:
    """Insert a user if not already present."""
    db.user.insert_one({
        "_id": user_id,
        "name": user_name,
        "servers": []
    })

def ensure_user_exists(user_id: str, user_name: str) -> None:
    """Ensure a user exists in the database; insert if not."""
    if not getUser(user_id):
        insertUser(user_id, user_name)

def get_log_channel(server_id: str, category: str, log_type: str) -> dict:
    """Return the log settings for a specific log type."""
    server = getLoggingConfig(server_id)
    config = (
        server.get("logs", {})
              .get(category, {})
              .get(log_type, {})
        if server else {}
    )
    return {
        "enabled": config.get("enabled", False),
        "channel_id": config.get("channel_id") or ""
    }

def should_log(server_id: str, category: str, log_type: str) -> bool:
    """Returns True if logging is enabled for the given type."""
    server = getLoggingConfig(server_id)
    return (
        server.get("logs", {})
              .get(category, {})
              .get(log_type, {})
              .get("enabled", False)
        if server else False
    )

def set_log(server_id: str, category: str, log_type: str, channel_id: str, enabled: bool = True) -> None:
    """Enable or disable logging for a given log type."""
    db.servers_logging.update_one(
        {"_id": server_id},
        {"$set": {
            f"logs.{category}.{log_type}.enabled": enabled,
            f"logs.{category}.{log_type}.channel_id": channel_id
        }}
    )
=======
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
>>>>>>> recovery-b00a416
