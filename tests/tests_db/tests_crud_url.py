import datetime
from asyncio import ensure_future, gather
from asyncio import sleep as asleep
from time import sleep
from typing import Any

import pytest
from asyncpg import CheckViolationError, Connection, Pool, UniqueViolationError

from aiven.db.crud import (
    create_new_url,
    get_next_url,
    remove_url_by_url,
    remove_url_by_url_and_regex,
    update_last_run_at,
)
from conf.config import settings

GET_URLS = """
SELECT * FROM url;
"""


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("url", "period", "regex", "expected_result"),
    [
        (
            "https://test.com",
            15,
            ".*",
            [{"id": 1, "last_run_at": None, "period": 15, "regex": ".*", "url": "https://test.com"}],
        ),
    ],
)
async def test_create_new_url(
    db_connection: Connection,
    url: str,
    period: int,
    regex: str,
    expected_result: list[dict],
) -> None:
    await create_new_url(db_connection, url, period, regex)
    result = []
    for row in await db_connection.fetch(GET_URLS):
        row_result = dict(row)
        del row_result["created_at"]
        result.append(row_result)

    assert result == expected_result


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "expected_exception"),
    [
        (
            [
                (
                    "https://test.com",
                    15,
                    None,
                ),
                (
                    "https://test.com",
                    15,
                    None,
                ),
            ],
            UniqueViolationError,
        ),
        (
            [
                (
                    "https://test.com",
                    settings.MIN_PERIOD - 1,
                    None,
                ),
            ],
            CheckViolationError,
        ),
        (
            [
                (
                    "https://test.com",
                    settings.MAX_PERIOD + 1,
                    None,
                ),
            ],
            CheckViolationError,
        ),
    ],
)
async def test_create_new_url_with_exception(
    db_connection: Connection,
    rows: list[tuple[str, int, str]],
    expected_exception: type[Exception],
) -> None:
    with pytest.raises(expected_exception):  # noqa: PT012
        for row in rows:
            url, period, regex = row
            await create_new_url(db_connection, url, period, regex)


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "delete_url", "expected_result"),
    [
        (
            [
                (
                    "https://test.com",
                    15,
                    None,
                ),
                (
                    "https://test.com",
                    15,
                    ".*",
                ),
                (
                    "https://test1.com",
                    15,
                    ".*",
                ),
            ],
            "https://test1.com",
            [
                {"id": 1, "last_run_at": None, "period": 15, "regex": None, "url": "https://test.com"},
                {"id": 2, "last_run_at": None, "period": 15, "regex": ".*", "url": "https://test.com"},
            ],
        ),
        (
            [
                (
                    "https://test.com",
                    15,
                    None,
                ),
                (
                    "https://test.com",
                    15,
                    ".*",
                ),
                (
                    "https://test1.com",
                    15,
                    ".*",
                ),
            ],
            "https://test.com",
            [{"id": 3, "last_run_at": None, "period": 15, "regex": ".*", "url": "https://test1.com"}],
        ),
    ],
)
async def test_remove_url(
    db_connection: Connection,
    rows: list[tuple[str, int, str]],
    delete_url: str,
    expected_result: list[dict[str, Any]],
) -> None:
    for row in rows:
        url, period, regex = row
        await create_new_url(db_connection, url, period, regex)

    await remove_url_by_url(db_connection, delete_url)

    result = []
    for row in await db_connection.fetch(GET_URLS):
        row_result = dict(row)
        del row_result["created_at"]
        result.append(row_result)

    assert result == expected_result


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "delete_url", "delete_regex", "expected_result"),
    [
        (
            [
                (
                    "https://test.com",
                    15,
                    None,
                ),
                (
                    "https://test.com",
                    15,
                    "test",
                ),
                (
                    "https://test1.com",
                    15,
                    "test1",
                ),
            ],
            "https://test1.com",
            "test1",
            [
                {"id": 1, "last_run_at": None, "period": 15, "regex": None, "url": "https://test.com"},
                {"id": 2, "last_run_at": None, "period": 15, "regex": "test", "url": "https://test.com"},
            ],
        ),
        (
            [
                (
                    "https://test.com",
                    15,
                    "test",
                ),
                (
                    "https://test.com",
                    15,
                    "test1",
                ),
            ],
            "https://test.com",
            "test",
            [{"id": 2, "last_run_at": None, "period": 15, "regex": "test1", "url": "https://test.com"}],
        ),
    ],
)
async def test_remove_url_with_regex(
    db_connection: Connection,
    rows: list[tuple[str, int, str]],
    delete_url: str,
    delete_regex: str,
    expected_result: list[dict[str, Any]],
) -> None:
    for row in rows:
        url, period, regex = row
        await create_new_url(db_connection, url, period, regex)

    await remove_url_by_url_and_regex(db_connection, delete_url, delete_regex)

    result = []
    for row in await db_connection.fetch(GET_URLS):
        row_result = dict(row)
        del row_result["created_at"]
        result.append(row_result)

    assert result == expected_result


@pytest.mark.freeze_time("2024-01-01T00:00:00.000Z")
@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "url_id", "expected_result"),
    [
        (
            [
                (
                    "https://test.com",
                    15,
                    None,
                ),
                (
                    "https://test.com",
                    15,
                    ".*",
                ),
                (
                    "https://test1.com",
                    15,
                    ".*",
                ),
            ],
            1,
            [
                {"id": 2, "last_run_at": None, "period": 15, "regex": ".*", "url": "https://test.com"},
                {"id": 3, "last_run_at": None, "period": 15, "regex": ".*", "url": "https://test1.com"},
                {
                    "id": 1,
                    "last_run_at": datetime.datetime(2024, 1, 1, 0, 0, tzinfo=datetime.timezone.utc),
                    "period": 15,
                    "regex": None,
                    "url": "https://test.com",
                },
            ],
        ),
    ],
)
async def test_update_last_run_at(
    db_connection: Connection,
    rows: list[tuple[str, int, str]],
    url_id: int,
    expected_result: list[dict[str, Any]],
) -> None:
    for row in rows:
        url, period, regex = row
        await create_new_url(db_connection, url, period, regex)

    await update_last_run_at(db_connection, url_id)

    result = []
    for row in await db_connection.fetch(GET_URLS):
        row_result = dict(row)
        del row_result["created_at"]
        result.append(row_result)

    assert result == expected_result


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "sleep_time", "expected_result_1", "expected_result_2"),
    [
        (
            [
                (
                    "https://test.com",
                    5,
                    None,
                ),
            ],
            0,
            {"id": 1, "regex": None, "url": "https://test.com"},
            None,
        ),
        (
            [
                (
                    "https://test.com",
                    5,
                    None,
                ),
            ],
            6,
            {"id": 1, "regex": None, "url": "https://test.com"},
            {"id": 1, "regex": None, "url": "https://test.com"},
        ),
    ],
)
async def test_get_next_url(
    db_connection: Connection,
    rows: list[tuple[str, int, str]],
    sleep_time: int,
    expected_result_1: dict[str, Any],
    expected_result_2: dict[str, Any],
) -> None:
    for row in rows:
        url, period, regex = row
        await create_new_url(db_connection, url, period, regex)

    result = dict(await get_next_url(db_connection))
    assert result == expected_result_1

    await update_last_run_at(db_connection, 1)

    sleep(sleep_time)

    if next_url := await get_next_url(db_connection):
        result = dict(next_url)
    else:
        result = None

    assert result == expected_result_2


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "expected_result"),
    [
        (
            [
                (
                    "https://test.com",
                    5,
                    None,
                ),
            ],
            [{"id": 1, "regex": None, "url": "https://test.com"}, None],
        ),
    ],
)
async def test_get_next_url_with_2_workers(
    db_pool: Pool,
    rows: list[tuple[str, int, str | None]],
    expected_result: dict[str, Any],
) -> None:
    async with db_pool.acquire() as connection:
        for row in rows:
            url, period, regex = row
            await create_new_url(connection, url, period, regex)

    async def fetch_next_url(db_pool: Pool) -> dict | None:
        async with db_pool.acquire() as connection:
            async with connection.transaction():
                result = None
                if next_url := await get_next_url(connection):
                    result = dict(next_url)

                await asleep(1)
                return result

    tasks = [ensure_future(fetch_next_url(db_pool)) for _ in range(2)]
    result = await gather(*tasks)

    assert expected_result == result
