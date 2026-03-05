# Building and Running prompt-assemble

## Frontend Build Setup (Vite + React)

The UI uses Vite for fast builds and React for the interface.

### Prerequisites

- Node.js 16+ and npm
- Python 3.11+

### Build Steps

#### 1. Install Frontend Dependencies

```bash
cd src/prompt_assemble/api/frontend
npm install
```

#### 2. Build the Frontend

```bash
npm run build
```

This compiles the React TypeScript code to static files in `src/prompt_assemble/api/static/`.

#### 3. Run the Server

```bash
cd /Users/asanchez/DevWorkspace/prompt-assemble
python -m prompt_assemble.api.server
```

The app will be available at **http://localhost:5000**

### Development Workflow

#### Option 1: Watch Mode (Recommended for Development)

**Terminal 1 - Frontend Dev Server**
```bash
cd src/prompt_assemble/api/frontend
npm run dev
```
This starts Vite dev server at http://localhost:5173 with hot reload

**Terminal 2 - Flask Backend**
```bash
python -m prompt_assemble.api.server
```

#### Option 2: Build Once and Serve

```bash
# Build frontend
cd src/prompt_assemble/api/frontend
npm run build

# Run backend
cd /Users/asanchez/DevWorkspace/prompt-assemble
python -m prompt_assemble.api.server
```

### Complete Setup Script

```bash
#!/bin/bash
set -e

cd /Users/asanchez/DevWorkspace/prompt-assemble

# Install Python dependencies
pip install -e .

# Install frontend dependencies
cd src/prompt_assemble/api/frontend
npm install

# Build frontend
npm run build

# Run server
cd /Users/asanchez/DevWorkspace/prompt-assemble
export PROMPT_ASSEMBLE_UI=true
python -m prompt_assemble.api.server
```

### Environment Variables

For the UI to work, ensure:
```bash
export PROMPT_ASSEMBLE_UI=true
```

For database backend:
```bash
export DB_HOSTNAME=localhost
export DB_PORT=5432
export DB_USERNAME=postgres
export DB_PASSWORD=secret
export DB_DATABASE=prompts
```

## Troubleshooting

### Static Files Not Found

If you see blank page with 404 errors for static files:
1. Make sure you ran `npm run build`
2. Check that `src/prompt_assemble/api/static/` directory exists
3. Verify `index.html` is in the static directory

### Port Already in Use

```bash
# Change port
python -m prompt_assemble.api.server --port 8000
```

### Module Import Errors

Make sure you installed Python package in development mode:
```bash
cd /Users/asanchez/DevWorkspace/prompt-assemble
pip install -e .
```

## Production Deployment

For production:
1. Build the frontend: `npm run build`
2. Use a production WSGI server (gunicorn, uwsgi, etc.)
3. Serve static files with a CDN or web server (nginx)
4. Set `FLASK_DEBUG=false`
5. Use PostgreSQL database backend
