from asyncio import ensure_future, gather
from asyncio import sleep as asleep
from typing import Any

import pytest
from asyncpg import Connection, ForeignKeyViolationError, Pool

from aiven.db.crud import TaskResult, create_next_task, finish_task, get_next_task, set_result

GET_TASKS = """
SELECT * FROM task;
"""

GET_TASKS_RESULT = """
SELECT * FROM task_result;
"""


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("url", "regex", "expected_result"),
    [
        (
            "http://test.com",
            None,
            [{"id": 1, "regex": None, "status": 0, "url": "http://test.com"}],
        ),
    ],
)
async def test_create_next_task(
    db_connection: Connection,
    url: str,
    regex: str | None,
    expected_result: list[dict],
) -> None:
    await create_next_task(db_connection, url, regex)

    result = []
    for row in await db_connection.fetch(GET_TASKS):
        row_result = dict(row)
        del row_result["created_at"]
        result.append(row_result)

    assert result == expected_result


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "expected_result"),
    [
        (
            [
                (
                    "http://test.com",
                    None,
                ),
            ],
            [{"id": 1, "regex": None, "url": "http://test.com"}],
        ),
    ],
)
async def test_get_next_task(
    db_connection: Connection,
    rows: list[tuple[str, str]],
    expected_result: list[dict],
) -> None:
    for row in rows:
        url, regex = row
        await create_next_task(db_connection, url, regex)

    result = [dict(await get_next_task(db_connection))]

    assert result == expected_result


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "task_id", "expected_result"),
    [
        (
            [
                (
                    "http://test.com",
                    None,
                ),
            ],
            1,
            [{"id": 1, "regex": None, "status": 2, "url": "http://test.com"}],
        ),
    ],
)
async def test_finish_task(
    db_connection: Connection,
    rows: list[tuple[str, str]],
    task_id: int,
    expected_result: list[dict],
) -> None:
    for row in rows:
        url, regex = row
        await create_next_task(db_connection, url, regex)

    await finish_task(db_connection, task_id)

    result = []
    for row in await db_connection.fetch(GET_TASKS):
        row_result = dict(row)
        del row_result["created_at"]
        result.append(row_result)

    assert result == expected_result


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "task_result", "expected_result"),
    [
        (
            [
                (
                    "http://test.com",
                    None,
                ),
            ],
            TaskResult(
                task_id=1,
                url="http://test.com",
                status_code=0,
                response_time=1.1,
                error_text="",
                regex_is_found=True,
                regex_result="",
            ),
            [
                {
                    "error_text": "",
                    "id": 1,
                    "regex_is_found": True,
                    "regex_result": "",
                    "response_time": 1.1,
                    "status_code": 0,
                    "task_id": 1,
                    "url": "http://test.com",
                },
            ],
        ),
    ],
)
async def test_set_result(
    db_connection: Connection,
    rows: list[tuple[str, str]],
    task_result: TaskResult,
    expected_result: list[dict],
) -> None:
    for row in rows:
        url, regex = row
        await create_next_task(db_connection, url, regex)

    await set_result(db_connection, task_result)

    result = []
    for row in await db_connection.fetch(GET_TASKS_RESULT):
        row_result = dict(row)
        del row_result["timestamp"]
        result.append(row_result)

    assert result == expected_result


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "task_result", "exception"),
    [
        (
            [
                (
                    "http://test.com",
                    None,
                ),
            ],
            TaskResult(
                task_id=2,
                url="http://test.com",
                status_code=0,
                response_time=1.1,
                error_text="",
                regex_is_found=True,
                regex_result="",
            ),
            ForeignKeyViolationError,
        ),
    ],
)
async def test_set_result_with_exception(
    db_connection: Connection,
    rows: list[tuple[str, str]],
    task_result: TaskResult,
    exception: type[Exception],
) -> None:
    for row in rows:
        url, regex = row
        await create_next_task(db_connection, url, regex)

    with pytest.raises(exception):
        await set_result(db_connection, task_result)


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "expected_result"),
    [
        (
            [
                (
                    "https://test.com",
                    None,
                ),
            ],
            [{"id": 1, "regex": None, "url": "https://test.com"}, None],
        ),
        (
            [
                (
                    "https://test.com",
                    None,
                ),
                (
                    "https://test1.com",
                    None,
                ),
            ],
            [
                {"id": 1, "regex": None, "url": "https://test.com"},
                {"id": 2, "regex": None, "url": "https://test1.com"},
            ],
        ),
    ],
)
async def test_get_next_task_with_2_workers(
    db_pool: Pool,
    rows: list[tuple[str, str | None]],
    expected_result: dict[str, Any],
) -> None:
    async with db_pool.acquire() as connection:
        for row in rows:
            url, regex = row
            await create_next_task(connection, url, regex)

    async def _get_next_task(pool: Pool) -> dict | None:
        async with pool.acquire() as connection:
            async with connection.transaction():
                result = None
                if next_task := await get_next_task(connection):
                    result = dict(next_task)

                await asleep(1)
                return result

    tasks = [ensure_future(_get_next_task(db_pool)) for _ in range(2)]
    result = await gather(*tasks)

    assert result == expected_result
