# Loading the Research Paper System into PostgreSQL

This guide explains how to load all 14 prompts, their tags, and 6 variable sets into your PostgreSQL database.

## Prerequisites

1. PostgreSQL installed and running
2. Database created and schema initialized by `DatabaseSource._ensure_schema()`
3. Environment variables configured (or use psql flags)

## Quick Start

```bash
# Method 1: Using environment variables
export DB_HOSTNAME=localhost
export DB_USERNAME=postgres
export DB_PASSWORD=your_password
export DB_DATABASE=prompts

psql -h $DB_HOSTNAME -U $DB_USERNAME -d $DB_DATABASE -f load_to_postgres.sql

# Method 2: Direct command
psql -h localhost -U postgres -d prompts -f load_to_postgres.sql
```

## What Gets Loaded

### Prompts (14 total)

| Prompt                          | Type         | Purpose                                    |
|---------------------------------|--------------|--------------------------------------------|
| `research_paper_generator`      | Orchestrator | Main entry point coordinating all sections |
| `abstract_template`             | Template     | Reusable abstract section                  |
| `research_instructions`         | Template     | Research methodology guidelines            |
| `methodology_template`          | Template     | Detailed methodology structure             |
| `validation_checklist`          | Template     | Quality validation checklist               |
| `reference_guidelines`          | Template     | Citation and reference standards           |
| `example_ai_research`           | Case Study   | AI in computer science research            |
| `example_biomedical_study`      | Case Study   | AI in drug discovery                       |
| `example_social_science`        | Case Study   | NLP in social science research             |
| `foundational_machine_learning` | Reference    | ML concepts and principles                 |
| `foundational_statistics`       | Reference    | Statistical hypothesis testing             |
| `foundational_research_ethics`  | Reference    | Research ethics and IRB                    |
| `example_citation_ml`           | Example      | ML citation examples                       |
| `example_citation_statistics`   | Example      | Statistics citation examples               |

### Tags (63 total across prompts)

Organized by category:

- **Template tags**: template, academic, methods
- **Case study tags**: case_study, practical_example
- **Reference tags**: reference, foundational
- **Domain tags**: ai, machine_learning, statistics, biomedical, psychology, etc.

### Variable Sets (6 total)

1. **General Research Settings** (14 variables)
    - Paper metadata, subject area, problem statement, thesis, etc.

2. **Academic Style - PhD Level** (14 variables)
    - Methodology details, audience level, research design, tools, etc.

3. **Validation Framework** (5 variables)
    - Validity checks, review authority, validation method

4. **Citation & References** (5 variables)
    - Citation style, minimum references, recency standards, authority levels

5. **Success Metrics** (3 variables)
    - Metrics, findings summary, field implications

6. **Results Presentation** (1 variable)
    - Results presentation style

**Total: 47 variables**

## Database Schema

The script assumes the following tables exist (created by `DatabaseSource._ensure_schema()`):

```sql
-- Prompts storage
CREATE TABLE prompts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) UNIQUE NOT NULL,
  content TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Prompt metadata
CREATE TABLE prompt_registry (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  prompt_id UUID UNIQUE REFERENCES prompts(id),
  description TEXT,
  owner VARCHAR(255),
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Prompt tags
CREATE TABLE prompt_tags (
  prompt_id UUID REFERENCES prompts(id),
  tag VARCHAR(255),
  PRIMARY KEY (prompt_id, tag)
);

-- Variable sets
CREATE TABLE variable_sets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Variables within sets
CREATE TABLE variable_set_variables (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  variable_set_id UUID REFERENCES variable_sets(id),
  key VARCHAR(255) NOT NULL,
  value TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE (variable_set_id, key)
);
```

## Using the Loaded Prompts

### In Python

```python
from prompt_assemble.sources import DatabaseSource, create_database_source_from_env
from prompt_assemble import PromptProvider
import psycopg2

# Method 1: Using environment variables
source = create_database_source_from_env()

# Method 2: Direct connection
conn = psycopg2.connect("dbname=prompts user=postgres")
source = DatabaseSource(conn)

# Create provider
provider = PromptProvider(source)

# List all prompts
print(provider.list())

# Find by tags (AND intersection)
case_studies = provider.find_by_tag("case_study", "practical_example")
print(case_studies)
# Output: ['example_ai_research', 'example_biomedical_study', 'example_social_science']

# Render with variables
variables = {
    "PAPER_TITLE": "My Research Paper",
    "AUTHOR_NAME": "My Name",
    # ... all 47 variables from variable sets ...
}

output = provider.render("research_paper_generator", variables=variables)
```

### In Web UI

```bash
# Build the frontend
cd src/prompt_assemble/api/frontend
npm run build

# Configure environment
export PROMPT_ASSEMBLE_UI=true
export PROMPT_ASSEMBLE_SOURCE=database
export DB_HOSTNAME=localhost
export DB_USERNAME=postgres
export DB_PASSWORD=your_password
export DB_DATABASE=prompts

# Start server
cd ../
python -m prompt_assemble.api.server

# Open http://localhost:8000
```

In the UI:

1. Prompts automatically appear in the explorer
2. Tags enable filtering and searching
3. Variable sets can be created and subscribed to documents

## SQL Script Breakdown

The `load_to_postgres.sql` script has 5 sections:

### Section 1: Insert Prompts

Loads all 14 .prompt files as records in the `prompts` table. Uses `ON CONFLICT (name) DO UPDATE` to allow re-running
the script.

### Section 2: Insert Metadata

Adds descriptions and owner information to `prompt_registry` for each prompt.

### Section 3: Insert Tags

Applies 63 tags across the 14 prompts using `prompt_tags` table.

### Section 4: Create Variable Sets

Creates 6 named variable sets in the `variable_sets` table.

### Section 5: Populate Variables

Inserts 47 variables across the 6 sets in `variable_set_variables` table.

## Verifying the Load

After running the script, verify the load:

```sql
-- Check prompts loaded
SELECT COUNT(*) FROM prompts;
-- Output: 14

-- Check tags applied
SELECT COUNT(DISTINCT prompt_id) FROM prompt_tags;
-- Output: 14

-- Check total tags
SELECT COUNT(*) FROM prompt_tags;
-- Output: 63

-- Check variable sets created
SELECT COUNT(*) FROM variable_sets;
-- Output: 6

-- Check variables populated
SELECT COUNT(*) FROM variable_set_variables;
-- Output: 47

-- List all prompts
SELECT name FROM prompts ORDER BY name;

-- Find prompts by tag
SELECT DISTINCT p.name FROM prompts p
  JOIN prompt_tags t ON p.id = t.prompt_id
  WHERE t.tag = 'case_study'
  ORDER BY p.name;

-- List variable sets and their variable counts
SELECT vs.name, COUNT(vsv.id) as variable_count
  FROM variable_sets vs
  LEFT JOIN variable_set_variables vsv ON vs.id = vsv.variable_set_id
  GROUP BY vs.id, vs.name
  ORDER BY vs.name;
```

## Re-running the Script

The script is idempotent (safe to run multiple times):

- `ON CONFLICT (name) DO UPDATE` for prompts ensures old content is updated
- `ON CONFLICT DO NOTHING` for tags and variables prevents duplicates

To fully reset:

```bash
# WARNING: This deletes all data
psql -h localhost -U postgres -d prompts -c "
  DELETE FROM variable_set_variables;
  DELETE FROM variable_sets;
  DELETE FROM prompt_tags;
  DELETE FROM prompt_registry;
  DELETE FROM prompts;
"

# Then reload
psql -h localhost -U postgres -d prompts -f load_to_postgres.sql
```

## Troubleshooting

### "FATAL: role "postgres" does not exist"

```bash
# Use your actual PostgreSQL user
psql -h localhost -U your_username -d prompts -f load_to_postgres.sql
```

### "FATAL: database "prompts" does not exist"

```bash
# Create database first
createdb -U postgres prompts
# Or with psql
psql -U postgres -c "CREATE DATABASE prompts;"
```

### "ERROR: relation "prompts" does not exist"

The schema hasn't been initialized. Initialize it first:

```python
from prompt_assemble.sources import DatabaseSource
import psycopg2

conn = psycopg2.connect("dbname=prompts user=postgres")
source = DatabaseSource(conn)  # This creates the schema
```

Then run the SQL script.

### "ERROR: syntax error in SQL"

Make sure you're using the correct PostgreSQL version. The script uses:

- `gen_random_uuid()` (PostgreSQL 9.4+)
- `ON CONFLICT` clauses (PostgreSQL 9.5+)

## Integration with Variable Sets Feature

The 6 variable sets loaded work seamlessly with the web UI's variable sets feature:

1. **Create Document**: In web UI, create a new research paper document
2. **Subscribe to Sets**: Click "Variables" → "Select Variable Sets"
3. **Choose Sets**: Select any combination of the 6 variable sets
4. **Override Variables**: Customize specific variables for this document
5. **Render**: Click "Render" button to generate output with merged variables

Example workflow:

- Document subscribes to: "General Research Settings" + "Academic Style - PhD Level"
- Override: `AUTHOR_NAME` → "Your Name", `INSTITUTION` → "Your University"
- Render: All variables merged and substituted into the complete paper

## Customization

To modify the loaded data:

### Add New Prompt

```sql
INSERT INTO prompts (name, content) VALUES
  ('my_new_prompt', 'Content here with [[VARIABLES]]');

INSERT INTO prompt_registry (prompt_id, description, owner) VALUES
  ((SELECT id FROM prompts WHERE name = 'my_new_prompt'),
   'Description',
   'team-name');

INSERT INTO prompt_tags (prompt_id, tag) VALUES
  ((SELECT id FROM prompts WHERE name = 'my_new_prompt'), 'my_tag');
```

### Add New Variable to Existing Set

```sql
INSERT INTO variable_set_variables (variable_set_id, name, value) VALUES
  ((SELECT id FROM variable_sets WHERE name = 'General Research Settings'),
   'NEW_VARIABLE',
   'New value here');
```

### Create New Variable Set

```sql
INSERT INTO variable_sets (name) VALUES ('My New Set');

INSERT INTO variable_set_variables (variable_set_id, name, value) VALUES
  ((SELECT id FROM variable_sets WHERE name = 'My New Set'),
   'VAR1', 'value1'),
  ((SELECT id FROM variable_sets WHERE name = 'My New Set'),
   'VAR2', 'value2');
```

## Performance Notes

- 14 prompts with average 1.2KB each ≈ 17KB total
- 63 tags create minimal overhead
- Variable lookups use indexed variable_set_id
- Tag searching uses sequential scan (acceptable for small sets)

For larger deployments (100+ prompts), consider:

- Creating indexes on `prompt_tags.tag`
- Caching tag lists in application layer
- Pagination in UI for large lists

