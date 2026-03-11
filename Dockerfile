# Frontend build stage
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

# Install git (needed to clone repository)
RUN apk add --no-cache git

# Clone the frontend repository
ARG FRONTEND_REPO=https://github.com/HominemAI/prompt-assemble-ui.git
ARG FRONTEND_BRANCH=main

RUN git clone --branch ${FRONTEND_BRANCH} ${FRONTEND_REPO} . && \
    npm ci && \
    npm run build

# Backend build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and source
COPY setup.py pyproject.toml README.md LICENSE /app/
COPY src/ /app/src/

# Copy built frontend assets to static directory
COPY --from=frontend-builder /frontend/static /app/src/prompt_assemble/api/static

# Install prompt-assemble with UI and database dependencies
RUN pip install --no-cache-dir -e ".[ui-full]"

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=builder /app/src /app/src

# Create prompts directory for filesystem-based prompts
RUN mkdir -p /app/prompts

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/prompts || exit 1

# Expose port
EXPOSE 8000

# Default command - start Flask server
# Set environment variables before running: DB_HOSTNAME, DB_PORT, DB_USERNAME, DB_PASSWORD, DB_DATABASE, DB_PREFIX
CMD ["python", "-c", "from prompt_assemble.api.server import run_server; from prompt_assemble.sources import create_database_source_from_env; run_server(source=create_database_source_from_env(), host='0.0.0.0', port=8000, debug=False)"]
