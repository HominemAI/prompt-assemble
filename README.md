# prompt-assemble

A lightweight prompt assembly library for building dynamic prompts with sigil-based substitution. No logic in
templates — templates stay dumb, logic stays in Python.

## Features

- **Sigil-based substitution** — Simple placeholder syntax (`[[VAR_NAME]]` and `[[PROMPT: name]]`)
- **Format-agnostic** — Works with loose XML, JSON, or plain text
- **Recursive substitution** — Variable values can contain sigils, resolved in a second pass
- **Comments support** — Single-line (`#!`) and multiline (`<!-- -->`) comments
- **No template logic** — Loops, conditionals, and transforms belong in Python
- **Portable** — Easy to use across different environments

## Installation

```bash
pip install prompt-assemble
```

## Quick Start

```python
from prompt_assemble import assemble

template = """
<system>
You are a [[PROMPT: persona]] specializing in [[DOMAIN]].
</system>

<task>
[[PROMPT: task-instructions]]
</task>

<question>
[[QUESTION]]
</question>
"""

components = {
    "persona": "expert software architect",
    "task-instructions": "Analyze the code and provide recommendations.",
}

variables = {
    "DOMAIN": "Python development",
    "QUESTION": "How can we improve this function?",
}

result = assemble(template, components=components, variables=variables)
print(result)
```

## Format Support

### Loose XML

```xml

<system>You are a [[PROMPT: persona]]</system>
<task>[[PROMPT: task-instructions]]</task>
```

### JSON

```json
{
  "system": "You are a [[PROMPT: persona]]",
  "task": "[[PROMPT: task-instructions]]"
}
```

### Plain Text

```
Subject: [[SUBJECT]]

Body:
[[BODY]]
```

## Sigil Syntax

| Sigil                          | Purpose                                             |
|--------------------------------|-----------------------------------------------------|
| `[[VAR_NAME]]`                 | Simple variable substitution                        |
| `[[PROMPT: name]]`             | Inject a named prompt component                     |
| `[[PROMPT_TAG: tag1, tag2]]`   | Inject all prompts matching tags (AND intersection) |
| `[[PROMPT_TAG:N: tag1, tag2]]` | Inject N most recent prompts matching tags          |

## Comments

```
#! Single line comment

<!-- Multi-line
     comment -->
```

Comments are stripped before substitution and never reach the model.

## Recursive Substitution

Variable values can themselves contain sigils:

```python
variables = {
    "TASK": "Analyze [[CODE_TYPE]] code",
    "CODE_TYPE": "Python",
}

# Second pass resolves nested sigils
```

## CLI Usage

```bash
pambl --template prompt.prompt --components components.json --variables vars.json
```

## Database

**PostgreSQL is required.** The DatabaseSource implementation uses PostgreSQL-specific features including automatic
reconnection on timeout and transaction management optimized for reliability.

### PostgreSQL Support

- **PostgreSQL 10+** (required for production and testing)
- Automatic connection reconnection on timeout
- Multi-tenant support via table prefixes
- Version history and tagging

### Quick Setup with PostgreSQL

```python
import psycopg2
from prompt_assemble.sources import DatabaseSource

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    database="prompts",
    user="postgres",
    password="secret"
)

# Create source with table prefix for multi-tenant support
source = DatabaseSource(conn, table_prefix="prod_")

# Use with PromptProvider
from prompt_assemble import PromptProvider

provider = PromptProvider(source)
```

### Docker Compose with PostgreSQL

See [DOCKER.md](./DOCKER.md#with-database) for a complete Docker Compose setup with PostgreSQL.

## Bulk Import (Preloading Database)

The `bulk_import()` function allows you to migrate all prompts and their metadata from one source to another. This is useful for:
- Populating a database with prompts stored in the filesystem
- Migrating between storage backends
- Backing up/restoring prompts

```python
from prompt_assemble import (
    PromptProvider,
    FileSystemSource,
    DatabaseSource,
    bulk_import
)
import psycopg2

# Load prompts from filesystem
filesystem_source = FileSystemSource('./prompts')
source_provider = PromptProvider(filesystem_source)

# Connect to PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="prompts",
    user="postgres",
    password="secret"
)
database_source = DatabaseSource(conn, table_prefix="prod_")
target_provider = PromptProvider(database_source)

# Bulk import with all metadata (tags, description, owner)
results = bulk_import(source_provider, target_provider, verbose=True)

print(f"✅ Imported {results['imported']} prompts")
print(f"⚠️  Skipped {results['skipped']} existing prompts")
print(f"❌ Errors: {results['errors']}")
```

### Bulk Import Options

```python
# Skip prompts already in target
results = bulk_import(
    source_provider,
    target_provider,
    skip_existing=True  # Don't overwrite existing prompts
)

# Verbose output for debugging
results = bulk_import(
    source_provider,
    target_provider,
    verbose=True  # Log each import operation
)
```

### Return Value

The `bulk_import()` function returns a dictionary with import statistics:

```python
{
    "imported": 42,      # Successfully imported
    "skipped": 3,        # Skipped (already exist or skip_existing=True)
    "errors": 1,         # Failed imports
    "errors_list": [     # Details of failures
        {"name": "failing_prompt", "error": "Connection timeout"}
    ]
}
```

### What Gets Transferred

All metadata is preserved during bulk import:
- ✅ Prompt content
- ✅ Tags (AND intersection filtering supported)
- ✅ Description
- ✅ Owner
- ✅ Versioning (for database targets)

## Environment Variables

The prompt-assemble library and UI support the following environment variables for configuration:

### Starting the UI Server

Use the provided startup script:

```bash
python start_ui_db.py
```

This script automatically:

- Connects to PostgreSQL using environment variables
- Initializes the database schema
- Starts the Flask UI server
- Creates tables with the configured prefix

### Database Configuration (PostgreSQL)

| Variable      | Type   | Default     | Description                                                                  |
|---------------|--------|-------------|------------------------------------------------------------------------------|
| `DB_HOSTNAME` | string | `localhost` | PostgreSQL server hostname                                                   |
| `DB_PORT`     | int    | `5432`      | PostgreSQL server port                                                       |
| `DB_USERNAME` | string | `postgres`  | PostgreSQL username                                                          |
| `DB_PASSWORD` | string | (required)  | PostgreSQL password                                                          |
| `DB_DATABASE` | string | `prompts`   | PostgreSQL database name                                                     |
| `DB_SSLMODE`  | string | `require`   | SSL mode: `require`, `prefer`, `disable`                                     |
| `DB_PREFIX`   | string | `pambl_`    | Table name prefix (e.g., tables become `pambl_prompts`, `pambl_prompt_tags`) |
| `PORT`        | int    | `8000`      | Port for the Flask UI server                                                 |

**Example - Local PostgreSQL:**

```bash
export DB_HOSTNAME=localhost
export DB_PORT=5432
export DB_USERNAME=postgres
export DB_PASSWORD=your_password
export DB_DATABASE=prompts
export DB_PREFIX=pambl_
export PORT=8000

python start_ui_db.py
```

**Example - DigitalOcean Managed PostgreSQL:**

```bash
export DB_HOSTNAME=db-postgresql-sfo2-xxxx-do-user-xxxxx-0.e.db.ondigitalocean.com
export DB_PORT=25060
export DB_USERNAME=pambl_user
export DB_PASSWORD=your_secure_password
export DB_DATABASE=pambl_db
export DB_SSLMODE=require
export DB_PREFIX=pambl_
export PORT=8000

python start_ui_db.py
```

### Programmatic Configuration (Legacy)

| Variable                       | Type   | Default      | Description                                                   |
|--------------------------------|--------|--------------|---------------------------------------------------------------|
| `PROMPT_ASSEMBLE_UI`           | bool   | `false`      | Enable/disable the web UI server. Set to `"true"` to activate |
| `PROMPT_ASSEMBLE_TABLE_PREFIX` | string | `""` (empty) | Table prefix (deprecated - use `DB_PREFIX` instead)           |

### Listener & Event Configuration

| Variable       | Type | Default | Description                                        |
|----------------|------|---------|----------------------------------------------------|
| None currently | -    | -       | Listener callbacks are configured programmatically |

## Configuration Examples

### Development Environment (Local PostgreSQL)

```bash
export DB_HOSTNAME=localhost
export DB_PORT=5432
export DB_USERNAME=postgres
export DB_PASSWORD=dev_password
export DB_DATABASE=prompts_dev
export DB_SSLMODE=disable
export DB_PREFIX=dev_
export PORT=8000

python start_ui_db.py
```

### Production (DigitalOcean PostgreSQL)

```bash
export DB_HOSTNAME=db-postgresql-sfo2-xxxxx-do-user-xxxxx-0.e.db.ondigitalocean.com
export DB_PORT=25060
export DB_USERNAME=prod_user
export DB_PASSWORD=your_secure_password
export DB_DATABASE=prompts_prod
export DB_SSLMODE=require
export DB_PREFIX=prod_
export PORT=8000

python start_ui_db.py
```

### Testing

```bash
export DB_HOSTNAME=localhost
export DB_PORT=5432
export DB_USERNAME=postgres
export DB_PASSWORD=test_password
export DB_DATABASE=prompts_test
export DB_PREFIX=test_
export PORT=8001

python start_ui_db.py
```

## Programmatic Configuration

You can also configure these settings directly in Python:

```python
from prompt_assemble.sources import DatabaseSource
from prompt_assemble.api import run_server
import psycopg2

# Configure PostgreSQL database with table prefix
conn = psycopg2.connect(
    host="localhost",
    database="prompts",
    user="postgres",
    password="secret"
)
source = DatabaseSource(conn, table_prefix='myapp_')

# Configure Flask server
run_server(
    source=source,
    host='0.0.0.0',
    port=8000,
    debug=False
)
```

## Quick Reference

### All Environment Variables

```bash
# UI Server (Required for web interface)
PROMPT_ASSEMBLE_UI=true

# Flask Configuration (Optional)
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
FLASK_DEBUG=false

# PostgreSQL Database Connection
DB_HOSTNAME=localhost
DB_PORT=5432
DB_USERNAME=postgres
DB_PASSWORD=secret
DB_DATABASE=prompts

# Database Options
PROMPT_ASSEMBLE_TABLE_PREFIX=myapp_  # Table prefix for multi-tenancy
```

### Database Driver

Install psycopg2 for PostgreSQL:

```bash
pip install psycopg2-binary
```

## Connection Resilience

The DatabaseSource automatically handles connection timeouts and network interruptions:

- **Automatic reconnection** — Detects closed connections and reconnects transparently
- **Health checks** — Validates connection before each operation
- **Timeout recovery** — Handles PostgreSQL idle timeout gracefully

No configuration required — reconnection happens automatically on these operations:

- `save_prompt()` - Save/update prompts
- `delete_prompt()` - Delete prompts
- `refresh()` - Reload metadata
- `get_raw()` - Fetch content
- All variable set operations

## Testing

Run the full test suite:

```bash
pytest tests/
```

**Note:** Database-specific tests require PostgreSQL:

```bash
# Skip database tests (for environments without PostgreSQL)
pytest tests/ -k "not test_database"

# Run only with PostgreSQL available
PGHOST=localhost PGUSER=postgres PGPASSWORD=secret PGDATABASE=test_prompts pytest tests/test_database_source.py
```

**Test Coverage:** 135 passing tests covering core library, FileSystem source, listener system, save/delete operations, and bulk import functionality. PostgreSQL-specific tests are marked as requiring PostgreSQL.

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## License

MIT License — see LICENSE file for details.
