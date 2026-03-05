# DatabaseSource: PostgreSQL & Table Prefix Feature

## Database Backend

**The primary data backend is PostgreSQL.** The `DatabaseSource` class uses DBAPI2-compatible database drivers, supporting:

- **PostgreSQL** (recommended for production)
- SQLite (development/testing)
- MySQL, MariaDB, and other DBAPI2-compatible databases

### Quick Start with PostgreSQL

**Option 1: Using Environment Variables (Recommended)**

```bash
# Set PostgreSQL connection environment variables
export DB_HOSTNAME=localhost
export DB_PORT=5432
export DB_USERNAME=postgres
export DB_PASSWORD=secret
export DB_DATABASE=prompts
export PROMPT_ASSEMBLE_TABLE_PREFIX=prod_

# Python code
from prompt_assemble.sources import create_database_source_from_env

source = create_database_source_from_env()  # Reads all env vars automatically
```

**Option 2: Direct Python Connection**

```python
import psycopg2
from prompt_assemble.sources import DatabaseSource

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="prompts",
    user="postgres",
    password="secret"
)

# Create source with table prefix
source = DatabaseSource(conn, table_prefix="prod_")
```

## PostgreSQL Configuration

Configure PostgreSQL connection using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `DB_HOSTNAME` | `localhost` | PostgreSQL server hostname |
| `DB_PORT` | `5432` | PostgreSQL server port |
| `DB_USERNAME` | `postgres` | PostgreSQL username |
| `DB_PASSWORD` | (required) | PostgreSQL password |
| `DB_DATABASE` | `prompts` | PostgreSQL database name |

```bash
export DB_HOSTNAME=postgres.example.com
export DB_PORT=5432
export DB_USERNAME=myuser
export DB_PASSWORD=mypassword
export DB_DATABASE=prompts_db
```

Then create the source:

```python
from prompt_assemble.sources import create_database_source_from_env

source = create_database_source_from_env()
```

## Table Prefix Feature

The `DatabaseSource` supports configurable table name prefixes, allowing multiple independent prompt databases to coexist in the same database instance. This is useful for multi-tenant applications, testing environments, or when you need to avoid table name collisions.

## Configuration

### 1. Environment Variable (Recommended)

Set the `PROMPT_ASSEMBLE_TABLE_PREFIX` environment variable:

```bash
export DB_HOSTNAME=localhost
export DB_PASSWORD=secret
export PROMPT_ASSEMBLE_TABLE_PREFIX=myapp_
python your_script.py
```

All tables will be prefixed with `myapp_`:
- `myapp_prompts`
- `myapp_prompt_registry`
- `myapp_prompt_tags`
- `myapp_prompt_versions`

### 2. Constructor Argument

Pass the prefix directly to `DatabaseSource`:

```python
from prompt_assemble.sources import DatabaseSource
import sqlite3

conn = sqlite3.connect('prompts.db')
source = DatabaseSource(conn, table_prefix='app_')
```

### 3. Default Behavior

If neither environment variable nor constructor argument is provided, tables have no prefix:

```python
source = DatabaseSource(conn)
# Creates: prompts, prompt_registry, prompt_tags, prompt_versions
```

## Priority

Constructor argument takes priority over environment variable:

```python
# Environment variable
os.environ['PROMPT_ASSEMBLE_TABLE_PREFIX'] = 'env_'

# Constructor argument overrides it
source = DatabaseSource(conn, table_prefix='arg_')
# Uses prefix: 'arg_' (not 'env_')
```

## Use Cases

### Multi-Tenant Application

```python
def create_tenant_source(tenant_id, db_connection):
    """Create isolated prompt source per tenant."""
    prefix = f"tenant_{tenant_id}_"
    return DatabaseSource(db_connection, table_prefix=prefix)

# Each tenant gets isolated tables
tenant1_source = create_tenant_source(1, conn)
tenant2_source = create_tenant_source(2, conn)
```

### Development/Testing

```python
# Development database
os.environ['PROMPT_ASSEMBLE_TABLE_PREFIX'] = 'dev_'
dev_source = DatabaseSource(dev_conn)

# Test database (in same instance)
test_source = DatabaseSource(test_conn, table_prefix='test_')
```

### Multiple Application Instances

```python
# App 1
source1 = DatabaseSource(conn, table_prefix='app1_')

# App 2 (same database)
source2 = DatabaseSource(conn, table_prefix='app2_')
```

## Schema

All tables are created automatically with the specified prefix:

### With Prefix: `myapp_`

```sql
CREATE TABLE myapp_prompts (...)
CREATE TABLE myapp_prompt_registry (...)
CREATE TABLE myapp_prompt_tags (...)
CREATE TABLE myapp_prompt_versions (...)
```

### Without Prefix (empty string)

```sql
CREATE TABLE prompts (...)
CREATE TABLE prompt_registry (...)
CREATE TABLE prompt_tags (...)
CREATE TABLE prompt_versions (...)
```

## Database Schema Details

### Table: `{prefix}prompts`
- `id` (TEXT, PRIMARY KEY)
- `name` (TEXT, UNIQUE)
- `content` (TEXT)
- `version` (INTEGER)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Table: `{prefix}prompt_registry`
- `id` (TEXT, PRIMARY KEY)
- `prompt_id` (TEXT, FK to prompts)
- `description` (TEXT)
- `owner` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

### Table: `{prefix}prompt_tags`
- `prompt_id` (TEXT, FK to prompts)
- `tag` (TEXT)
- `PRIMARY KEY (prompt_id, tag)`

### Table: `{prefix}prompt_versions`
- `id` (TEXT, PRIMARY KEY)
- `prompt_id` (TEXT, FK to prompts)
- `version` (INTEGER)
- `content` (TEXT)
- `created_at` (TIMESTAMP)
- `UNIQUE(prompt_id, version)`

## Examples

### Example 1: Simple Prefix

```python
import sqlite3
from prompt_assemble.sources import DatabaseSource

conn = sqlite3.connect('mydb.sqlite3')
source = DatabaseSource(conn, table_prefix='prompts_')

# Tables created: prompts_prompts, prompts_prompt_registry, ...
source.save_prompt('greeting', 'Hello!', tags=['greeting'])
```

### Example 2: Multi-Tenant

```python
import sqlite3
from prompt_assemble.sources import DatabaseSource

conn = sqlite3.connect('multitenant.db')

# Tenant A
tenant_a = DatabaseSource(conn, table_prefix='tenant_a_')
tenant_a.save_prompt('greeting', 'Hola!', tags=['es'])

# Tenant B
tenant_b = DatabaseSource(conn, table_prefix='tenant_b_')
tenant_b.save_prompt('greeting', 'Hello!', tags=['en'])

# Each has independent data
assert tenant_a.get_raw('greeting') == 'Hola!'
assert tenant_b.get_raw('greeting') == 'Hello!'
```

### Example 3: Environment Variable

```bash
# Set prefix for all DatabaseSource instances
export PROMPT_ASSEMBLE_TABLE_PREFIX=production_

# In Python
import sqlite3
from prompt_assemble.sources import DatabaseSource

conn = sqlite3.connect('prod.db')
source = DatabaseSource(conn)  # Uses production_ prefix from env

# Tables: production_prompts, production_prompt_registry, ...
```

### Example 4: With UI Server

```python
import os
from prompt_assemble.sources import DatabaseSource
from prompt_assemble.api import run_server
import sqlite3

# Set up multi-tenant database
os.environ['PROMPT_ASSEMBLE_TABLE_PREFIX'] = 'ui_'

conn = sqlite3.connect('prompts.db')
source = DatabaseSource(conn)

# UI will use prefixed tables
run_server(source=source, port=5000)
```

## Testing

### Verify Prefix is Applied

```python
import sqlite3
from prompt_assemble.sources import DatabaseSource

conn = sqlite3.connect(':memory:')
source = DatabaseSource(conn, table_prefix='test_')

cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(tables)
# Output: ['test_prompts', 'test_prompt_registry', 'test_prompt_tags', 'test_prompt_versions']
```

### Running Tests

```bash
# Run prefix-specific tests
python -m pytest tests/test_database_prefix.py -v

# All tests
python -m pytest tests/ -v
```

## Important Notes

1. **Prefix Format**: Use alphanumeric characters and underscores. Common patterns:
   - `app_` - application name
   - `tenant_a_` - tenant identifier
   - `test_` - testing environment
   - `dev_` - development environment

2. **SQL Injection**: The prefix is NOT user-input validated in constructor for flexibility. If accepting user input, validate it:
   ```python
   import re

   def validate_prefix(prefix: str) -> bool:
       return bool(re.match(r'^[a-z0-9_]*$', prefix))

   if validate_prefix(user_prefix):
       source = DatabaseSource(conn, table_prefix=user_prefix)
   ```

3. **Backward Compatibility**: Existing code without prefix continues to work unchanged:
   ```python
   source = DatabaseSource(conn)  # No prefix, uses default tables
   ```

4. **Migration**: To migrate from no prefix to prefixed tables:
   ```sql
   -- Rename existing tables
   ALTER TABLE prompts RENAME TO app_prompts;
   ALTER TABLE prompt_registry RENAME TO app_prompt_registry;
   ALTER TABLE prompt_tags RENAME TO app_prompt_tags;
   ALTER TABLE prompt_versions RENAME TO app_prompt_versions;
   ```

5. **Performance**: The prefix is just a string prepended to table names. No performance impact.

## Troubleshooting

### Issue: Tables Not Found

If you get "no such table" errors, verify:

1. Check the prefix value:
   ```python
   print(source.table_prefix)  # Should show your prefix
   ```

2. Verify tables exist:
   ```python
   cursor = conn.cursor()
   cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
   print(cursor.fetchall())
   ```

3. Ensure consistency across calls:
   ```python
   # Wrong: Different prefixes
   source1 = DatabaseSource(conn, table_prefix='app_')
   source2 = DatabaseSource(conn, table_prefix='other_')
   # Each creates different tables

   # Right: Same prefix
   source1 = DatabaseSource(conn, table_prefix='app_')
   source2 = DatabaseSource(conn, table_prefix='app_')
   # Both access same tables
   ```

### Issue: Environment Variable Not Applied

Verify the environment variable is set:

```bash
# Check it's set
echo $PROMPT_ASSEMBLE_TABLE_PREFIX

# Set it for current session
export PROMPT_ASSEMBLE_TABLE_PREFIX=myapp_

# Verify
python -c "from prompt_assemble.sources import DatabaseSource; import sqlite3; s = DatabaseSource(sqlite3.connect(':memory:')); print(s.table_prefix)"
```

## API Reference

### DatabaseSource Constructor

```python
DatabaseSource(
    connection: Any,
    table_prefix: Optional[str] = None
) -> DatabaseSource
```

**Parameters:**
- `connection`: DBAPI2-compatible database connection
- `table_prefix`: Optional table name prefix. If not provided, reads from `PROMPT_ASSEMBLE_TABLE_PREFIX` environment variable. Defaults to empty string.

**Returns:** DatabaseSource instance

**Raises:** SourceConnectionError if connection is invalid

### Properties

```python
source.table_prefix: str  # Read-only table prefix
```

### Internal Method

```python
source._table(name: str) -> str  # Get prefixed table name
```

## See Also

- [DatabaseSource Documentation](../README.md)
- [Test File](../../tests/test_database_prefix.py)
- [Example Usage](../ui/example_usage.py)
