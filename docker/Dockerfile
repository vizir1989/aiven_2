FROM python:3.12-slim as base

ARG POETRY_VERSION=1.5.1

ENV PYTHONUNBUFFERED 1
WORKDIR /app
RUN apt update -y && apt install -y gcc

RUN python -m pip install --upgrade pip
RUN python -m pip install --upgrade setuptools wheel poetry==${POETRY_VERSION}
RUN apt-get update && apt-get install systemd gettext -y

RUN useradd -m aiven

COPY --chown=aiven:aiven poetry.lock ./
COPY --chown=aiven:aiven pyproject.toml ./

RUN poetry config installer.max-workers 10 && \
    poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi

RUN chown aiven:aiven -R /app

USER aiven

FROM base as flake
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY --chown=aiven:aiven . .
RUN chmod +x ./scripts/cicd/flake8.sh
RUN ./scripts/cicd/flake8.sh


FROM base as test

USER root

RUN apt update -y && apt install -y libpq5 libpq-dev
RUN apt install curl gnupg2 lsb-release -y
RUN curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc | gpg --dearmor -o /etc/apt/trusted.gpg.d/postgresql.gpg
RUN sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN apt update -y
RUN apt install postgresql-16 -y

RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

USER aiven

COPY --chown=aiven:aiven . .

RUN chmod +x ./scripts/cicd/test.sh
RUN PYTHONPATH=. ./scripts/cicd/test.sh


FROM base as dist-image

COPY --chown=aiven:aiven . .

ENV PYTHONPATH=.

RUN chmod +x ./scripts/application/producer.sh
RUN chmod +x ./scripts/application/consumer.sh
RUN chmod +x ./scripts/application/create_db.sh
RUN chmod +x ./aiven/cli/aiven_cli.py
