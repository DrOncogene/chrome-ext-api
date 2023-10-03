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
    """
    creates 24MB chunks of audio from audio_file 
    saving them in audio_path

    :param audio_path: path to save audio chunks
    :param audio_file: path to audio file

    :return: total number of chunks
    """
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
    """
    transcription callback to consume from TRANSCRIBE_QUEUE
    extract audio from video, create 24MB chunks and transcribe
    via openai whisper api
    """

    try:
        file_id = json.loads(body).get('file_id')
        audio_dir = f'{settings.AUDIO_DIR}/{file_id}'
        audio_file = f'{audio_dir}/{file_id}.wav'
        video_path = f'{settings.SAVE_DIR}/{file_id}.mp4'

        os.makedirs(audio_dir, mode=0o771, exist_ok=True)

        # ffmpeg.input(f'{settings.SAVE_DIR}/{file_id}.mp4'
        #              ).output(audio_file).run()

        audio = mp.VideoFileClip(video_path).audio

        if audio is None:
            print(f'no audio in video {video_path}')
            return

        audio.write_audiofile(audio_file)

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

        os.rmdir(audio_dir)  # remove audio chunks

        session.end_session()
        print(f'[*] Transcription complete for video {video_path}')
    except Exception as err:
        print(err)
        print(f"[*] Unable to process video {file_id}")


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
        print('TRANSCRIPTION SERVICE STOPPED ❌')
        try:
            exit(0)
        except SystemExit:
            os._exit(0)
