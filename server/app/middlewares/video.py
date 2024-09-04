from datetime import datetime, UTC
import json
import os
import shutil
import re

from fastapi.exceptions import HTTPException
from fastapi import UploadFile
from bson.objectid import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from aio_pika import Message, DeliveryMode

from app.schemas.video import Video
from app.settings import settings
from app.queue import channel_pool
from app import logger as app_logger
from helpers import format_videos


async def create_video(
    name: str, file_type: str, db: AsyncIOMotorDatabase
) -> tuple[str, HTTPException]:
    """creates a new video entry in db"""
    collection = db[settings.COLLECTION_NAME]

    try:
        result = await collection.insert_one(
            {
                "name": name,
                "file_type": file_type,
                "file_loc": None,
                "uploaded": True,
                "completed": False,
                "transcribed": False,
                "created_at": datetime.now(UTC),
            }
        )

        # create save dir if it does not exist
        os.makedirs(f"{settings.SAVE_DIR}", mode=0o711, exist_ok=True)

        return str(result.inserted_id), None
    except Exception as err:
        app_logger.error(str(err))
        return None, HTTPException(status_code=500, detail="Error creating new video")


async def publish_merge_job(
    file_id: str,
) -> None:
    """publishes a merge job to the queue"""

    async with channel_pool.acquire() as channel:
        await channel.default_exchange.publish(
            Message(
                json.dumps({"file_id": file_id}).encode("utf-8"),
                content_type="text/json",
                delivery_mode=DeliveryMode.PERSISTENT,
            ),
            routing_key=settings.VIDEO_QUEUE,
        )


async def get_videos(db: AsyncIOMotorDatabase, skip: int) -> list[Video]:
    """gets all videos from db"""

    collection = db[settings.COLLECTION_NAME]

    videos = await collection.find({}).skip(skip).limit(5).to_list(length=None)

    return await format_videos(videos)


async def get_video(
    file_id: str, db: AsyncIOMotorDatabase
) -> tuple[Video, HTTPException]:
    """gets video from db"""

    collection = db[settings.COLLECTION_NAME]

    file = await collection.find_one({"_id": ObjectId(file_id)})
    if not file:
        return None, HTTPException(status_code=404, detail="That video does not exist")

    if not file["completed"]:
        return None, HTTPException(status_code=400, detail="Video still being processed")

    return file, None


async def search_videos(db: AsyncIOMotorDatabase, query: str) -> list[Video]:
    """searches for video in the db with video.name == query"""

    collection = db[settings.COLLECTION_NAME]
    pattern = re.compile(f".*{re.escape(query)}.*", re.IGNORECASE)

    matches = await collection.find({"name": {"$regex": pattern}}).to_list(length=None)

    return format_videos(matches)


def save_chunk(file_id: str, chunk: UploadFile, chunk_num: int):
    """saves a video chunk to disk"""

    chunks_dir = f"{settings.CHUNKS_DIR}/{file_id}"
    chunk_file = f"{chunks_dir}/{chunk_num}.webm"

    with open(chunk_file, "wb") as f:
        shutil.copyfileobj(chunk.file, f)
