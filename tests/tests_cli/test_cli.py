from argparse import ArgumentTypeError
from typing import Any

import pytest
from asyncpg import Connection

from aiven.cli.aiven_cli import add_url, parser, remove_url
from aiven.db.crud import create_new_url

GET_URLS = """
SELECT * FROM url;
"""


@pytest.mark.parametrize(
    "args",
    [
        (
            [
                "add",
                "http://test.com",
                "-p 30",
                "-r .*",
            ],
        ),
        (
            [
                "add",
                "http://test.com",
                "--period",
                "30",
                "--regex",
                ".*",
            ],
        ),
        (
            [
                "remove",
                "http://test.com",
            ],
        ),
        (
            [
                "add",
                "http://test.com",
                "--regex",
                ".*",
            ],
        ),
    ],
)
def test_valid_args(args: list[str]) -> None:
    parser.parse_args(*args)


@pytest.mark.parametrize(
    "args",
    [
        (
            [
                "random_action",
                "http://test.com",
                "-p 30",
                "-r .*",
            ],
        ),
        (
            [
                "add",
                "test.com",
                "-p 30",
                "-r .*",
            ],
        ),
        (
            [
                "add",
                "http://test.com",
                "-p 1",
                "-r .*",
            ],
        ),
        (
            [
                "add",
                "http://test.com",
                "-p 15",
                "-r (.*",
            ],
        ),
    ],
)
def test_invalid_args(args: list[str]) -> None:
    with pytest.raises(SystemExit):
        parser.parse_args(*args)


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "new_url", "new_regex", "new_period", "expected_result"),
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
            "http://test2.com",
            None,
            15,
            [
                {"id": 1, "last_run_at": None, "period": 5, "regex": None, "url": "https://test.com"},
                {"id": 2, "last_run_at": None, "period": 5, "regex": None, "url": "https://test1.com"},
                {"id": 3, "last_run_at": None, "period": 15, "regex": None, "url": "http://test2.com"},
            ],
        ),
    ],
)
async def test_add_url(
    db_connection: Connection,
    rows: list[tuple[str, int, str | None]],
    new_url: str,
    new_regex: str,
    new_period: int,
    expected_result: dict[str, Any],
) -> None:
    for row in rows:
        url, period, regex = row
        await create_new_url(db_connection, url, period, regex)

    await add_url(new_url, new_period, new_regex)

    result = []
    for row in await db_connection.fetch(GET_URLS):
        row_result = dict(row)
        del row_result["created_at"]
        result.append(row_result)

    assert result == expected_result


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "new_url", "new_regex", "new_period"),
    [
        (
            [
                (
                    "http://test.com",
                    5,
                    None,
                ),
                (
                    "http://test1.com",
                    5,
                    None,
                ),
            ],
            "http://test.com",
            None,
            15,
        ),
        (
            [
                (
                    "http://test.com",
                    5,
                    None,
                ),
                (
                    "http://test1.com",
                    5,
                    None,
                ),
            ],
            "http://test2.com",
            None,
            1,
        ),
    ],
)
async def test_add_url_with_exception(
    db_connection: Connection,
    rows: list[tuple[str, int, str | None]],
    new_url: str,
    new_regex: str,
    new_period: int,
) -> None:
    for row in rows:
        url, period, regex = row
        await create_new_url(db_connection, url, period, regex)

    with pytest.raises(ArgumentTypeError):
        await add_url(new_url, new_period, new_regex)


@pytest.mark.usefixtures("_create_tables")
@pytest.mark.parametrize(
    ("rows", "delete_url", "delete_regex", "expected_result"),
    [
        (
            [
                (
                    "https://test.com",
                    5,
                    ".*",
                ),
                (
                    "https://test.com",
                    5,
                    None,
                ),
                (
                    "https://test.com",
                    5,
                    "test",
                ),
                (
                    "https://test1.com",
                    5,
                    None,
                ),
            ],
            "https://test.com",
            None,
            [{"id": 4, "last_run_at": None, "period": 5, "regex": None, "url": "https://test1.com"}],
        ),
        (
            [
                (
                    "https://test.com",
                    5,
                    ".*",
                ),
                (
                    "https://test.com",
                    5,
                    None,
                ),
                (
                    "https://test.com",
                    5,
                    "test",
                ),
                (
                    "https://test1.com",
                    5,
                    "test",
                ),
            ],
            "https://test.com",
            "test",
            [
                {"id": 1, "last_run_at": None, "period": 5, "regex": ".*", "url": "https://test.com"},
                {"id": 2, "last_run_at": None, "period": 5, "regex": None, "url": "https://test.com"},
                {"id": 4, "last_run_at": None, "period": 5, "regex": "test", "url": "https://test1.com"},
            ],
        ),
    ],
)
async def test_remove_url(
    db_connection: Connection,
    rows: list[tuple[str, int, str | None]],
    delete_url: str,
    delete_regex: str | None,
    expected_result: dict[str, Any],
) -> None:
    for row in rows:
        url, period, regex = row
        await create_new_url(db_connection, url, period, regex)

    await remove_url(delete_url, delete_regex)

    result = []
    for row in await db_connection.fetch(GET_URLS):
        row_result = dict(row)
        del row_result["created_at"]
        result.append(row_result)

    assert result == expected_result
