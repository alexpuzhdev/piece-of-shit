FROM python:3.13-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./
RUN apt-get update \
    && apt-get install -y --no-install-recommends netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*
RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction

COPY bot /app/bot
COPY project /app/project

COPY .docker/entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
