from decouple import config


class Settings:
    DB_HOST = config('DB_HOST', default='localhost')
    DB_PORT = config('DB_PORT', default='27017')
    DB_NAME = config('DB_NAME', default='videos_store')
    DB_USER = config('DB_USER', default=None)
    DB_PASSWORD = config('DB_PASSWORD', default=None)
    SERVER_URL = config('SERVER_URL', default='http://localhost:8001')


settings = Settings()
