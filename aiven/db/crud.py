from dataclasses import astuple, dataclass
from datetime import datetime, timezone

from asyncpg import Connection, Record

CREATE_NEW_URL = """
INSERT INTO url (url, period, regex) VALUES ($1, $2, $3) RETURNING id;
"""

GET_NEXT_URL = """
SELECT id, url, regex FROM url
    WHERE last_run_at IS NULL OR last_run_at + INTERVAL '1 sec' * url.period < localtimestamp
    ORDER BY id
    LIMIT 1
    for update skip locked;
"""


CREATE_NEXT_TASK = """
INSERT INTO task (url, regex) VALUES ($1, $2) RETURNING id;
"""


GET_NEXT_TASK = """
WITH next_task AS (
    SELECT id, url, regex FROM task
    WHERE status = 0
    ORDER BY id
    LIMIT 1
    FOR UPDATE skip locked
)
UPDATE task
SET
    status = 1
FROM next_task
WHERE task.id = next_task.id
RETURNING task.id, task.url, task.regex;
"""

FINISH_TASK = """
UPDATE task
SET
    status = 2
WHERE id = $1;
"""


SET_RESULT = """
INSERT INTO task_result
    (task_id, url, status_code, response_time, error_text, regex_is_found, regex_result)
VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id;
"""

UPDATE_LAST_RUN_AT = """
UPDATE url SET
    last_run_at = $2
WHERE id = $1
"""


REMOVE_URL_BY_URL = """
DELETE FROM url
WHERE url = $1;
"""

REMOVE_URL_BY_URL_AND_REGEX = """
DELETE FROM url
WHERE url = $1 and regex = $2;
"""


@dataclass
class TaskResult:
    task_id: int
    url: str
    status_code: int
    response_time: float
    error_text: str
    regex_is_found: bool
    regex_result: str


async def create_next_task(connection: Connection, url: str, regex: str | None) -> None:
    await connection.execute(CREATE_NEXT_TASK, url, regex)


async def get_next_task(connection: Connection) -> Record:
    return await connection.fetchrow(GET_NEXT_TASK)


async def finish_task(connection: Connection, task_id: int) -> None:
    await connection.execute(FINISH_TASK, task_id)


async def set_result(connection: Connection, task_result: TaskResult) -> None:
    await connection.execute(SET_RESULT, *astuple(task_result))


async def create_new_url(connection: Connection, url: str, period: int, regex: str | None = None) -> None:
    await connection.execute(CREATE_NEW_URL, url, period, regex)


async def get_next_url(connection: Connection) -> Record:
    return await connection.fetchrow(GET_NEXT_URL)


async def update_last_run_at(connection: Connection, url_id: int) -> None:
    dt = datetime.now(timezone.utc)
    await connection.execute(UPDATE_LAST_RUN_AT, url_id, dt)


async def remove_url_by_url(connection: Connection, url: str) -> None:
    await connection.execute(REMOVE_URL_BY_URL, url)


async def remove_url_by_url_and_regex(connection: Connection, url: str, regex: str) -> None:
    await connection.execute(REMOVE_URL_BY_URL_AND_REGEX, url, regex)
