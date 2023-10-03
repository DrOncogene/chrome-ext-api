import json
import os
from typing import Annotated, Any

from fastapi import APIRouter, Depends, BackgroundTasks, Body, Form, UploadFile
from fastapi.responses import FileResponse
from pymongo.database import Database
from pika.channel import Channel

from app.db import get_db
from app.services.video import create_video, merge_chunks, get_video
from app.schemas.video import VideoIn
from app.services.backgroud_tasks import save_chunk
from app.queque import get_channel
from app.settings import settings


router = APIRouter()


@router.post('/upload/new', status_code=201)
async def start_upload(
    vid: VideoIn,
    db: Database = Depends(get_db)
):
    """
    starts a new upload
    """
    file_id, err = create_video(vid.file_type, db)

    if err:
        raise err

    return {
        'status_code': 201,
        'message': 'Video upload started successfully',
        'data': {
            'file_id': file_id,
        }
    }


@router.post('/upload/chunks', status_code=201)
async def upload_chunks(
    file_id: Annotated[str, Form()],
    chunk: Annotated[UploadFile, Form(media_type='video/x-matroska')],
    is_final: Annotated[bool, Form()],
    chunk_num: Annotated[int, Form()],
    background_tasks: BackgroundTasks,
    channel: Channel = Depends(get_channel)
):
    """
    uploads chunks of data
    """
    print(chunk)

    os.makedirs(f'{settings.CHUNKS_DIR}/{file_id}', mode=0o771, exist_ok=True)

    background_tasks.add_task(save_chunk, file_id, chunk, chunk_num)
    if is_final:
        print('final chunk recieved')
        print(f'recieved {chunk_num} chunks')
        merge_chunks(file_id, channel)

    return {
        'status_code': 201,
        'message': 'Video chunks uploaded successfully',
        'data': None
    }


@router.get('/videos/{video_id}')
async def fetch_video(video_id: str, db: Database = Depends(get_db)):
    """
    fetches video given it's id
    Returns a streaming response
    """
    file, err = get_video(video_id, db)

    if err:
        raise err

    if not file.completed:
        return {
            'status_code': 200,
            'message': 'Video is still being processed',
            'data': None
        }

    return FileResponse(file['file_loc'], media_type='video/mp4')
