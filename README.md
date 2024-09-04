## Description

A backend api for a chrome extension that functions as a screen recorder. The api processes and stored the video files.

## Technologies

- Python 3.12
- FastAPI
- [Motor ODM](https://motor.readthedocs.io/en/stable/index.html) for MongoDB
- mongodb on docker
- RabbitMQ (docker or [cloud AMQP](https://www.cloudamqp.com/))
- poetry or pip for dependency management
- Docker compose
- OPENAI Whisper API

## Setup

- Clone the repo
- Install poetry [here](https://python-poetry.org/docs/)
- Run `poetry install` to install dependencies
- Run `poetry shell` to activate the virtual environment
- Or use pip to install dependencies from `requirements.txt`: `pip install -r requirements.txt`
- Set environment variables: see `server/app/settings.py`
- Create a `secrets/` folder in `server/` and add files `openai_secret` and `rabbitmq_url`.
- Run `docker compose up -d` to bring up the services

## Endpoints

1. POST `/upload/new`: Start recording a new video

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

2. POST `/upload/chunks`: Upload a chunk of the video

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

3. GET `/videos/{file_id}`: Get a video

- Response: Video file

4. GET `/videos`: Get all videos

- Response: List of

5. GET `/search?{query_str}`: Search videos

- Response: List of videos that match the `query_str`

## Enjoy!

### Note

- Check `client/README.md` for the client/extension
