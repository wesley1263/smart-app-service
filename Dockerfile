FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml .

# ── dev: inclui pytest, black, mypy, etc. (usado por test e lint) ──────────────
FROM base AS dev
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .

# ── prod: somente dependências de runtime ──────────────────────────────────────
FROM base AS prod
RUN pip install --no-cache-dir -e "."
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
