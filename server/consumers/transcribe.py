import json
import os
from sys import exit
import shutil
from bson import ObjectId
import asyncio
import logging

import openai
import ffmpeg
from aio_pika import IncomingMessage

from app.queue import channel_pool
from app.db import get_db
from app.settings import settings
from helpers import make_audio_chuncks


logger = logging.getLogger("TRANSCRIBER")
with open(f"{settings.SECRET_PATH}/{settings.OPENAI_SECRET_FILE}", "r") as f:
    OPENAI_SECRET = f.read().strip()
    openai.api_key = OPENAI_SECRET


async def transcribe(msg: IncomingMessage):
    """
    transcription callback to consume from TRANSCRIBE_QUEUE
    extract audio from video, create 24MB chunks and transcribe
    via openai whisper api
    """
    file_id = json.loads(str(msg.body, encoding="utf-8")).get("file_id")
    audio_dir = f"{settings.AUDIO_DIR}/{file_id}"
    audio_file = f"{audio_dir}/{file_id}.mp3"
    video_path = f"{settings.SAVE_DIR}/{file_id}.webm"

    retries = msg.headers.get("x-retries", 0) if msg.headers else 0

    os.makedirs(audio_dir, mode=0o771, exist_ok=True)
    logger.info(f"Transcribing {video_path}...")

    try:
        probe = ffmpeg.probe(
            video_path, v="error", select_streams="a:0", show_entries="stream=codec_name"
        )
        if len(probe["streams"]) > 0:
            (
                ffmpeg.input(video_path, format="webm", v="error")
                .output(audio_file, v="error")
                .run(overwrite_output=True)
            )
        else:
            raise ValueError(f"NO AUDIO CONTENT found in {video_path}")

        total_chunks = make_audio_chuncks(audio_dir, audio_file)
        transcript_file = f"{settings.SAVE_DIR}/{file_id}.vtt"

        with open(transcript_file, "w+t") as f:
            for i in range(total_chunks):
                file = f"{audio_dir}/chunk_{i}.mp3"
                with open(file, "rb") as c:
                    transcript = openai.Audio.transcribe(
                        "whisper-1", c, response_format="vtt"
                    )
                    f.write(transcript)

        async for db in get_db():
            collection = db[settings.COLLECTION_NAME]
            result = await collection.update_one(
                {"_id": ObjectId(file_id)}, {"$set": {"transcribed": True}}
            )

        shutil.rmtree(audio_dir)  # remove audio chunks
        await msg.ack()

        logger.info(f"[*] Transcription complete for video {video_path}")
    except ValueError as err:
        await msg.ack()
        logger.error(f"NO AUDIO CONTENT in {video_path}, exiting...")
    except Exception as err:
        if retries < settings.MAX_RETRIES:
            retries += 1

            requeue_delay = float(2**retries)
            msg.headers = msg.headers or {}
            msg.headers["x-retries"] = retries

            await asyncio.sleep(requeue_delay)

            await msg.channel.basic_publish(
                body=msg.body,
                routing_key=msg.routing_key,
                properties=msg.properties,
            )
            await msg.nack(requeue=False)

            logger.error(
                f"Transcription failed for video {video_path}, "
                f"requeueing for retry {retries}..."
            )
        else:
            msg.channel.basic_ack(delivery_tag=msg.delivery_tag)
            logger.error(
                f"UNABLE TO TRANSCRIBE video {video_path} "
                f"after {retries} retries: {str(err)}"
            )


async def main():
    async with channel_pool.acquire() as channel:
        queue = await channel.declare_queue(settings.TRANSCRIBE_QUEUE, durable=True)
        await queue.consume(transcribe)

        logger.info("Waiting for transcription jobs. To exit press CTRL+C")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nTRANSCRIPTION SERVICE STOPPED ❌")
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
