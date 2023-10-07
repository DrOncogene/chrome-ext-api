import json
import os
from sys import exit
import shutil
from time import sleep

import openai
import ffmpeg
from pika.channel import Channel
from pika import BasicProperties

from app.queque import get_channel_unyield
from app.db import get_db_unyield
from app.settings import settings
from app.helpers import make_audio_chuncks


openai.api_key = settings.OPENAI_SECRET


def transcribe(ch: Channel, method, properties: BasicProperties, body):
    """
    transcription callback to consume from TRANSCRIBE_QUEUE
    extract audio from video, create 24MB chunks and transcribe
    via openai whisper api
    """
    file_id = json.loads(body).get('file_id')
    audio_dir = f'{settings.AUDIO_DIR}/{file_id}'
    audio_file = f'{audio_dir}/{file_id}.mp3'
    video_path = f'{settings.SAVE_DIR}/{file_id}.webm'

    if properties.headers:
        retries = properties.headers.get('x-retries', 0)
    else:
        properties.headers = {'x-retries': 0}
        retries = 0

    os.makedirs(audio_dir, mode=0o771, exist_ok=True)
    print('transcribing...', video_path)

    try:
        probe = ffmpeg.probe(video_path, v='error', select_streams='a:0',
                             show_entries='stream=codec_name')
        print('probing...')
        if len(probe['streams']) > 0:
            (
                ffmpeg
                .input(video_path, format='webm', v='error')
                .output(audio_file, v='error')
                .run(overwrite_output=True)
            )
        else:
            raise ValueError('No audio stream found in video')

        total_chunks = make_audio_chuncks(audio_dir, audio_file)

        transcript_file = f'{settings.SAVE_DIR}/{file_id}.txt'

        with open(transcript_file, 'w+t') as f:
            for i in range(total_chunks):
                file = f'{audio_dir}/chunk_{i}.mp3'
                with open(file, 'rb') as c:
                    transcript = openai.Audio.transcribe(
                        'whisper-1', c, response_format='vtt')
                    print(f'transcript: {transcript}')
                    f.write(transcript)
                sleep(20.0)

        db, session = get_db_unyield()
        collection = db[settings.COLLECTION_NAME]

        result = collection.update_one(
            {'_id': file_id},
            {'$set': {'transcribed': True}}
        )

        shutil.rmtree(audio_dir)  # remove audio chunks

        session.end_session()
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f'[*] Transcription complete for video {video_path}')
    except Exception as err:
        print(err)

        if retries < settings.MAX_RETRIES:
            retries += 1

            requeue_delay = float(2 ** retries)

            properties.headers['x-retries'] = retries

            sleep(requeue_delay)

            ch.basic_publish(
                exchange='',
                routing_key=settings.TRANSCRIBE_QUEUE,
                body=body,
                properties=properties
            )
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
            print(f'[*] Transcription failed for video {video_path}, '
                  f'requeueing for retry {retries}')
        else:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print(f"[*] UNABLE TO TRANSCRIBE video {video_path} "
                  f"after {retries} retries")


def main():
    channel = get_channel_unyield()
    channel.queue_declare(queue=settings.TRANSCRIBE_QUEUE, durable=True)

    channel.basic_consume(
        queue=settings.TRANSCRIBE_QUEUE,
        on_message_callback=transcribe
    )

    print(' [*] Waiting for transcription jobs. To exit press CTRL+C')

    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nTRANSCRIPTION SERVICE STOPPED ❌')
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
