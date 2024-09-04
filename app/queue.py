from pika import BlockingConnection, ConnectionParameters
from pika.channel import Channel

from app.settings import settings


def get_channel() -> Channel:
    connection = BlockingConnection(
        ConnectionParameters(host=settings.RABBITMQ_HOST,
                             port=settings.RABBITMQ_PORT))
    try:
        channel = connection.channel()
        channel.basic_qos(prefetch_count=1)
        yield channel
    finally:
        connection.close()


def get_channel_unyield() -> Channel:
    connection = BlockingConnection(
        ConnectionParameters(host=settings.RABBITMQ_HOST,
                             port=settings.RABBITMQ_PORT))

    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)

    return channel
