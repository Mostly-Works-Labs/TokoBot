import os
import time
import logging
import pkgutil
import importlib
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import ConnectionFailure
from beanie import init_beanie, Document
from dotenv import load_dotenv

# Dynamically import all models from the models package
def get_beanie_models():
    import models  # Make sure models/__init__.py exists
    model_classes = []
    for _, module_name, _ in pkgutil.iter_modules(models.__path__):
        module = importlib.import_module(f"models.{module_name}")
        for attr in dir(module):
            obj = getattr(module, attr)
            if isinstance(obj, type) and issubclass(obj, Document) and obj is not Document:
                model_classes.append(obj)
    return model_classes

# === Terminal Styling ===

class Colour:
    timestamp = "\033[38;5;240m\033[1m"
    label = "\033[38;5;37m\033[1m"
    reset = "\033[0m"
    levels = {
        "DEBUG":    "\033[38;5;240m\033[1m",
        "INFO":     "\033[38;5;75m\033[1m",
        "WARNING":  "\033[38;5;214m\033[1m",
        "ERROR":    "\033[38;5;160m\033[1m",
        "CRITICAL": "\033[38;5;124m\033[1m",
    }

# === Logger ===

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
            label = f"{self.colour.label}TokoDB{self.colour.reset}"
            return f"{timestamp} {level} {label}  {record.getMessage()}"

    formatter = MongoFormatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    console.setFormatter(formatter)
    logger.addHandler(console)

    log_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs", "latest.log")
    file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="a")
    file_handler.setFormatter(logging.Formatter(fmt="%(asctime)s %(levelname)s %(name)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
    logger.addHandler(file_handler)

# === Async Beanie Database Wrapper ===

class TokoDatabase:
    def __init__(self):
        load_dotenv()
        self._client = AsyncIOMotorClient(os.getenv("mongoURI"))
        self._db = self._client["Toko"]

    async def ping(self) -> float | None:
        try:
            start = time.time()
            await self._client.admin.command("ping")
            return round((time.time() - start) * 1000, 2)
        except ConnectionFailure as e:
            logger.error(f"Failed to ping MongoDB:\n{e}")
            return None

    async def connect(self):
        logger.info("Connecting to MongoDB...")
        ms = await self.ping()
        if ms is not None:
            logger.info(f"Connected to MongoDB. Ping: {ms}ms")
        else:
            logger.warning("Connection established, but ping failed.")

        # Dynamically load all Beanie models from the models package
        models = get_beanie_models()
        await init_beanie(
            database=self._db,
            document_models=models
        )

db = TokoDatabase()