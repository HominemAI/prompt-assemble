# Docker Setup for prompt-assemble

This document describes how to build and run prompt-assemble as a Docker container.

## Quick Start

### Using Pre-built Image

```bash
# Pull the latest image from GitHub Container Registry
docker pull ghcr.io/AgentSanchez/prompt-assemble:latest

# Run the container
docker run -p 5000:5000 \
  -e PROMPT_ASSEMBLE_UI=true \
  -v prompts:/app/prompts \
  ghcr.io/AgentSanchez/prompt-assemble:latest
```

Open http://localhost:5000 in your browser.

### Building Locally

```bash
# Clone the repository
git clone https://github.com/AgentSanchez/prompt-assemble.git
cd prompt-assemble

# Build the Docker image
docker build -t prompt-assemble:local .

# Run the container
docker run -p 5000:5000 \
  -e PROMPT_ASSEMBLE_UI=true \
  -v prompts:/app/prompts \
  prompt-assemble:local
```

## Docker Image Details

### Base Image
- **Python:** 3.11-slim (optimized for smaller size)
- **OS:** Debian Linux (minimal)
- **Size:** ~300-400 MB

### Components
- prompt-assemble core library
- Flask-based UI server
- All dependencies

### Exposed Port
- **5000** - Flask web UI server

### Health Check
- HTTP GET to `/` every 30 seconds
- 5 second startup grace period
- 10 second timeout
- Fails after 3 retries

## Running the Container

### Basic Usage (Filesystem Source)

```bash
docker run -p 5000:5000 \
  -e PROMPT_ASSEMBLE_UI=true \
  ghcr.io/AgentSanchez/prompt-assemble:latest
```

### With Prompt Volume

```bash
# Create a Docker volume
docker volume create prompt-data

# Run with persistent prompts
docker run -p 5000:5000 \
  -e PROMPT_ASSEMBLE_UI=true \
  -v prompt-data:/app/prompts \
  ghcr.io/AgentSanchez/prompt-assemble:latest
```

### With Local Prompts Directory

```bash
# Run with local directory mounted
docker run -p 5000:5000 \
  -e PROMPT_ASSEMBLE_UI=true \
  -v $(pwd)/prompts:/app/prompts \
  ghcr.io/AgentSanchez/prompt-assemble:latest
```

### With PostgreSQL Database (Recommended)

```bash
docker run -p 5000:5000 \
  -e PROMPT_ASSEMBLE_UI=true \
  -e PROMPT_ASSEMBLE_TABLE_PREFIX=docker_ \
  -e DB_HOSTNAME=postgres \
  -e DB_PORT=5432 \
  -e DB_USERNAME=postgres \
  -e DB_PASSWORD=secret \
  -e DB_DATABASE=prompts \
  ghcr.io/AgentSanchez/prompt-assemble:latest
```

### With SQLite Database (Development Only)

```bash
docker run -p 5000:5000 \
  -e PROMPT_ASSEMBLE_UI=true \
  -e PROMPT_ASSEMBLE_TABLE_PREFIX=docker_ \
  -v db-data:/app/db \
  -e DATABASE_URL=sqlite:////app/db/prompts.db \
  ghcr.io/AgentSanchez/prompt-assemble:latest
```

### Custom Configuration

```bash
docker run -p 5000:5000 \
  -e PROMPT_ASSEMBLE_UI=true \
  -e FLASK_HOST=0.0.0.0 \
  -e FLASK_PORT=5000 \
  -e FLASK_DEBUG=false \
  -e PROMPT_ASSEMBLE_TABLE_PREFIX=myapp_ \
  -v prompts:/app/prompts \
  ghcr.io/AgentSanchez/prompt-assemble:latest
```

## Docker Compose

### Basic Setup

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  prompt-assemble:
    image: ghcr.io/AgentSanchez/prompt-assemble:latest
    ports:
      - "5000:5000"
    environment:
      PROMPT_ASSEMBLE_UI: "true"
      FLASK_HOST: 0.0.0.0
      FLASK_PORT: 5000
      PROMPT_ASSEMBLE_TABLE_PREFIX: "docker_"
    volumes:
      - prompts:/app/prompts
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

volumes:
  prompts:
```

Run with:
```bash
docker-compose up
```

### With PostgreSQL Database (Recommended)

```yaml
version: '3.8'

services:
  prompt-assemble:
    image: ghcr.io/AgentSanchez/prompt-assemble:latest
    ports:
      - "5000:5000"
    environment:
      PROMPT_ASSEMBLE_UI: "true"
      FLASK_HOST: 0.0.0.0
      FLASK_PORT: 5000
      PROMPT_ASSEMBLE_TABLE_PREFIX: "app_"
      # PostgreSQL Configuration
      DB_HOSTNAME: postgres
      DB_PORT: "5432"
      DB_USERNAME: postgres
      DB_PASSWORD: prompts
      DB_DATABASE: prompts
    volumes:
      - prompts:/app/prompts
    depends_on:
      postgres:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: prompts
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: prompts
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres-data:
  prompts:
```

## Environment Variables

See [README.md - Environment Variables](./README.md#environment-variables) for complete reference.

Key variables for Docker:
- `PROMPT_ASSEMBLE_UI=true` - Enable web UI
- `FLASK_HOST=0.0.0.0` - Listen on all interfaces
- `FLASK_PORT=5000` - Server port
- `PROMPT_ASSEMBLE_TABLE_PREFIX=` - Database table prefix

## Volume Mounts

| Path | Purpose | Optional |
|------|---------|----------|
| `/app/prompts` | Filesystem-based prompts | Yes |
| `/app/db` | Database files (SQLite) | Yes |

## Networking

The container exposes port 5000 by default. Map it to your host:

```bash
# Map to same port
docker run -p 5000:5000 ...

# Map to different port
docker run -p 8000:5000 ...

# Expose to network (use with caution)
docker run -p 0.0.0.0:5000:5000 ...
```

## Kubernetes Deployment

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prompt-assemble
spec:
  replicas: 1
  selector:
    matchLabels:
      app: prompt-assemble
  template:
    metadata:
      labels:
        app: prompt-assemble
    spec:
      containers:
      - name: prompt-assemble
        image: ghcr.io/AgentSanchez/prompt-assemble:latest
        ports:
        - containerPort: 5000
        env:
        - name: PROMPT_ASSEMBLE_UI
          value: "true"
        - name: FLASK_HOST
          value: "0.0.0.0"
        - name: PROMPT_ASSEMBLE_TABLE_PREFIX
          value: "k8s_"
        volumeMounts:
        - name: prompts
          mountPath: /app/prompts
        livenessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
      volumes:
      - name: prompts
        emptyDir: {}
---
apiVersion: v1
kind: Service
metadata:
  name: prompt-assemble
spec:
  selector:
    app: prompt-assemble
  ports:
  - port: 5000
    targetPort: 5000
  type: LoadBalancer
```

### Service Mesh (Istio)

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: prompt-assemble
spec:
  hosts:
  - prompt-assemble
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: prompt-assemble
        port:
          number: 5000
```

## Image Variants

### Tags

- `latest` - Most recent release
- `v1.2.3` - Specific version
- `main` - Latest from main branch (on each push)

### Building Custom Variants

To build with custom configurations:

```dockerfile
# Dockerfile.custom
FROM ghcr.io/AgentSanchez/prompt-assemble:latest

# Add your custom prompts
COPY ./prompts/ /app/prompts/

# Custom entrypoint
ENTRYPOINT ["python", "-m", "prompt_assemble.ui"]
```

Build and run:
```bash
docker build -f Dockerfile.custom -t my-prompts:1.0 .
docker run -p 5000:5000 my-prompts:1.0
```

## Troubleshooting

### Container won't start

```bash
# View logs
docker logs <container-id>

# Run with interactive shell
docker run -it prompt-assemble:latest /bin/bash
```

### Port already in use

```bash
# Use different port
docker run -p 8000:5000 ...

# Find what's using the port
lsof -i :5000
```

### Volume permissions

```bash
# Ensure correct permissions
docker run --user 0 -v prompts:/app/prompts ...

# Or use Docker volume driver
docker volume create prompts
docker run -v prompts:/app/prompts ...
```

### Health check failures

```bash
# Test manually
docker exec <container-id> curl -f http://localhost:5000/

# View health status
docker inspect <container-id> --format='{{.State.Health.Status}}'
```

## GitHub Actions

Images are automatically built and published on tag push:

```bash
# Create and push a tag
git tag v1.2.3
git push origin v1.2.3

# Image will be available at:
# ghcr.io/AgentSanchez/prompt-assemble:v1.2.3
# ghcr.io/AgentSanchez/prompt-assemble:latest
```

## Development

### Build locally

```bash
docker build -t prompt-assemble:dev .
```

### Debug mode

```bash
docker run -it \
  -e FLASK_DEBUG=true \
  -v $(pwd)/src:/app/src \
  prompt-assemble:dev
```

### Multi-stage build

The Dockerfile uses multi-stage builds to minimize image size:
1. **Builder stage** - Installs dependencies
2. **Runtime stage** - Only includes necessary files

## See Also

- [README.md](./README.md) - Main documentation
- [SETUP_GUIDE.md](./src/prompt_assemble/ui/SETUP_GUIDE.md) - UI setup
- [Dockerfile](./Dockerfile) - Docker configuration
- [docker-compose.yml](#docker-compose) - Example compose file
