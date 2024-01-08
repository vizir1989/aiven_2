from asyncio import Event, ensure_future, gather, sleep
from typing import Any

import pytest
from asyncpg import Connection, PostgresError

from aiven.db.crud import create_new_url
from aiven.producer.worker import start_workers
from conf.config_producer import settings

GET_TASKS = """
SELECT * FROM task;
"""


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "amount_of_workers", "expected_result"),
    [
        (
            [
                (
                    "https://test.com",
                    5,
                    None,
                ),
            ],
            2,
            [{"regex": None, "status": 0, "url": "https://test.com"}],
        ),
        (
            [
                (
                    "https://test.com",
                    5,
                    None,
                ),
                (
                    "https://test1.com",
                    5,
                    None,
                ),
            ],
            2,
            [
                {"regex": None, "status": 0, "url": "https://test.com"},
                {"regex": None, "status": 0, "url": "https://test1.com"},
            ],
        ),
    ],
)
async def test_producer(
    db_connection: Connection,
    rows: list[tuple[str, int, str | None]],
    amount_of_workers: int,
    expected_result: dict[str, Any],
) -> None:
    for row in rows:
        url, period, regex = row
        await create_new_url(db_connection, url, period, regex)

    stop_event = Event()
    tasks = [ensure_future(start_workers(amount_of_workers, stop_event))]
    await sleep(1)
    stop_event.set()
    await gather(*tasks)

    result = []
    for row in await db_connection.fetch(GET_TASKS):
        row_result = dict(row)
        del row_result["created_at"]
        del row_result["id"]
        result.append(row_result)

    assert sorted(result, key=lambda x: x["url"]) == expected_result


@pytest.mark.usefixtures("_create_tables", "_mock_get_new_url_with_exception")
@pytest.mark.parametrize(
    ("rows", "sleep_time", "amount_of_workers", "exception", "amount_of_exception", "expected_result"),
    [
        (
            [
                (
                    "https://test.com",
                    5,
                    None,
                ),
                (
                    "https://test1.com",
                    5,
                    None,
                ),
            ],
            settings.SLEEP_AFTER_EXCEPTION - 1 + 0.1,
            2,
            PostgresError,
            2,
            [],
        ),
        (
            [
                (
                    "https://test.com",
                    5,
                    None,
                ),
                (
                    "https://test1.com",
                    5,
                    None,
                ),
            ],
            settings.SLEEP_AFTER_EXCEPTION + 1,
            2,
            PostgresError,
            2,
            [
                {"regex": None, "status": 0, "url": "https://test.com"},
                {"regex": None, "status": 0, "url": "https://test1.com"},
            ],
        ),
    ],
)
async def test_producer_with_db_exception(
    db_connection: Connection,
    rows: list[tuple[str, int, str | None]],
    sleep_time: float,
    amount_of_workers: int,
    expected_result: dict[str, Any],
) -> None:
    for row in rows:
        url, period, regex = row
        await create_new_url(db_connection, url, period, regex)

    stop_event = Event()
    tasks = [ensure_future(start_workers(amount_of_workers, stop_event))]
    await sleep(sleep_time)
    stop_event.set()
    await gather(*tasks)

    result = []
    for row in await db_connection.fetch(GET_TASKS):
        row_result = dict(row)
        del row_result["created_at"]
        del row_result["id"]
        result.append(row_result)

    assert sorted(result, key=lambda x: x["url"]) == expected_result
