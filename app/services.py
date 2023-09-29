from fastapi import UploadFile
from fastapi.exceptions import HTTPException
from bson.objectid import ObjectId
from pymongo.database import Database
from typing import BinaryIO

from gridfs import GridFSBucket, GridOut

from app.helpers import generate_link


def save_video(
    video: UploadFile,
    collection: str,
    db: Database
) -> tuple[str, HTTPException]:
    """saves video to db"""

    fs = GridFSBucket(db, bucket_name=collection)

    try:
        file_id = fs.upload_from_stream(
            filename=video.filename,
            source=video.file,
        )

        return str(file_id), None
    except Exception as err:
        return None, HTTPException(status_code=500,
                                   detail="Error saving video")


def get_video(
    file_id: str,
    collection: str,
    db: Database
) -> tuple[GridOut, HTTPException]:
    """gets video from db"""

    fs = GridFSBucket(db, bucket_name=collection)

    try:
        file = fs.open_download_stream(ObjectId(file_id))
        return file, None
    except Exception as err:
        return None, HTTPException(status_code=500,
                                   detail="Error fetching video")


def get_collection_videos(
    collection: str,
    db: Database
) -> tuple[list[str], HTTPException]:
    """gets all videos from a collection"""

    fs = GridFSBucket(db, bucket_name=collection)

    try:
        files = fs.find()
        links = [generate_link(collection, file._id) for file in files]

        return links, None
    except Exception as err:
        return None, HTTPException(status_code=500,
                                   detail="Error fetching links to your vids")


def delete_video(
    file_id: str,
    collection: str,
    db: Database
) -> tuple[bool, HTTPException]:
    """deletes video from db"""

    fs = GridFSBucket(db, bucket_name=collection)

    try:
        fs.delete(ObjectId(file_id))
        return True, None
    except Exception as err:
        return False, HTTPException(status_code=500,
                                    detail="Error deleting video")
