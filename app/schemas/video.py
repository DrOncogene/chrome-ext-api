from typing import Any

from pydantic import BaseModel


class VideoIn(BaseModel):
    file_type: str = 'mp4'


class VideoOut(BaseModel):
    file_type: str
    file_url: str


class Video(BaseModel):
    file_type: str
    file_url: str
    file_id: str
    completed: bool = False


class Chunk(BaseModel):
    data: Any
    blob_num: int
    is_final: bool = False


class ChunksIn(BaseModel):
    file_id: str
    chunks: list[Chunk]
