from typing import Annotated

from fastapi import FastAPI, UploadFile, Depends
from fastapi.responses import StreamingResponse, FileResponse
import uvicorn
from pymongo.database import Database
from gridfs import GridFSBucket

from app.db import get_db
from app.services import (
    save_video,
    get_video,
    get_collection_videos,
    delete_video
)
from app.settings import settings
from app.helpers import generate_link


app = FastAPI()


@app.post('/upload/{collection}', status_code=201)
async def upload_video(
    collection: Annotated[str, 'collection name/reference to the browser'],
    video: UploadFile,
    db: Database = Depends(get_db)
):
    """upload a new video"""

    file_id, err = save_video(video, collection, db)

    if err:
        raise err

    url = generate_link(collection, file_id)

    return {
        'status_code': 201,
        'description': 'Video uploaded successfully',
        'data': {
            'video_url': url,
        }
    }


@app.get('/videos/{collection}/{video_id}')
async def fetch_video(
    collection: str,
    video_id: str,
    db: Database = Depends(get_db)
):
    """fetches video from db"""

    def loop_file(file):
        yield from file

    file, err = get_video(video_id, collection, db)

    if err:
        raise err

    return StreamingResponse(loop_file(file), media_type='video/mp4')


@app.get('/{collection}/videos')
async def fetch_user_videos(
    collection: str,
    db: Database = Depends(get_db)
):
    """fetches links for all videos in a collection"""

    links, err = get_collection_videos(collection, db)

    if err:
        raise err

    return {
        'status_code': 200,
        'description': 'Videos fetched successfully',
        'data': {
            'videos': links
        }
    }


@app.delete('/{collection}/{video_id}', status_code=204)
async def del_video(
    collection: str,
    video_id: str,
    db: Database = Depends(get_db)
):
    """deletes a video from db"""

    _, err = delete_video(video_id, collection, db)

    if err:
        raise err

    return {
        'status_code': 204,
        'description': 'Video deleted successfully',
        'data': None
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost",
                port=8000, reload=True, workers=3)
