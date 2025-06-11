import os
import time
import logging
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# === Terminal Styling ===

class Colour:
    timestamp = "\033[38;5;240m\033[1m"    # Bold gray
    label = "\033[38;5;37m\033[1m"         # Teal for [MongoDB]
    reset = "\033[0m"
    levels = {
        "DEBUG":    "\033[38;5;240m\033[1m",  # Gray
        "INFO":     "\033[38;5;75m\033[1m",   # Blue
        "WARNING":  "\033[38;5;214m\033[1m",  # Yellow
        "ERROR":    "\033[38;5;160m\033[1m",  # Red
        "CRITICAL": "\033[38;5;124m\033[1m",  # Dark red
    }

# === Mongo Logger ===

logger = logging.getLogger("mongodb")
logger.setLevel(logging.INFO)

if not logger.handlers:
    console = logging.StreamHandler()

    class MongoFormatter(logging.Formatter):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.colour = Colour

        def format(self, record):
            levelname = record.levelname.upper()
            level = f"{self.colour.levels.get(levelname, '')}{levelname:<8}{self.colour.reset}"
            timestamp = f"{self.colour.timestamp}{self.formatTime(record, self.datefmt)}{self.colour.reset}"
            label = f"{self.colour.label}MongoDB{self.colour.reset}"
            return f"{timestamp} {level} {label}  {record.getMessage()}"

    formatter = MongoFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console.setFormatter(formatter)
    logger.addHandler(console)

    # Shared log file handler
    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "latest.log")
    file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
    file_handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

# === MongoDB Wrapper ===

class RamenDatabase:
    def __init__(self):
        load_dotenv("config/.env")
        self._client = MongoClient(os.getenv("mongoURI"))
        self._db = self._client["Ramen"] 

        self.prefixes = self._db["prefixes"]
        self.servers = self._db["servers"]
        self.user = self._db["users"]

    def ping(self) -> float | None:
        try:
            start = time.time()
            self._client.admin.command("ping")
            return round((time.time() - start) * 1000, 2)
        except ConnectionFailure as e:
            logger.error(f"Failed to ping MongoDB:\n{e}")
            return None

    def connect(self):
        logger.info("Connecting to MongoDB...")
        ms = self.ping()
        if ms is not None:
            logger.info(f"Connected to MongoDB. Ping: {ms}ms")
        else:
            logger.warning("Connection established, but ping failed.")
