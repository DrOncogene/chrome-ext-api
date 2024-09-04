import asyncio
import json
import os
from sys import exit
import shutil
from bson import ObjectId
import logging

from aio_pika import IncomingMessage

from app.queue import channel_pool
from app.db import get_db
from app.settings import settings
from helpers.helpers import combine_chunks


logger = logging.getLogger("MERGER")


async def merge(msg: IncomingMessage):
    """
    consumer of `VIDEO_QUEUE`. merges chunks into a video
    and publish to a job to the `TRANSCRIBE_QUEUE`
    """
    await asyncio.sleep(5)

    file_id: str = json.loads(msg.body.decode("utf-8")).get("file_id")
    video_path = f"{settings.SAVE_DIR}/{file_id}.webm"
    chunks_dir = f"{settings.CHUNKS_DIR}/{file_id}"

    async for db in get_db():
        collection = db[settings.COLLECTION_NAME]
        result = await collection.find_one({"_id": ObjectId(file_id)})
        if not result:
            await collection.delete_one({"_id": ObjectId(file_id)})
            await msg.nack(requeue=False)
            logger.error(f"video file broken: {file_id}")

    logger.info(f"Processing {video_path}...")

    retries = msg.headers.get("x-retries", 0) if msg.headers else 0

    try:
        #  get a sorted list of paths to chunks
        chunks = sorted([chunk.path for chunk in os.scandir(chunks_dir)])
        success = combine_chunks(chunks, video_path)
        if not success:
            raise Exception("Unable to merge chunks")

        shutil.rmtree(f"{settings.CHUNKS_DIR}/{file_id}")

        async for db in get_db():
            collection = db[settings.COLLECTION_NAME]
            result = await collection.update_one(
                {"_id": ObjectId(file_id)},
                {"$set": {"completed": True, "file_loc": video_path}},
            )

        await msg.channel.basic_publish(
            body=json.dumps(
                {
                    "file_id": file_id,
                }
            ).encode(),
            routing_key=settings.TRANSCRIBE_QUEUE,
            properties=msg.properties,
        )

        await msg.ack()
        logger.info(f"Completed processing video {video_path}")
    except OSError as err:
        logger.error(str(err))
        await msg.nack(requeue=False)
        logger.error(f"CHUNKS NOT FOUND for video {video_path}")
    except Exception as err:
        logger.error(str(err))

        if retries < settings.MAX_RETRIES:
            retries += 1

            requeue_delay = float(2**retries)
            msg.headers = msg.headers or {}
            msg.headers["x-retries"] = retries

            await asyncio.sleep(requeue_delay)

            # requeue job with modified properties/headers
            await msg.channel.basic_publish(
                body=msg.body,
                routing_key=msg.routing_key,
                properties=msg.properties,
            )
            await msg.nack(requeue=False)

            logger.error(
                f"Processing failed for video {video_path}, "
                f"requeueing for retry {retries}"
            )
        else:
            await msg.ack()
            logger.error(
                f"Processing failed for video {video_path} " f"after {retries} retries"
            )


async def main():
    async with channel_pool.acquire() as channel:
        queue = await channel.declare_queue(settings.VIDEO_QUEUE, durable=True)
        await queue.consume(merge)

        logger.info("Waiting for merging jobs. To exit press CTRL+C")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nMERGER SERVICE STOPPED ❌")
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
