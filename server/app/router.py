import os
from typing import Annotated

from fastapi import APIRouter, Depends, BackgroundTasks, Form, UploadFile
from fastapi.responses import FileResponse
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.db import get_db
from app.middlewares.video import (
    create_video,
    get_videos,
    publish_merge_job,
    get_video,
    search_videos,
)
from app.schemas.video import VideoIn
from app.schemas.responses import ResponseModel
from app.middlewares.video import save_chunk
from app.settings import settings


router = APIRouter()


@router.post("/upload/new", status_code=201)
async def start_upload(
    vid: VideoIn, db: AsyncIOMotorDatabase = Depends(get_db)
) -> ResponseModel:
    """
    starts a new upload
    """
    file_id, err = await create_video(vid.name, vid.file_type, db)

    if err:
        raise err

    return {
        "status_code": 201,
        "message": "Video upload started successfully",
        "data": {
            "file_id": file_id,
        },
    }


@router.post("/upload/chunks", status_code=201)
async def upload_chunks(
    file_id: Annotated[str, Form()],
    chunk: Annotated[UploadFile, Form(media_type="video/x-matroska")],
    is_final: Annotated[bool, Form()],
    chunk_num: Annotated[int, Form()],
    background_tasks: BackgroundTasks,
) -> ResponseModel:
    """
    uploads chunks of a video
    """

    # create chunks directory if it doesn't exist
    os.makedirs(f"{settings.CHUNKS_DIR}/{file_id}", mode=0o771, exist_ok=True)

    # save chunk to disk in the background
    background_tasks.add_task(save_chunk, file_id, chunk, chunk_num)
    if is_final:
        await publish_merge_job(file_id)

    return {
        "status_code": 201,
        "message": "Video chunks uploaded successfully",
        "data": None,
    }


@router.get("/videos")
async def fetch_videos(
    limit: int = 10, db: AsyncIOMotorDatabase = Depends(get_db)
) -> ResponseModel:
    """
    fetches videos
    """
    videos = await get_videos(db, limit)
    print(videos)

    return {"status_code": 200, "message": "Videos fetched successfully", "data": videos}


@router.get("/videos/{video_id}")
async def fetch_video(
    video_id: str, db: AsyncIOMotorDatabase = Depends(get_db)
) -> ResponseModel:
    """
    fetches video given it's id
    Returns a streaming response
    """
    file, err = await get_video(video_id, db)

    if err:
        raise err

    if not file.completed:
        return {
            "status_code": 200,
            "message": "Video is still being processed",
            "data": None,
        }

    return FileResponse(file["file_loc"], media_type="video/webm")


@router.get("/search")
async def search(
    query: str, db: AsyncIOMotorDatabase = Depends(get_db)
) -> ResponseModel:
    """searches videos whose name contains query term"""

    matches = await search_videos(db, query)

    return {
        "status_code": 200,
        "message": "Videos fetched successfully",
        "data": matches,
    }
