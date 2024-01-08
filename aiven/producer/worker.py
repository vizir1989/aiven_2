import asyncio
import logging
from asyncio import Event, ensure_future, gather, sleep

from asyncpg import InterfaceError, Pool, PostgresError

from aiven.db.crud import create_next_task, get_next_url, update_last_run_at
from aiven.db.db import get_db_pool
from conf.config_producer import settings

logger = logging.getLogger(__name__)


async def start_worker(stop_event: Event, pool: Pool) -> None:
    async with pool.acquire() as connection:
        while not stop_event.is_set():
            try:
                async with connection.transaction():
                    next_url = await get_next_url(connection)
                    if next_url:
                        url_id, url, regex = next_url
                        logger.info("Create task. url: %s, regex: %s", (url, regex))
                        await create_next_task(connection, url, regex)
                        await update_last_run_at(connection, url_id)

                if not next_url:
                    await sleep(settings.SLEEP_WITHOUT_TASK)

            except (PostgresError, InterfaceError, asyncio.TimeoutError):
                logger.exception("Exception in producer")
                # TODO: Circuit breaker design pattern
                # (https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern#:~:text=Circuit%20breaker%20is%20a%20design,failure%20or%20unexpected%20system%20difficulties.)
                await sleep(settings.SLEEP_AFTER_EXCEPTION)
                # TODO: add slack/email notification


async def start_workers(max_workers: int, stop_event: Event | None = None) -> None:
    logger.info("Start producer with %s workers", max_workers)
    if not stop_event:
        stop_event = Event()

    try:
        async with get_db_pool() as pool:
            tasks = [ensure_future(start_worker(stop_event, pool)) for _ in range(max_workers)]
            await gather(*tasks)
    except (PostgresError, InterfaceError, asyncio.TimeoutError):
        logger.exception("Can't start producer's workers")
