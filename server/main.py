from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.router import router
from app.queue import channel_setup, channel_pool
from app.settings import settings


async def on_startup() -> None:
    """called when fastapi starts"""
    await channel_setup(channel_pool)


app = FastAPI(on_startup=[on_startup])
app.include_router(router)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@app.get("/")
async def root():
    return {"message": "Welcome to the video service API"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        workers=3,
    )
