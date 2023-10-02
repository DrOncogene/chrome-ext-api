import cv2
import numpy as np

from app.settings import settings


def generate_link(collection: str, file_id: str) -> str:
    """generates a link to a video"""

    return f'{settings.SERVER_URL}/videos/{collection}/{file_id}'


def combine_chunks_to_video(chunks: list[str], output_path: str):
    # Get a list of chunk files in the directory

    chunk_data = []
    for chunk_file in chunks:
        with open(chunk_file, 'rb') as file:
            chunk_data.append(file.read())

    # Combine the binary chunks
    video_data = b''.join(chunk_data)
    print(len(video_data))

    # Define frame width, height, and frame rate
    frame_width = 640
    frame_height = 480
    frame_rate = 30.0
    channel = 3  # Assuming 3 channels (e.g., RGB)

    # Create a VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # codec
    writer = cv2.VideoWriter(output_path, fourcc,
                             frame_rate, (frame_width, frame_height))

    # Initialize variables for tracking frame position
    frame_pos = 0
    frame_size = frame_width * frame_height * channel

    # Read frames from the video data and write them to the output video
    while frame_pos < len(video_data):
        frame_data = video_data[frame_pos:frame_pos + frame_size]
        if len(frame_data) != frame_size:
            #  Add padding at the end of the last frame
            padding = frame_size - len(frame_data)
            frame_data += b'\x00' * padding

        # Reshape frame data and write it to the video
        frame = np.frombuffer(frame_data, dtype=np.uint8).reshape(
            frame_height, frame_width, 3)
        writer.write(frame)
        frame_pos += frame_size

    # Release the VideoWriter and close the video file
    writer.release()
