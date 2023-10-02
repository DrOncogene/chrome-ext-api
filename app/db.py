from pymongo import MongoClient
from pymongo.database import Database
from pymongo.client_session import ClientSession

from app.settings import settings

if settings.DB_USER:
    URI = f'mongodb://{settings.DB_USER}:{settings.DB_PASSWORD}@' \
        f'{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'
else:
    URI = f'mongodb://{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}'

client = MongoClient(URI)


def get_db() -> Database:
    """
    yields a db instance
    """
    session = client.start_session()

    try:
        db = session.client.get_database(settings.DB_NAME)
        yield db
    finally:
        session.end_session()


def get_db_unyield() -> tuple[Database, ClientSession]:
    """
    returns a db instance
    """
    session = client.start_session()

    db = session.client.get_database(settings.DB_NAME)
    return db, session
