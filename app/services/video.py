from datetime import datetime
import json
import os

from fastapi.exceptions import HTTPException
from bson.objectid import ObjectId
from pymongo.database import Database
import pika
from pika.channel import Channel

from app.schemas.video import Video
from app.settings import settings


def create_video(
    file_type: str,
    db: Database
) -> tuple[str, HTTPException]:
    """creates a new video entry in db"""
    collection = db[settings.COLLECTION_NAME]

    try:
        result = collection.insert_one({
            'file_type': file_type,
            'file_loc': None,
            'completed': False,
            'transcribed': False,
            'created_at': datetime.utcnow(),
        })

        # create save dir if it does not exist
        os.makedirs(f'{settings.SAVE_DIR}', mode=0o711, exist_ok=True)

        return str(result.inserted_id), None
    except Exception as err:
        print(err)
        return None, HTTPException(status_code=500,
                                   detail="Error creating new video")


def publish_merge_job(
    file_id: str,
    channel: Channel
) -> tuple[bool, HTTPException]:
    """publishes a merge job to the queue"""
    channel.queue_declare(queue=settings.VIDEO_QUEUE, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=settings.VIDEO_QUEUE,
        body=json.dumps({
            'file_id': file_id,
        }),
        properties=pika.BasicProperties(
            delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
        )
    )


def get_video(
    file_id: str,
    db: Database
) -> tuple[Video, HTTPException]:
    """gets video from db"""

    collection = db[settings.COLLECTION_NAME]

    file = collection.find_one({'_id': ObjectId(file_id)})
    if not file:
        return None, HTTPException(status_code=404,
                                   detail="That video does not exist")

    if not file['completed']:
        return None, HTTPException(status_code=400,
                                   detail="Video still being processed")

    return file, None
