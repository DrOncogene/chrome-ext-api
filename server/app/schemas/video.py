from datetime import datetime

from pydantic import BaseModel


class VideoIn(BaseModel):
    name: str
    file_type: str = "webm"


class Video(BaseModel):
    _id: str
    file_type: str
    file_loc: str
    uploaded: bool = False
    completed: bool = False
    transcribed: bool = False
    created_at: datetime
