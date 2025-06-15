import os
import sys
import logging
import pyvolt

from dotenv import load_dotenv
from pyvolt.ext import commands
from utils.mongodb import TokoDatabase

load_dotenv()

# === Prepare log directory ===
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# === Styled Logging Setup ===

class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG":    "\033[38;5;240m\033[1m",
        "INFO":     "\033[38;5;75m\033[1m",
        "WARNING":  "\033[38;5;214m\033[1m",
        "ERROR":    "\033[38;5;160m\033[1m",
        "CRITICAL": "\033[38;5;124m\033[1m",
    }
    RESET = "\033[0m"
    TIMESTAMP = "\033[38;5;240m\033[1m"
    TOKO_COLOR = "\033[38;5;229m\033[1m"  # Light yellow

    def format(self, record):
        levelname = record.levelname
        level_colored = f"{self.COLORS.get(levelname, '')}{levelname:<8}{self.RESET}"
        timestamp = f"{self.TIMESTAMP}{self.formatTime(record, self.datefmt)}{self.RESET}"

        source = record.name.capitalize()
        if source.lower() == "toko":
            source_colored = f"{self.TOKO_COLOR}TokoBot{self.RESET}"
        else:
            source_colored = f"\033[38;5;244m\033[1m{source}{self.RESET}"

        return f"{timestamp} {level_colored} {source_colored}  {record.getMessage()}"

# === Logger Configuration ===

log_format = "%(asctime)s %(levelname)-8s %(name)s %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

# Main Toko logger
logger = logging.getLogger("toko")
logger.setLevel(logging.INFO)
logger.propagate = False

# Pyvolt logger (to prevent duplication)
pyvolt_logger = logging.getLogger("Pyvolt")
pyvolt_logger.setLevel(logging.INFO)
pyvolt_logger.propagate = False

if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter(fmt=log_format, datefmt=date_format))

    log_file_path = os.path.join(LOG_DIR, "latest.log")
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="w")
    file_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    # Add to both loggers
    for log in (logger, pyvolt_logger):
        log.addHandler(console_handler)
        log.addHandler(file_handler)

# === Bot Class ===

class Toko(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=self.get_prefix,
            token=os.getenv("TOKEN"),
        )
        self.db = TokoDatabase()
        self.logger = logger

    async def load_cogs(self) -> None:
        cog_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for file in os.listdir(cog_dir):
            if file.endswith(".py"):
                ext = file[:-3]
                try:
                    await self.load_extension(f"cogs.{ext}")
                    logger.info(f"Loaded extension '{ext}'")
                except commands.errors.ExtensionAlreadyLoaded:
                    pass
                except Exception as e:
                    logger.error(f"Failed to load extension '{ext}': {e}")

    async def get_prefix(self, message: pyvolt.Message):
        default_prefix = ".t"

        if message.server is None:
            return [default_prefix]

        server_id = message.server.id
        server_name = message.server.name
        collection = self.db.prefixes.find_one({"_id": server_id})

        if collection:
            return [collection.get("prefix", default_prefix)]

        self.db.prefixes.insert_one({
            "_id": server_id,
            "servername": server_name,
            "prefix": default_prefix
        })
        return [default_prefix]

    async def setup_hook(self) -> None:
        self.db.connect()
        await self.load_cogs()

    async def on_ready(self, event) -> None:
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")

# === Run Bot ===

bot = Toko()

if __name__ == "__main__":
    try:
        logger.info("Starting TokoBot...")
        bot.run(os.environ.get("TOKEN"))
    except Exception as e:
        logger.exception(f"Failed to run bot: {e}")
