FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e ".[dev]"

FROM base AS development

CMD ["python", "-m", "src.main"]

FROM python:3.12-slim AS production

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e "."
COPY src/ src/

CMD ["digester-worker"]
