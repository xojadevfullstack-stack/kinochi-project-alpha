FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir setuptools wheel pip -U

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

CMD ["python", "main.py"]
