from typing import BinaryIO

from fastapi import UploadFile

from app.settings import settings
from app.schemas.video import Chunk


def save_chunk(file_id: str, chunks: UploadFile, chunk_num: int):
    """adds a chunk of data to a video"""

    chunks_dir = f'{settings.CHUNKS_DIR}/{file_id}'

    with open(f'{chunks_dir}/{chunk_num}', 'w+b') as f:
        f.write(chunks.file.read())
