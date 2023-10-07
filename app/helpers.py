import ffmpeg

from pydub import AudioSegment


def combine_chunks(chunks: list[str], output: str) -> bool:
    """
    combines chunks of video into a single video

    :param `chunks`: list of paths to chunks
    :param `output`: path to save combined video

    :return: True if successful, False otherwise
    """
    try:
        (
            ffmpeg
            .input(f'concat:{"|".join(chunks)}', f='webm', v='error')
            .output(output, crf=18, preset='veryfast',
                    strict='experimental', v='error')
            .run(overwrite_output=True)
        )

        return True
    except Exception as err:
        print(err)
        return False


def make_audio_chuncks(audio_path: str, audio_file: str) -> int:
    """
    creates 24MB chunks of audio from audio_file
    saving them in audio_path

    :param `audio_path`: path to save audio chunks
    :param `audio_file`: path to audio file

    :return: total number of chunks
    """

    print('creating audio chunks..')
    chunk_size = 24 * 1024 * 1024

    audio: AudioSegment = AudioSegment.from_file(audio_file)

    i = 0
    while len(audio) > 0:
        # calculate length of 24mb chunk in milliseconds
        size_ms = int(
            chunk_size / ((audio.frame_rate / 1000) * audio.frame_width))

        # if audio is less than 24mb, use its length
        size_ms = min(size_ms, len(audio))

        chunk = audio[:size_ms]

        audio = audio[size_ms:]

        chunk.export(f'{audio_path}/chunk_{i}.mp3', format='mp3')

        i += 1

    return i
