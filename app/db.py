from pymongo import MongoClient
from pymongo.database import Database

from app.settings import settings

if settings.DB_USER:
    URI = f'mongodb://{settings.DB_USER}:{settings.DB_PASSWORD}@' \
        f'{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'
else:
    URI = f'mongodb://{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'

client = MongoClient(URI)


def get_db() -> Database:
    """
    returns a gridfs instance tied to a collection
    """
    session = client.start_session()

    try:
        db = session.client.get_database(settings.DB_NAME)
        yield db
    finally:
        session.end_session()
