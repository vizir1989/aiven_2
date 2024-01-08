from collections.abc import Generator
from contextlib import asynccontextmanager

import asyncpg
from asyncpg import Connection, Pool

from conf.config import settings


@asynccontextmanager
async def get_db_pool() -> Generator[Pool, None, None]:
    pool = await asyncpg.create_pool(
        dsn=settings.DB_DSN,
        command_timeout=settings.DB_TIMEOUT,
    )

    yield pool

    await pool.close()


@asynccontextmanager
async def get_db_connection() -> Generator[Connection, None, None]:
    connection = await asyncpg.connect(
        dsn=settings.DB_DSN,
        timeout=settings.DB_TIMEOUT,
        command_timeout=settings.DB_TIMEOUT,
    )

    yield connection

    await connection.close()
