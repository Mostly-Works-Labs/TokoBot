import os
import sys
import logging
import pyvolt

from dotenv import load_dotenv
from pyvolt.ext import commands
from utils.mongodb import RamenDatabase

load_dotenv()

# === Prepare log directory ===
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# === Styled Logging Setup ===

class ColorFormatter(logging.Formatter):
    COLORS = {
        "DEBUG":    "\033[38;5;240m\033[1m",  # Bold dark gray
        "INFO":     "\033[38;5;75m\033[1m",   # Bold deep blue
        "WARNING":  "\033[38;5;214m\033[1m",  # Bold golden yellow
        "ERROR":    "\033[38;5;160m\033[1m",  # Bold red
        "CRITICAL": "\033[38;5;124m\033[1m",  # Bold dark red
    }
    RESET = "\033[0m"
    TIMESTAMP = "\033[38;5;240m\033[1m"       # Bold gray
    RAMEN_COLOR = "\033[38;5;229m\033[1m"      # #FAFAD0 as ANSI 229

    def format(self, record):
        levelname = record.levelname
        level_colored = f"{self.COLORS.get(levelname, '')}{levelname:<8}{self.RESET}"
        timestamp = f"{self.TIMESTAMP}{self.formatTime(record, self.datefmt)}{self.RESET}"

        source = record.name.capitalize()
        if source.lower() == "ramen":
            source_colored = f"{self.RAMEN_COLOR}RamenBot{self.RESET}"
        else:
            source_colored = f"\033[38;5;244m\033[1m{source}{self.RESET}"  # Dim gray bold

        return f"{timestamp} {level_colored} {source_colored}  {record.getMessage()}"

# === Logger Configuration ===

log_format = "%(asctime)s %(levelname)-8s %(name)s %(message)s"
date_format = "%Y-%m-%d %H:%M:%S"

logger = logging.getLogger("ramen")
logger.setLevel(logging.INFO)

if not logger.handlers:
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(ColorFormatter(fmt=log_format, datefmt=date_format))

    # File handler (logs/latest.log)
    log_file_path = os.path.join(LOG_DIR, "latest.log")
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8", mode="w")
    file_handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # PyVolt internal logging
    pyvolt_logger = logging.getLogger("pyvolt")
    pyvolt_logger.setLevel(logging.INFO)
    if not pyvolt_logger.handlers:
        pyvolt_logger.addHandler(console_handler)
        pyvolt_logger.addHandler(file_handler)

# === Bot Class ===

class Ramen(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=self.get_prefix,
            token = os.getenv("TOKEN"),
        )
        self.db = RamenDatabase()
        self.logger = logger

    async def load_cogs(self) -> None:
        cog_dir = os.path.join(os.path.dirname(__file__), "cogs")
        for file in os.listdir(cog_dir):
            if file.endswith(".py"):
                ext = file[:-3]
                try:
                    await self.load_extension(f"cogs.{ext}")
                    logger.info(f"Loaded extension '{ext}'")
                except Exception as e:
                    logger.error(f"Failed to load extension '{ext}': {e}")
    
    async def get_prefix(self, message: pyvolt.Message):
        if message.server is None:
            return "r"
        server_id = message.server.id
        server_name = message.server.name
        collection = self.db.prefixes.find_one({"_id": server_id})

        if collection:
            return collection.get("prefix")

        default_prefix = "r"
        self.db.prefixes.insert_one({
            "_id": server_id,
            "servername": server_name,
            "prefix": default_prefix
        })
        return default_prefix

    async def setup_hook(self) -> None:
        self.db.connect()
        await self.load_cogs()

    async def on_ready(self, event) -> None:
        logger.info(f"Logged in as {self.user.name} ({self.user.id})")

# === Bot ===
bot = Ramen()

if __name__ == "__main__":
    bot.run(os.environ.get("TOKEN"))  # Start the bot

