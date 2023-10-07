import shutil

from fastapi import UploadFile

from app.settings import settings


def save_chunk(file_id: str, chunk: UploadFile, chunk_num: int):
    """adds a chunk of data to a video"""

    chunks_dir = f'{settings.CHUNKS_DIR}/{file_id}'

    with open(f'{chunks_dir}/{chunk_num}.webm', 'wb') as chunk_file:
        shutil.copyfileobj(chunk.file, chunk_file)
