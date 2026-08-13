# syntax=docker/dockerfile:1

# ============================================================================
# Stage 1: builder — compiles/installs Python deps into an isolated prefix.
# Keeps build toolchain (gcc, *-dev headers) out of the final image.
# ============================================================================
FROM python:3.14-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --prefix=/install -r requirements.txt

# ============================================================================
# Stage 2: runtime — slim image with only runtime shared libs + the
# installed packages copied over. No compilers, no build headers.
# ============================================================================
FROM python:3.14-slim AS runtime

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    gdal-bin \
    libgeos-c1v5 \
    libproj25 \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/usr/local/bin:$PATH" \
    PYTHONPATH="/usr/local/lib/python3.14/site-packages"

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

COPY --from=builder /install /usr/local

COPY --chown=appuser:appuser . /app

USER appuser

EXPOSE 8000

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", "--timeout", "60"]