from typing import Any

import pytest
from asyncpg import Connection

from aiven.db.create_db import main

GET_DATABASE_DESCRIPTION = """
SELECT TABLE_SCHEMA ,
       TABLE_NAME ,
       COLUMN_NAME ,
       ORDINAL_POSITION ,
       COLUMN_DEFAULT ,
       DATA_TYPE ,
       CHARACTER_MAXIMUM_LENGTH ,
       NUMERIC_PRECISION ,
       NUMERIC_PRECISION_RADIX ,
       NUMERIC_SCALE ,
       DATETIME_PRECISION
FROM   INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME=$1
"""


@pytest.mark.parametrize(
    "expected_results",
    [
        (
            {
                "url": [
                    {
                        "character_maximum_length": None,
                        "column_default": "nextval('url_id_seq'::regclass)",
                        "column_name": "id",
                        "data_type": "integer",
                        "datetime_precision": None,
                        "numeric_precision": 32,
                        "numeric_precision_radix": 2,
                        "numeric_scale": 0,
                        "ordinal_position": 1,
                        "table_name": "url",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": "5",
                        "column_name": "period",
                        "data_type": "smallint",
                        "datetime_precision": None,
                        "numeric_precision": 16,
                        "numeric_precision_radix": 2,
                        "numeric_scale": 0,
                        "ordinal_position": 4,
                        "table_name": "url",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": "now()",
                        "column_name": "created_at",
                        "data_type": "timestamp with time zone",
                        "datetime_precision": 6,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 5,
                        "table_name": "url",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": None,
                        "column_name": "last_run_at",
                        "data_type": "timestamp with time zone",
                        "datetime_precision": 6,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 6,
                        "table_name": "url",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": 255,
                        "column_default": None,
                        "column_name": "url",
                        "data_type": "character varying",
                        "datetime_precision": None,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 2,
                        "table_name": "url",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": 255,
                        "column_default": None,
                        "column_name": "regex",
                        "data_type": "character varying",
                        "datetime_precision": None,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 3,
                        "table_name": "url",
                        "table_schema": "public",
                    },
                ],
                "task_result": [
                    {
                        "character_maximum_length": None,
                        "column_default": "nextval('task_result_id_seq'::regclass)",
                        "column_name": "id",
                        "data_type": "integer",
                        "datetime_precision": None,
                        "numeric_precision": 32,
                        "numeric_precision_radix": 2,
                        "numeric_scale": 0,
                        "ordinal_position": 1,
                        "table_name": "task_result",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": None,
                        "column_name": "task_id",
                        "data_type": "integer",
                        "datetime_precision": None,
                        "numeric_precision": 32,
                        "numeric_precision_radix": 2,
                        "numeric_scale": 0,
                        "ordinal_position": 2,
                        "table_name": "task_result",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": None,
                        "column_name": "response_time",
                        "data_type": "double precision",
                        "datetime_precision": None,
                        "numeric_precision": 53,
                        "numeric_precision_radix": 2,
                        "numeric_scale": None,
                        "ordinal_position": 5,
                        "table_name": "task_result",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": "0",
                        "column_name": "status_code",
                        "data_type": "smallint",
                        "datetime_precision": None,
                        "numeric_precision": 16,
                        "numeric_precision_radix": 2,
                        "numeric_scale": 0,
                        "ordinal_position": 6,
                        "table_name": "task_result",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": "true",
                        "column_name": "regex_is_found",
                        "data_type": "boolean",
                        "datetime_precision": None,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 8,
                        "table_name": "task_result",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": "now()",
                        "column_name": "timestamp",
                        "data_type": "timestamp with time zone",
                        "datetime_precision": 6,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 4,
                        "table_name": "task_result",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": 255,
                        "column_default": None,
                        "column_name": "url",
                        "data_type": "character varying",
                        "datetime_precision": None,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 3,
                        "table_name": "task_result",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": None,
                        "column_name": "regex_result",
                        "data_type": "text",
                        "datetime_precision": None,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 9,
                        "table_name": "task_result",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": None,
                        "column_name": "error_text",
                        "data_type": "text",
                        "datetime_precision": None,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 7,
                        "table_name": "task_result",
                        "table_schema": "public",
                    },
                ],
                "task": [
                    {
                        "character_maximum_length": None,
                        "column_default": "nextval('task_id_seq'::regclass)",
                        "column_name": "id",
                        "data_type": "integer",
                        "datetime_precision": None,
                        "numeric_precision": 32,
                        "numeric_precision_radix": 2,
                        "numeric_scale": 0,
                        "ordinal_position": 1,
                        "table_name": "task",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": "now()",
                        "column_name": "created_at",
                        "data_type": "timestamp with time zone",
                        "datetime_precision": 6,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 2,
                        "table_name": "task",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": None,
                        "column_default": "0",
                        "column_name": "status",
                        "data_type": "integer",
                        "datetime_precision": None,
                        "numeric_precision": 32,
                        "numeric_precision_radix": 2,
                        "numeric_scale": 0,
                        "ordinal_position": 3,
                        "table_name": "task",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": 255,
                        "column_default": None,
                        "column_name": "url",
                        "data_type": "character varying",
                        "datetime_precision": None,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 4,
                        "table_name": "task",
                        "table_schema": "public",
                    },
                    {
                        "character_maximum_length": 255,
                        "column_default": None,
                        "column_name": "regex",
                        "data_type": "character varying",
                        "datetime_precision": None,
                        "numeric_precision": None,
                        "numeric_precision_radix": None,
                        "numeric_scale": None,
                        "ordinal_position": 5,
                        "table_name": "task",
                        "table_schema": "public",
                    },
                ],
            }
        ),
    ],
)
async def test_create_db(db_connection: Connection, expected_results: dict[str, list[dict[str, Any]]]) -> None:
    await main()

    for table_name, expected_result in expected_results.items():
        result = [dict(row) for row in await db_connection.fetch(GET_DATABASE_DESCRIPTION, table_name)]
        assert result == expected_result
