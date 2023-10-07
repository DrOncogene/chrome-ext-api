import json
import os
from sys import exit
import shutil
from time import sleep

import pika
from pika.channel import Channel
from pika import BasicProperties

from app.queque import get_channel_unyield
from app.db import get_db_unyield
from app.settings import settings
from app.helpers import combine_chunks


def merge(ch: Channel, method, properties: BasicProperties, body):
    """
    consumer of `VIDEO_QUEUE`. merges chunks into a video
    and publish to a job to the `TRANSCRIBE_QUEUE`
    """
    sleep(5)

    file_id: str = json.loads(body).get('file_id')
    video_path = f'{settings.SAVE_DIR}/{file_id}.webm'
    chunks_dir = f'{settings.CHUNKS_DIR}/{file_id}'

    print(f'merging chunks for {video_path}...')

    if properties.headers:
        retries = properties.headers.get('x-retries', 0)
    else:
        properties.headers = {'x-retries': 0}
        retries = 0

    try:

        #  get a sorted list of paths to chunks
        chunks = sorted([chunk.path for chunk in os.scandir(chunks_dir)])

        success = combine_chunks(chunks, video_path)

        if not success:
            raise Exception('Unable to merge chunks')

        shutil.rmtree(f'{settings.CHUNKS_DIR}/{file_id}')

        db, session = get_db_unyield()
        collection = db[settings.COLLECTION_NAME]

        result = collection.update_one(
            {'_id': file_id},
            {'$set': {'completed': True, 'file_loc': video_path}}
        )

        session.end_session()

        # publish transcription job
        ch.basic_publish(
            exchange='',
            routing_key=settings.TRANSCRIBE_QUEUE,
            body=json.dumps({
                'file_id': file_id,
            }),
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            )
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f'[*] Merging complete for video {video_path}')
    except OSError as err:
        print(err)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f'[*] CHUNKS NOT FOUND for video {video_path}')
    except Exception as err:
        print(err)

        if retries < settings.MAX_RETRIES:
            retries += 1

            requeue_delay = float(2 ** retries)

            properties.headers['x-retries'] = retries

            sleep(requeue_delay)  # sleep for 2^retries seconds

            # requeue job with modified properties/headers
            ch.basic_publish(
                exchange='',
                routing_key=settings.VIDEO_QUEUE,
                body=body,
                properties=properties
            )
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            print(f'[*] MERGING CHUNKS failed for video {video_path}, '
                  f'requeueing for retry {retries}')
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"[*] UNABLE TO MERGE chunks for video {video_path} "
                  f"after {retries} retries")


def main():
    channel = get_channel_unyield()
    channel.queue_declare(queue=settings.VIDEO_QUEUE, durable=True)
    channel.basic_consume(
        queue='videos',
        on_message_callback=merge
    )

    print(' [*] Waiting for merging jobs. To exit press CTRL+C')

    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nMERGER SERVICE STOPPED ❌')
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
