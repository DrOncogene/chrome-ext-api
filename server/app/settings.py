import logging
import logging.config

from decouple import config


logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(name)s | %(asctime)s | %(levelname)s: %(message)s",
        },
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        }
    },
    "loggers": {
        "root": {"level": "INFO", "handlers": ["stdout"]},
    },
}
logging.config.dictConfig(logging_config)


class Settings:
    APP_HOST = config("APP_HOST", default="localhost")
    APP_PORT = config("APP_PORT", default=8000, cast=int)
    DEBUG = config("DEBUG", default=False, cast=bool)
    DB_HOST = config("DB_HOST", default="localhost")
    DB_PORT = config("DB_PORT", default="27017")
    DB_NAME = config("DB_NAME", default="videos_store")
    DB_USER = config("DB_USER", default=None)
    DB_PASSWORD = config("DB_PASSWORD", default=None)
    COLLECTION_NAME = config("COLLECTION_NAME", default="videos")
    SAVE_DIR = config("SAVE_DIR", default="/tmp/videos")
    CHUNKS_DIR = config("CHUNKS_DIR", default="/tmp/chunks")
    AUDIO_DIR = config("AUDIO_DIR", default="/tmp/audio_chunks")
    VIDEO_QUEUE = config("VIDEO_QUEUE", default="videos")
    TRANSCRIBE_QUEUE = config("TRANSCRIBE_QUEUE", default="transcripts")
    MAX_RETRIES = config("MAX_RETRIES", default=3, cast=int)
    SECRET_PATH = config("SECRET_PATH")
    RABBITMQ_SECRET_FILE = config("RABBITMQ_SECRET_FILE", "rabbitmq_url")
    OPENAI_SECRET_FILE = config("OPENAI_SECRET_FILE", "openai_secret")
    RABBITMQ_URL = None
    OPENAI_SECRET = None


settings = Settings()
with open(f"{settings.SECRET_PATH}/{settings.RABBITMQ_SECRET_FILE}", "r") as f:
    settings.RABBITMQ_URL = f.read().strip()
