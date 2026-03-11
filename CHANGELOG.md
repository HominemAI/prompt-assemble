# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.12] - 2026-03-11

### Fixed

- **Docker Image Flask Dependencies**: Docker builds now include Flask and Flask-CORS via `.[ui-full]` extras
  - Prevents "ModuleNotFoundError: No module named 'flask'" at runtime
  - Both Dockerfile and Dockerfile.unified updated with explicit Flask installation

- **Variable Sets API Endpoint**: `/api/variable-sets` now uses Python library method for proper table prefix support
  - Changed from direct SQL queries to `app.prompt_source.list_variable_sets()`
  - Ensures table prefixes are applied correctly (fixes multi-tenancy scenarios)
  - Matches approach used for prompts endpoint

- **API Error Handling**: Improved logging for variable sets endpoint
  - Now returns actual error messages instead of silent failures
  - Logs when file-based source is used instead of database
  - Better debugging visibility with warning-level logs

## [0.3.7] - 2026-03-10

### Changed

- **Undefined Variable Handling**: Undefined variables during substitution are now logged as warnings and replaced with empty strings instead of raising `ValueError`
  - Improves resilience of prompt rendering when variables are missing
  - Logged at WARNING level for debugging purposes
  - Allows prompts to render gracefully even with incomplete variable sets

## [0.3.6] - 2026-03-10

### Added

- **Tagged Variables**: Variables can now carry optional XML wrapper tags
  - Format: `{"value": "expert", "tag": "persona"}` renders as `<persona>\n  expert\n</persona>`
  - Backward compatible with simple strings: `{"KEY": "value"}` still works
  - Tag resolution in `render()` via `_resolve_variable_value()` helper

- **Variable Set Rendering**: `render()` now accepts `variable_sets` parameter
  - Explicit variable set IDs passed to render with automatic merging
  - Priority hierarchy: subscriptions < additional_sets < per-prompt_overrides < explicit_variables
  - `_resolve_variable_sets()` helper implements merge logic with proper precedence

- **Granular Variable Operations**:
  - `add_variable_to_set(set_id, key, value, tag=None)` - Add/update single variable without full-swap
  - `remove_variable_from_set(set_id, key)` - Remove single variable
  - Both available in DatabaseSource, FileSystemSource, and PromptProvider

- **Variable Set Discovery**:
  - `find_variable_sets(name=None, owner=None, match_type="exact"|"partial")` - Search by name and/or owner
  - Exact and partial name matching support
  - Owner-scoped filtering for multi-tenant scenarios

- **Owner Scoping for Variable Sets**:
  - `list_global_variable_sets()` - Returns only sets with `owner=None`
  - `list_variable_sets_by_owner(owner)` - Filter by owner
  - `get_available_variable_sets(owner)` - Returns global + owner-scoped sets

- **REST API Endpoints**:
  - `GET /api/variable-sets/<id>` - Get specific variable set with full variables
  - `PUT /api/variable-sets/<id>` - Update variable set (name, owner, variables)
  - `POST /api/variable-sets/<id>/variables` - Add/update single variable with tag support
  - `DELETE /api/variable-sets/<id>/variables/<key>` - Remove single variable
  - `POST /api/variable-sets/find` - Find sets by name and/or owner
  - `POST /api/prompts/<name>/render` - Render with `variable_sets` parameter

- **Database Schema**:
  - Added `tag TEXT` column to `variable_set_variables` table
  - Auto-migration in `_ensure_schema()` handles existing databases gracefully

### Changed

- `PromptProvider` render signature now includes `variable_sets: Optional[List[str]] = None`
- Variable set CRUD methods now support owner field (nullable)
- FileSystemSource variable storage now uses JSON format for tagged variables

## [0.3.3] - 2026-03-09

### Fixed

- FileSystemSource naming convention now matches UI implementation: prompt names are just filenames without directory paths
  - Previously: nested files were named with full path (e.g., `personas_expert` for `personas/expert.prompt`)
  - Now: names use only the filename (e.g., `expert`)
  - Directory structure is still tracked in registry metadata

## [0.1.0] - 2025-02-28

### Added

- Initial release of prompt-assemble
- Sigil-based substitution engine (`[[VAR_NAME]]` and `[[PROMPT: name]]`)
- Support for loose XML, JSON, and plain text templates
- Recursive variable substitution
- Comment stripping (`#!` and `<!-- -->`)
- CLI tool (`pambl`)
- Comprehensive test suite
