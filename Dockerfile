FROM python:3.11-slim AS build_stage

# --- Настройки окружения ---
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/poetry/bin:${PATH}"

# --- Установка Poetry ---
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/* \
 && curl -sSL https://install.python-poetry.org | python -

# --- Рабочая директория ---
WORKDIR /app

# --- Копируем зависимости и исходники ---
COPY pyproject.toml poetry.lock ./
COPY src /app/src
COPY scripts /app/scripts

# --- Указываем Python, где искать модули ---
ENV PYTHONPATH="/app"

# ----------------------------------------------------
# --- Runtime stage ---
FROM build_stage AS app

# Устанавливаем зависимости приложения в системное окружение (без .venv)
RUN poetry config virtualenvs.create false \
 && poetry install --no-root

WORKDIR /app

# Запуск как модуля (устойчиво к импортам)
ENTRYPOINT ["python", "src/main.py"]

# ----------------------------------------------------
# --- Tests stage ---
FROM build_stage AS tests

RUN poetry config virtualenvs.create false \
 && poetry install --no-root

WORKDIR /app
COPY tests /app/tests

ENTRYPOINT ["pytest", "-q", "tests"]
