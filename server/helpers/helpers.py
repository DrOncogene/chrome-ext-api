import ffmpeg

from pydub import AudioSegment


def combine_chunks(chunks: list[str], output: str) -> bool:
    """
    combines chunks of video into a single video

    :param `chunks`: list of paths to chunks
    :param `output`: path to save combined video

    :return: True if successful, False otherwise
    """
    if len(chunks) < 1:
        return False

    try:
        (
            ffmpeg.input(f'concat:{"|".join(chunks)}', f="webm", v="error")
            .output(output, crf=18, preset="veryfast", strict="experimental", v="error")
            .run(overwrite_output=True)
        )

        return True
    except Exception as err:
        from consumers.merger import logger

        logger.err(str(err))
        return False


def make_audio_chuncks(audio_path: str, audio_file: str) -> int:
    """
    creates 24MB chunks of audio from audio_file
    saving them in audio_path

    :param `audio_path`: path to save audio chunks
    :param `audio_file`: path to audio file

    :return: total number of chunks
    """

    chunk_size = 24 * 1024 * 1024

    audio: AudioSegment = AudioSegment.from_file(audio_file)

    i = 0
    while len(audio) > 0:
        # 24mb chunk in milliseconds
        size_ms = int(chunk_size / ((audio.frame_rate / 1000) * audio.frame_width))

        # if < 24mb, use its length
        size_ms = min(size_ms, len(audio))
        chunk = audio[:size_ms]
        audio = audio[size_ms:]

        chunk.export(f"{audio_path}/chunk_{i}.mp3", format="mp3")

        i += 1

    return i


async def format_videos(videos: list[dict]) -> list[dict]:
    """
    refactors a list of videos
    """
    new_videos = []
    for video in videos:
        name = video.get("name")
        if not bool(name):
            name = str(video.get("_id"))
        new_videos.append(
            {
                "id": str(video.get("_id")),
                "name": name,
                "file_type": video.get("file_type"),
                "url": video.get("file_loc"),
                "uploaded": video.get("uploaded"),
                "completed": video.get("completed"),
                "transcribed": video.get("transcribed"),
                "created_at": video.get("created_at").isoformat(),
            }
        )

    return new_videos
