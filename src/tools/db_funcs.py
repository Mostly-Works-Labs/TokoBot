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