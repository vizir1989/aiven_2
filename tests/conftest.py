import importlib
from collections.abc import Callable, Generator
from functools import partial
from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch
from aiohttp import web
from aiohttp.pytest_plugin import AiohttpClient
from aiohttp.test_utils import TestClient, TestServer
from aiohttp.web_response import Response
from asyncpg import Connection, Pool
from pytest_postgresql import factories
from pytest_postgresql.executor import PostgreSQLExecutor
from pytest_postgresql.janitor import DatabaseJanitor

from aiven.db.create_db import create_tables
from aiven.db.crud import get_next_url
from aiven.db.db import get_db_pool

test_db = factories.postgresql_proc()


class RaiseExceptionFunction:
    def __init__(self, func: Callable, exception: type[Exception], amount_of_exception: int) -> None:
        self.__amount_of_exception = amount_of_exception
        self.__func = func
        self.__exception = exception

    async def __call__(self, *args: int, **kwargs: str) -> Any:
        if self.__amount_of_exception == 0:
            return await self.__func(*args, **kwargs)
        else:
            self.__amount_of_exception -= 1
            raise self.__exception


@pytest.fixture()
async def db_pool(test_db: PostgreSQLExecutor) -> Pool:
    """Session for SQLAlchemy."""
    pg_host = test_db.host
    pg_port = test_db.port
    pg_user = test_db.user
    pg_password = test_db.password
    pg_db = test_db.dbname

    with DatabaseJanitor(pg_user, pg_host, pg_port, pg_db, test_db.version, pg_password):
        async with get_db_pool() as pool:
            yield pool


@pytest.fixture()
async def db_connection(db_pool: Pool) -> Connection:
    """Session for SQLAlchemy."""
    async with db_pool.acquire() as connection:
        yield connection


@pytest.fixture()
async def _create_tables(db_connection: Connection) -> None:
    await create_tables()


@pytest.fixture()
async def _mock_get_new_url_with_exception(
    monkeypatch: MonkeyPatch,
    exception: type[Exception],
    amount_of_exception: int,
) -> None:
    monkeypatch.setattr(
        "aiven.db.crud.get_next_url",
        RaiseExceptionFunction(get_next_url, exception, amount_of_exception),
    )
    import aiven.consumer.worker
    import aiven.producer.worker

    importlib.reload(aiven.producer.worker)
    importlib.reload(aiven.consumer.worker)
    yield
    monkeypatch.setattr("aiven.db.crud.get_next_url", get_next_url)
    importlib.reload(aiven.producer.worker)
    importlib.reload(aiven.consumer.worker)


@pytest.fixture()
async def web_client(
    aiohttp_client: AiohttpClient,
    endpoints: list[tuple[str, str, dict[str, str], str, int]],
) -> Generator[TestClient, None, None]:
    app = web.Application()

    for item in endpoints:
        type_request, endpoint, headers, response, status_code = item

        async def my_response(headers: dict, response: str, status_code: int, request: Any) -> Response:
            return web.Response(body=response, headers=headers, status=status_code)

        my_func = partial(my_response, headers, response, status_code)
        getattr(app.router, f"add_{type_request}")(endpoint, my_func)

    client = TestClient(TestServer(app, host="127.0.0.1", port=8080))
    await client.start_server()
    yield client
    await client.close()
