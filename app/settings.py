import os

from decouple import config, AutoConfig


class Settings:
    DB_HOST = config('DB_HOST', default='localhost')
    DB_PORT = config('DB_PORT', default='27017')
    DB_NAME = config('DB_NAME', default='videos_store')
    DB_USER = config('DB_USER', default=None)
    DB_PASSWORD = config('DB_PASSWORD', default=None)
    COLLECTION_NAME = config('COLLECTION_NAME', default='videos')
    SAVE_DIR = config('SAVE_DIR', default='/tmp/videos')
    CHUNKS_DIR = config('CHUNKS_DIR', default='/tmp/chunks')
    SERVER_URL = config('SERVER_URL', default='http://localhost:8001')
    RABBITMQ_HOST = config('RABBITMQ_HOST', default='localhost')
    RABBITMQ_PORT = config('RABBITMQ_PORT', default=5672, cast=int)
    VIDEO_QUEUE = config('VIDEO_QUEUE', default='videos')
    TRANSCRIBE_QUEUE = config('TRANSCRIBE_QUEUE', default='transcripts')
    OPENAPI_SECRET = config('OPENAPI_SECRET')


settings = Settings()
