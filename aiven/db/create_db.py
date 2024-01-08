# flake8: noqa: B950

import asyncio

from aiven.db.db import get_db_connection
from conf.config import settings

CREATE_URL_TABLE = f"""
CREATE TABLE IF NOT EXISTS url
(
    id             SERIAL PRIMARY KEY,
    url            VARCHAR(255) NOT NULL,
    regex          VARCHAR(255),
    period         SMALLINT NOT NULL DEFAULT {settings.MIN_PERIOD} CHECK (period >= {settings.MIN_PERIOD} AND period <= {settings.MAX_PERIOD}),
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_run_at    TIMESTAMPTZ,
    UNIQUE NULLS NOT DISTINCT (url, regex)
);

CREATE INDEX IF NOT EXISTS url__url__idx ON url (url);
"""


CREATE_TASK_QUEUE_TABLE = """
CREATE TABLE IF NOT EXISTS task
(
    id          SERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status      INTEGER NOT NULL DEFAULT 0,
    url         VARCHAR(255) NOT NULL,
    regex       VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS task__url__idx ON task (url);
"""


CREATE_TASK_RESULT_TABLE = """
CREATE TABLE IF NOT EXISTS task_result
(
    id              SERIAL PRIMARY KEY,
    task_id         INT,
    url             VARCHAR(255) NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    response_time   FLOAT,
    status_code     SMALLINT NOT NULL DEFAULT 0,
    error_text      TEXT,
    regex_is_found  BOOLEAN DEFAULT TRUE,
    regex_result    TEXT,
    CONSTRAINT fk_task FOREIGN KEY(task_id) REFERENCES task(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS task_result__url__idx ON task_result (url);
"""


async def create_tables() -> None:
    async with get_db_connection() as connection:
        async with connection.transaction():
            await connection.execute(CREATE_URL_TABLE)
            await connection.execute(CREATE_TASK_QUEUE_TABLE)
            await connection.execute(CREATE_TASK_RESULT_TABLE)


async def main() -> None:
    await create_tables()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    loop.close()
