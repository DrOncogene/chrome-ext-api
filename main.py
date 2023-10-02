from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.router import router


app = FastAPI()
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)


@app.get("/")
async def root():
    return {"message": "Welcome to the transcription API"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8001, reload=True,
        workers=3
    )
