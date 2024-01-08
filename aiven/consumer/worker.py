import asyncio
import logging
import re
import time
from asyncio import Event, ensure_future, gather, sleep

from aiohttp import ClientError, ClientSession, ClientTimeout
from asyncpg import InterfaceError, Pool, PostgresError

from aiven.db.crud import TaskResult, finish_task, get_next_task, set_result
from aiven.db.db import get_db_pool
from conf.config_consumer import settings

logger = logging.getLogger(__name__)


async def fetch_url(session: ClientSession, task_id: int, url: str, regex: str | None) -> TaskResult:
    logger.info("fetch url: %s, regex: %s", (url, regex))
    start_time = time.time()
    status_code = 0
    error_text = ""
    regex_is_found = False
    regex_result_str = ""

    try:
        async with session.get(url, allow_redirects=True) as resp:
            status_code = resp.status
            resp.raise_for_status()
            resp_text = await resp.text()
            if regex:
                regex_result = re.findall(regex, resp_text)
                if regex_result:
                    regex_is_found = True

                regex_result_str = "; ".join(regex_result)
    except (ClientError, TimeoutError) as e:
        error_text = f"{type(e).__name__}: {str(e)}"

    end_time = time.time()
    response_time = end_time - start_time
    return TaskResult(
        task_id=task_id,
        url=url,
        response_time=response_time,
        status_code=status_code,
        error_text=error_text,
        regex_is_found=regex_is_found,
        regex_result=regex_result_str,
    )


async def start_worker(stop_event: Event, pool: Pool) -> None:
    timeout = ClientTimeout(total=settings.HTTP_REQUEST_TIMEOUT)
    async with ClientSession(timeout=timeout) as session:
        try:
            async with pool.acquire() as connection:
                while not stop_event.is_set():
                    async with connection.transaction():
                        next_task = await get_next_task(connection)
                        if next_task:
                            task_id, url, regex = next_task
                            logger.info("Get new task. url: %s, regex: %s", (url, regex))
                            result = await fetch_url(session, task_id, url, regex)
                            await finish_task(connection, task_id)
                            await set_result(connection, result)

                    if not next_task:
                        await sleep(settings.SLEEP_WITHOUT_TASK)

        except (PostgresError, InterfaceError, asyncio.TimeoutError):
            logger.exception("Exception in consumer")
            # TODO: Circuit breaker design pattern
            # (https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern#:~:text=Circuit%20breaker%20is%20a%20design,failure%20or%20unexpected%20system%20difficulties.)
            await sleep(settings.SLEEP_AFTER_EXCEPTION)
            # TODO: add slack/email notification


async def start_workers(max_workers: int, stop_event: Event | None = None) -> None:
    logger.info("Start consumer with %s workers", max_workers)
    if not stop_event:
        stop_event = Event()

    try:
        async with get_db_pool() as pool:
            tasks = [ensure_future(start_worker(stop_event, pool)) for _ in range(max_workers)]
            await gather(*tasks)
    except (PostgresError, InterfaceError, asyncio.TimeoutError):
        logger.exception("Can't start consumer's workers")
