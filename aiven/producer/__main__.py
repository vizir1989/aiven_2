import asyncio

from aiven.producer.worker import start_workers
from conf.config_producer import settings

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_workers(settings.CONCURRENCY))
    loop.close()
