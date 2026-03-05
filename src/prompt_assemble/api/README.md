# Prompt Assemble REST API

A Flask-based REST API server for the `prompt-assemble` library. Provides a comprehensive set of endpoints for prompt management, including CRUD operations, tagging, versioning, and export functionality.

## Quick Start

```bash
# Enable the API server
export PROMPT_ASSEMBLE_API=true

# Configure database (optional)
export DB_HOSTNAME=localhost
export DB_PASSWORD=your_password

# Run the server
python -m prompt_assemble.api
```

The server will start at `http://127.0.0.1:8000`

## API Endpoints

### Prompts
- `GET /api/prompts` - List all prompts
- `GET /api/prompts/search?q=<query>` - Search prompts
- `GET /api/prompts/<name>` - Get prompt by name
- `POST /api/prompts/<name>` - Save/create prompt
- `DELETE /api/prompts/<name>` - Delete prompt

### Tags
- `GET /api/tags` - List all tags

### Variable Sets
- `GET /api/variable-sets` - List all variable sets
- `POST /api/variable-sets` - Create variable set
- `DELETE /api/variable-sets/<id>` - Delete variable set

### Prompt History
- `GET /api/prompts/<name>/history` - Get revision history
- `POST /api/prompts/<name>/revert` - Revert to previous version

### Export
- `POST /api/export` - Export prompts by criteria

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `PROMPT_ASSEMBLE_API` | Enable API server | false |
| `PORT` | Server port | 8000 |
| `DB_HOSTNAME` | PostgreSQL host | localhost |
| `DB_PORT` | PostgreSQL port | 5432 |
| `DB_USERNAME` | PostgreSQL user | postgres |
| `DB_PASSWORD` | PostgreSQL password | (required) |
| `DB_DATABASE` | PostgreSQL database | prompts |
| `PROMPT_ASSEMBLE_TABLE_PREFIX` | Table name prefix (multi-tenancy) | "" |

## Usage with Frontend

The API is designed to work with separate frontend applications:
- **OSS Frontend**: https://github.com/HominemAI/prompt-assemble-ui
- **Hominem Frontend**: https://github.com/HominemAI/prompt-assemble-ui-hominem

Both frontends proxy API calls to `http://localhost:8000/api`

## Testing

```bash
# Test the API
curl http://localhost:8000/api/prompts

# Search
curl "http://localhost:8000/api/prompts/search?q=test"
```
