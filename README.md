# HNGX Stage 5 task

## Description

A backend api for a chrome extension that functions as a screen recorder. The api processes and stored the video files.

## Technologies

- Python 3.11
- FastAPI
- Pymongo
- mongodb on docker
- poetry or pip for dependency management

## Installation

- Clone the repo
- Install poetry
- Run `poetry install` to install dependencies
- Run `poetry shell` to activate the virtual environment
- Or use pip to install dependencies from `requirements.txt`: `pip install -r requirements.txt`
- Set environment variables: see `.env.example`
- Spin up a mongodb instance on docker: `docker run -d -p 27017:27017 --name mongodb mongo:latest`
- Spin up rabbitmq instance on docker: `docker run -d -p 5672:5672 -p 15672:15672 -p 15692:15692 --name rabbitmq rabbitmq:latest`
- Both rabbitmq and mongodb can alse be installed manually without docker
- Install ffmpeg: `sudo apt install ffmpeg`
- Check [here](https://phoenixnap.com/kb/ffmpeg-windows) for instructions on installing ffmpeg on windows
- Run `python3 main.py` to start the server
- In separate terminals, run:
  - Run `python3 merger.py` to start the video merger service
  - Run `python3 transribe.py` to start the video transcription service

## Endpoints

- POST /upload/new: Start recording a new video

  - Request body:

  ```
  {
    file_type: str
  }
  ```

  - Response:

  ```
  {
    status_code: int,
    message: str,
    data: {
      file_id: str
    }
  }
  ```

- POST /upload/chunks: Upload a chunk of the video

  - Request body: formData with fields:

  ```
  {
    file_id: str,
    chunk: Blob,
    is_final: boolean
    chunk_num: int
  }
  ```

  - Response:

  ```
  {
    status_code: int,
    message: str,
    data: null
  }
  ```

- GET /videos/{file_id}: Get a video
  - Response: Video file

## Enjoy!
