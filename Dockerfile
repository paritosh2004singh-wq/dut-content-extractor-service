# ==========================================
# Stage 1: Builder
# ==========================================
FROM python:3.14-slim AS builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy dependency file first for caching
COPY requirements.txt .

# Install dependencies into a separate directory
RUN uv pip install \
    --no-cache \
    --system \
    --target /app/deps \
    -r requirements.txt


# ==========================================
# Stage 2: Runner
# ==========================================
FROM python:3.14-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# Ensure Python can find the transferred packages
ENV PYTHONPATH=/app/deps

WORKDIR /app

# Copy packages and code from builder and context
COPY --from=builder /app/deps /app/deps
COPY . /app

EXPOSE 80

# Execute the application directly
CMD ["python", "main.py"]
