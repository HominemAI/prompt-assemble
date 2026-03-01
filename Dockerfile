# Frontend build stage
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend source
COPY src/prompt_assemble/ui/frontend/package*.json ./
RUN npm ci

COPY src/prompt_assemble/ui/frontend/ .
RUN npm run build

# Python build stage
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

# Copy built frontend assets (Vite outputs to ../static from frontend dir)
COPY --from=frontend-builder /app/static /app/src/prompt_assemble/ui/static

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

# Copy application code (without docs/README from builder)
COPY --from=builder /app/src /app/src

# Create prompts directory for filesystem-based prompts
RUN mkdir -p /app/prompts

# Set environment variables
ENV PROMPT_ASSEMBLE_UI=true \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5000 \
    PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Expose port
EXPOSE 5000

# Default command - start UI server with filesystem source
CMD ["python", "-c", "from prompt_assemble.sources import FileSystemSource; from prompt_assemble.ui import run_server; source = FileSystemSource('/app/prompts'); run_server(source=source, host='0.0.0.0', port=5000, debug=False)"]
