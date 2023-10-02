import json
import math
import os
from sys import exit

from moviepy import editor as mp
import openai
from pydub import AudioSegment
from pydub.utils import make_chunks
import ffmpeg

from app.queque import get_channel_unyield
from app.db import get_db_unyield
from app.settings import settings


openai.api_key = settings.OPENAPI_SECRET


def make_audio_chuncks(audio_path: str, audio_file: str):
    print('creating audio chunks')
    audio = AudioSegment.from_file(audio_file)
    channel_count = audio.channels
    sample_width = audio.sample_width
    duration_in_sec = len(audio)/1000
    sample_rate = audio.frame_rate
    bit_depth = sample_width * 8

    file_size = (
        sample_rate * bit_depth * channel_count * duration_in_sec) / 8

    split_size = 24 * 1024 * 1024
    total_chunks = file_size // split_size

    chunk_length_sec = math.ceil((duration_in_sec * split_size)/file_size)
    chunk_length_ms = chunk_length_sec * 1000
    chunks = make_chunks(audio, chunk_length_ms)

    for i, chunk in enumerate(chunks):
        chunk_name = f'{audio_path}/chunk{i}.wav'
        chunk.export(chunk_name, format='wav')

    return total_chunks


def transcribe(channel, method, properties, body):
    """transcription consumer"""

    try:
        file_id = json.loads(body).get('file_id')
        audio_dir = f'/tmp/audio_chunks/{file_id}'
        audio_file = f'{audio_dir}/{file_id}.wav'

        os.makedirs(audio_dir, mode=0o771, exist_ok=True)

        # ffmpeg.input(f'{settings.SAVE_DIR}/{file_id}.mp4'
        #              ).output(audio_file).run()

        video = mp.VideoFileClip(f'{settings.SAVE_DIR}/{file_id}.mp4')
        audio = video.audio.write_audiofile(audio_file)

        total_chunks = make_audio_chuncks(audio_dir, audio_file)

        for i in range(total_chunks):
            transcript_file = open(
                f'{settings.SAVE_DIR}/{file_id}.txt', 'w+t')
            with open(f'{audio_dir}/chunk{i}.wav', 'rb') as f:
                transcript = openai.Audio.transcribe("whisper-2", file=f)
                transcript_file.write(transcript['text'])

        db, session = get_db_unyield()
        collection = db[settings.COLLECTION_NAME]

        result = collection.update_one(
            {'_id': file_id},
            {'$set': {'transcribed': True}}
        )

        os.rmdir(audio_dir)

        session.end_session()
        print(f'[*] Transcription complete for video {file_id}')
    except Exception as err:
        print(f"[*] Unable to process video {file_id}")
        # print(err)


def main():
    channel = get_channel_unyield()
    channel.queue_declare(queue=settings.TRANSCRIBE_QUEUE, durable=True)

    channel.basic_consume(
        queue=settings.TRANSCRIBE_QUEUE,
        auto_ack=True,
        on_message_callback=transcribe
    )

    print(' [*] Waiting for transcription jobs. To exit press CTRL+C')

    channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
