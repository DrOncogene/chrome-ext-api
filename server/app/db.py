from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import AsyncGenerator

from app.settings import settings

if settings.DB_USER:
    URI = (
        f"mongodb://{settings.DB_USER}:{settings.DB_PASSWORD}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
    )
else:
    URI = f"mongodb://{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

client = AsyncIOMotorClient(URI)


async def get_db() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    """
    yields a db instance
    """
    session = await client.start_session()

    try:
        db = session.client.get_database(settings.DB_NAME)
        yield db
    finally:
        await session.end_session()
