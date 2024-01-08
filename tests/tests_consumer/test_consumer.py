from asyncio import Event, ensure_future, gather, sleep
from typing import Any

import pytest
from asyncpg import Connection

from aiven.consumer.worker import start_workers
from aiven.db.crud import create_next_task

GET_TASKS = """
SELECT * FROM task;
"""

GET_TASKS_RESULT = """
SELECT * FROM task_result;
"""


@pytest.mark.usefixtures("_create_tables", "web_client")
@pytest.mark.parametrize(
    ("rows", "amount_of_workers", "endpoints", "expected_task", "expected_task_result"),
    [
        (
            [
                (
                    "http://127.0.0.1:8080/test/",
                    None,
                ),
            ],
            2,
            [
                (
                    "get",
                    "/test/",
                    {"Content-type": "application/text", "Accept": "application/text"},
                    "test.com",
                    200,
                ),
            ],
            [{"id": 1, "regex": None, "status": 2, "url": "http://127.0.0.1:8080/test/"}],
            [
                {
                    "error_text": "",
                    "regex_is_found": False,
                    "regex_result": "",
                    "status_code": 200,
                    "task_id": 1,
                    "url": "http://127.0.0.1:8080/test/",
                },
            ],
        ),
        (
            [
                (
                    "http://127.0.0.1:8080/non_existent_path/",
                    None,
                ),
            ],
            2,
            [
                (
                    "get",
                    "/test/",
                    {"Content-type": "application/text", "Accept": "application/text"},
                    "test.com",
                    200,
                ),
            ],
            [{"id": 1, "regex": None, "status": 2, "url": "http://127.0.0.1:8080/non_existent_path/"}],
            [
                {
                    "error_text": (
                        "ClientResponseError: 404, message='Not Found', "
                        "url=URL('http://127.0.0.1:8080/non_existent_path/')"
                    ),
                    "regex_is_found": False,
                    "regex_result": "",
                    "status_code": 404,
                    "task_id": 1,
                    "url": "http://127.0.0.1:8080/non_existent_path/",
                },
            ],
        ),
        (
            [
                (
                    "http://127.0.0.1:8080/test/",
                    "test",
                ),
            ],
            2,
            [
                (
                    "get",
                    "/test/",
                    {"Content-type": "application/text", "Accept": "application/text"},
                    "test.com",
                    200,
                ),
            ],
            [{"id": 1, "regex": "test", "status": 2, "url": "http://127.0.0.1:8080/test/"}],
            [
                {
                    "error_text": "",
                    "regex_is_found": True,
                    "regex_result": "test",
                    "status_code": 200,
                    "task_id": 1,
                    "url": "http://127.0.0.1:8080/test/",
                },
            ],
        ),
        (
            [
                (
                    "http://127.0.0.1:8080/test/",
                    "test",
                ),
            ],
            2,
            [
                (
                    "get",
                    "/test/",
                    {"Content-type": "application/text", "Accept": "application/text"},
                    "test.com",
                    500,
                ),
            ],
            [{"id": 1, "regex": "test", "status": 2, "url": "http://127.0.0.1:8080/test/"}],
            [
                {
                    "error_text": (
                        "ClientResponseError: 500, message='Internal Server Error', "
                        "url=URL('http://127.0.0.1:8080/test/')"
                    ),
                    "regex_is_found": False,
                    "regex_result": "",
                    "status_code": 500,
                    "task_id": 1,
                    "url": "http://127.0.0.1:8080/test/",
                },
            ],
        ),
    ],
)
async def test_consumer(
    db_connection: Connection,
    rows: list[tuple[str, str | None]],
    amount_of_workers: int,
    expected_task: dict[str, Any],
    expected_task_result: dict[str, Any],
) -> None:
    for row in rows:
        url, regex = row
        await create_next_task(db_connection, url, regex)

    stop_event = Event()
    tasks = [ensure_future(start_workers(amount_of_workers, stop_event))]
    await sleep(1)
    stop_event.set()
    await gather(*tasks)

    result = []
    for row in await db_connection.fetch(GET_TASKS):
        row_result = dict(row)
        del row_result["created_at"]
        result.append(row_result)

    assert sorted(result, key=lambda x: x["id"]) == expected_task

    result = []
    for row in await db_connection.fetch(GET_TASKS_RESULT):
        row_result = dict(row)
        del row_result["timestamp"]
        del row_result["response_time"]
        del row_result["id"]
        result.append(row_result)

    assert sorted(result, key=lambda x: x["url"]) == expected_task_result
