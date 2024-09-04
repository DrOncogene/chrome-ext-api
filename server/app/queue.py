from aio_pika import connect_robust
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel
from aio_pika.pool import Pool

from app.settings import settings


async def get_connection() -> AbstractRobustConnection:
    conn = await connect_robust(settings.RABBITMQ_URL)
    return conn


async def get_channel(pool: Pool) -> AbstractRobustChannel:
    async with pool.acquire() as conn:
        return await conn.channel()


async def channel_setup(pool: Pool) -> None:
    async with pool.acquire() as ch:
        await ch.set_qos(prefetch_count=1)
        await ch.declare_queue(name=settings.VIDEO_QUEUE, durable=True)
        await ch.declare_queue(name=settings.TRANSCRIBE_QUEUE, durable=True)


connection_pool = Pool(get_connection, max_size=3)
channel_pool = Pool(get_channel, connection_pool, max_size=3)
