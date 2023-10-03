import json
import os
from sys import exit
import shutil
from time import sleep

import moviepy.editor as mp

from app.queque import get_channel_unyield
from app.db import get_db_unyield
from app.settings import settings
from app.helpers import combine_chunks_to_video


def merge(channel, method, properties, body):
    """
    consumer of VIDEO_QUEUE. merges chunks into a video
    and publish to TRANSCRIBE_QUEUE
    """
    sleep(5)

    try:
        file_id: str = json.loads(body).get('file_id')
        file_path = f'{settings.SAVE_DIR}/{file_id}'
        chunks_dir = f'{settings.CHUNKS_DIR}/{file_id}'

        #  get a sorted list of paths to chunks
        chunks = sorted([chunk.path for chunk in os.scandir(chunks_dir)])

        combine_chunks_to_video(chunks, f'{file_path}.mp4')  # combine chunks

        # shutil.rmtree(f'{settings.CHUNKS_DIR}/{file_id}') #  remove chunks

        db, session = get_db_unyield()
        collection = db[settings.COLLECTION_NAME]

        result = collection.update_one(
            {'_id': file_id},
            {'$set': {'completed': True, 'file_loc': f'{file_path}.mp4'}}
        )

        session.end_session()

        channel.basic_publish(
            exchange='',
            routing_key=settings.TRANSCRIBE_QUEUE,
            body=json.dumps({
                'file_id': file_id,
            })
        )
        print(f'[*] Merging complete for video {file_id}')
    except Exception as err:
        print(f"[*] Unable to merge chunks for video {file_id}")
        print(err)


def main():
    channel = get_channel_unyield()
    channel.queue_declare(queue=settings.VIDEO_QUEUE, durable=True)
    channel.basic_consume(
        queue='videos',
        auto_ack=True,
        on_message_callback=merge
    )

    print(' [*] Waiting for messages. To exit press CTRL+C')

    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('MERGER SERVICE STOPPED ❌')
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
