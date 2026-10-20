FROM python:3.12-slim AS base

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# System deps for asyncpg (libpq) and general build tooling
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libpq-dev python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install all dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files (backend, bot, run.py, etc.)
COPY . .

CMD ["python", "run.py"]
