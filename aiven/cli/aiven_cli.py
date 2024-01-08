#!/usr/local/bin/python

import argparse
import asyncio
import logging
import re
from typing import Any

import validators
from asyncpg import CheckViolationError, InterfaceError, PostgresError, UniqueViolationError

from aiven.db.crud import create_new_url, remove_url_by_url, remove_url_by_url_and_regex
from aiven.db.db import get_db_connection
from conf.config import settings

logger = logging.getLogger(__name__)


def period(value: Any) -> int:
    ivalue = int(value)
    if ivalue <= settings.MIN_PERIOD or ivalue >= settings.MAX_PERIOD:
        raise argparse.ArgumentTypeError("%s is an invalid period value" % value)

    return ivalue


def url(value: Any) -> str:
    valid = validators.url(value)
    if not valid:
        raise argparse.ArgumentTypeError("%s is an invalid url value" % value)

    return value


def regex(value: Any) -> str:
    try:
        re.compile(value)
    except re.error:
        raise argparse.ArgumentTypeError("%s is an invalid regex value" % value)

    return value


parser = argparse.ArgumentParser(
    prog="aiven-cli",
    description="add/remove url and regex",
)

parser.add_argument("action", type=str, choices=["add", "remove"], help="action")
parser.add_argument("url", type=url, help="valid url, for instance http://test.com")
parser.add_argument("-p", "--period", type=period, help="interval between requests", default=5)
parser.add_argument("-r", "--regex", type=regex, required=False, help="regex, for instance .*")


async def add_url(url: str, period: int, regex: str | None = None) -> None:
    try:
        async with get_db_connection() as connection:
            try:
                await create_new_url(connection, url, period, regex)
            except UniqueViolationError:
                logger.exception("Add url error")
                raise argparse.ArgumentTypeError("(%s, %s) is not an unique url, regex value" % (url, regex))
            except CheckViolationError as exc:
                logger.exception("Add url error")
                raise argparse.ArgumentTypeError(
                    "(%s, %s) is not pass violation an url, period value. Exception: %s"  # noqa: BLK100
                    % (url, regex, exc),
                )
    except (PostgresError, InterfaceError, asyncio.TimeoutError):
        logger.exception("add url exception")


async def remove_url(url: str, regex: str | None = None) -> None:
    try:
        async with get_db_connection() as connection:
            if regex:
                await remove_url_by_url_and_regex(connection, url, regex)
            else:
                await remove_url_by_url(connection, url)
    except (PostgresError, InterfaceError, asyncio.TimeoutError):
        logger.exception("remove url exception")


if __name__ == "__main__":
    args = parser.parse_args()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if args.action == "add":
        loop.run_until_complete(add_url(args.url, args.period, args.regex))
    elif args.action == "remove":
        loop.run_until_complete(remove_url(args.url, args.regex))

    loop.close()
