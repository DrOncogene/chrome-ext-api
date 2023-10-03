from typing import Any
from datetime import datetime

from pydantic import BaseModel


class VideoIn(BaseModel):
    file_type: str = 'webm'


class Video(BaseModel):
    _id: str
    file_type: str
    file_loc: str
    completed: bool = False
    transcribed: bool = False
    created_at: datetime
