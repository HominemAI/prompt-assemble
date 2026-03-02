"""
Flask/FastAPI server for the prompt management UI.

Provides REST API endpoints for:
- Listing prompts
- CRUD operations on prompts
- Tag management
- Revision history
- Export functionality
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Path to frontend static files (built by Vite)
STATIC_DIR = Path(__file__).parent / "static"
FRONTEND_DIR = Path(__file__).parent / "frontend"


def create_app(source=None, config=None):
    """
    Create the Flask/FastAPI application.

    Args:
        source: PromptSource instance for managing prompts
        config: Configuration dict with defaults

    Returns:
        Flask or FastAPI app instance
    """
    try:
        from flask import Flask, jsonify, request
    except ImportError:
        logger.error(
            "Flask not installed. Install with: pip install flask flask-cors"
        )
        return None

    # Configure Flask to serve built React app from static directory
    app = Flask(
        __name__,
        static_folder=str(STATIC_DIR),
        static_url_path="/static"
    )

    if config:
        app.config.update(config)

    # Store source in app context
    app.prompt_source = source

    # Import CORS support
    try:
        from flask_cors import CORS

        CORS(app)
    except ImportError:
        logger.warning("flask-cors not installed, CORS support disabled")

    # ====== Root Routes ======

    @app.route("/")
    def index():
        """Serve the React app index.html"""
        index_path = STATIC_DIR / "index.html"
        if index_path.exists():
            return app.send_static_file("index.html")
        else:
            # Development: return inline HTML if build doesn't exist
            logger.warning("Static files not built. Run: npm run build in the frontend directory")
            return _get_index_html()

    @app.route("/favicon.svg")
    def serve_favicon():
        """Serve favicon at root level"""
        favicon_path = STATIC_DIR / "favicon.svg"
        if favicon_path.exists():
            return app.send_static_file("favicon.svg")
        return "", 404

    @app.route("/assets/<path:filename>")
    def serve_assets(filename):
        """Serve static assets (JS, CSS, etc.)"""
        return app.send_static_file(f"assets/{filename}")

    @app.route("/logos/<path:filename>")
    def serve_logos(filename):
        """Serve logo files"""
        return app.send_static_file(f"logos/{filename}")

    # ====== API Routes ======

    @app.route("/api/prompts", methods=["GET"])
    def list_prompts():
        """List all available prompts with metadata."""
        if not app.prompt_source:
            return jsonify({"error": "No prompt source configured"}), 500

        try:
            import time
            start_time = time.time()

            all_prompt_names = app.prompt_source.list()
            logger.info(f"[list_prompts] Total prompts in source: {len(all_prompt_names)}")

            # Pre-fetch all timestamps if using database source (avoid N+1 queries)
            timestamps = {}
            if hasattr(app.prompt_source, 'connection'):
                try:
                    logger.info("[list_prompts] Attempting to fetch timestamps from database")
                    cursor = app.prompt_source.connection.cursor()
                    try:
                        cursor.execute(f"SELECT name, updated_at FROM {app.prompt_source._table('prompts')}")
                        rows = cursor.fetchall()
                        logger.info(f"[list_prompts] Fetched {len(rows)} timestamps from database")
                        for row in rows:
                            timestamps[row[0]] = row[1]
                    finally:
                        cursor.close()
                except Exception as db_error:
                    logger.error(f"[list_prompts] DATABASE ERROR: Failed to fetch timestamps from database: {type(db_error).__name__}: {db_error}")
                    logger.error(f"[list_prompts] Database connection details: {app.prompt_source.connection if hasattr(app.prompt_source, 'connection') else 'No connection object'}")
                    # Continue without timestamps rather than failing completely
                    logger.warning("[list_prompts] Proceeding without database timestamps")

            prompts = []
            skipped_count = 0
            for name in all_prompt_names:
                # Filter out "Untitled" or "untitled" prompts
                if name.lower() == "untitled":
                    skipped_count += 1
                    continue

                prompt_data = _get_prompt_metadata(app.prompt_source, name)
                # Add pre-fetched timestamp
                if name in timestamps and timestamps[name]:
                    prompt_data['updated_at'] = timestamps[name].isoformat()
                prompts.append(prompt_data)

            elapsed = time.time() - start_time
            logger.info(f"[list_prompts] Returned {len(prompts)} prompts (skipped {skipped_count} untitled), took {elapsed:.3f}s")

            return jsonify({"prompts": prompts})
        except Exception as e:
            logger.error(f"Error listing prompts: {type(e).__name__}: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/prompts/search", methods=["GET"])
    def search_prompts():
        """Search prompts by name and/or tags."""
        query = request.args.get("q", "").lower()
        tags = request.args.getlist("tags")

        if not app.prompt_source:
            return jsonify({"error": "No prompt source configured"}), 500

        try:
            results = []

            # Get all prompts
            all_names = app.prompt_source.list()

            # Filter by tags if provided
            if tags:
                tagged = app.prompt_source.find_by_tag(*tags)
                all_names = [n for n in all_names if n in tagged]

            # Filter by query
            for name in all_names:
                if query in name.lower():
                    prompt_data = _get_prompt_metadata(app.prompt_source, name)
                    results.append(prompt_data)

            return jsonify({"results": results})
        except Exception as e:
            logger.error(f"Error searching prompts: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/prompts/<name>", methods=["GET"])
    def get_prompt(name):
        """Get full prompt content."""
        if not app.prompt_source:
            return jsonify({"error": "No prompt source configured"}), 500

        try:
            content = app.prompt_source.get_raw(name)
            metadata = _get_prompt_metadata(app.prompt_source, name)
            return jsonify({"name": name, "content": content, "metadata": metadata})
        except Exception as e:
            logger.error(f"Error getting prompt {name}: {e}")
            return jsonify({"error": str(e)}), 404

    @app.route("/api/prompts/<name>", methods=["POST"])
    def save_prompt(name):
        """Save or update a prompt."""
        if not app.prompt_source:
            return jsonify({"error": "No prompt source configured"}), 500

        # Prevent saving prompts named "Untitled" (case-insensitive)
        if name.lower() == "untitled" or not name.strip():
            return jsonify({"error": "Prompt name cannot be 'Untitled' or empty"}), 400

        try:
            data = request.json
            content = data.get("content")
            metadata = data.get("metadata", {})
            is_backend_save = data.get("isBackendSave", True)  # Default to True for backward compatibility

            if not content:
                return jsonify({"error": "Content required"}), 400

            # Save depending on source type
            if hasattr(app.prompt_source, "save_prompt"):
                prompt_id = app.prompt_source.save_prompt(
                    name=name,
                    content=content,
                    description=metadata.get("description", ""),
                    tags=metadata.get("tags", []),
                    owner=metadata.get("owner"),
                    increment_version=is_backend_save,
                    revision_comment=metadata.get("revisionComments"),
                )
                return jsonify(
                    {
                        "success": True,
                        "name": name,
                        "prompt_id": prompt_id,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
            else:
                return (
                    jsonify(
                        {
                            "error": "Source does not support saving",
                        }
                    ),
                    400,
                )
        except Exception as e:
            logger.error(f"Error saving prompt {name}: {e}")
            return jsonify({"error": str(e)}), 500

    @app.route("/api/prompts/<name>", methods=["DELETE"])
    def delete_prompt(name):
        """Delete a prompt (if source supports it)."""
        logger.info(f"DELETE request for prompt: {name}")
        if not app.prompt_source:
            logger.error("No prompt source configured")
            return jsonify({"error": "No prompt source configured"}), 500

        try:
            if hasattr(app.prompt_source, "delete_prompt"):
                logger.info(f"Deleting prompt: {name}")
                app.prompt_source.delete_prompt(name)
                logger.info(f"Successfully deleted prompt: {name}")
                return jsonify({"success": True, "deleted": name})
            else:
                logger.error(f"Source does not support deletion for: {name}")
                return (
                    jsonify(
                        {
                            "error": "Source does not support deletion",
                        }
                    ),
                    400,
                )
        except Exception as e:
            logger.error(f"Error deleting prompt {name}: {e}")
            # Return 404 if prompt not found, otherwise return 500
            if "not found" in str(e).lower():
                logger.warning(f"Prompt not found: {name}")
                return jsonify({"error": "Prompt not found"}), 404
            return jsonify({"error": str(e)}), 500

    @app.route("/api/prompts/<name>/variable-sets", methods=["GET"])
    def get_prompt_variable_sets(name):
        """Get variable set subscriptions for a prompt/document."""
        if not hasattr(app.prompt_source, 'connection'):
            return jsonify({"variableSetIds": [], "overrides": {}}), 200

        cursor = None
        try:
            cursor = app.prompt_source.connection.cursor()
            table_prefix = getattr(app.prompt_source, 'table_prefix', '')

            # Get the prompt ID
            cursor.execute(
                f"SELECT id FROM {table_prefix}prompts WHERE name = %s",
                (name,)
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"variableSetIds": [], "overrides": {}}), 200

            prompt_id = row[0]

            # Get variable set subscriptions
            cursor.execute(
                f"SELECT variable_set_id FROM {table_prefix}variable_set_selections WHERE prompt_id = %s ORDER BY list_order",
                (prompt_id,)
            )
            variable_set_ids = [row[0] for row in cursor.fetchall()]

            # Get overrides
            cursor.execute(
                f"SELECT variable_set_id, key, override_value FROM {table_prefix}variable_set_overrides WHERE prompt_id = %s",
                (prompt_id,)
            )

            overrides = {}
            for var_set_id, key, value in cursor.fetchall():
                if var_set_id not in overrides:
                    overrides[var_set_id] = {}
                overrides[var_set_id][key] = value

            return jsonify({"variableSetIds": variable_set_ids, "overrides": overrides}), 200
        except Exception as e:
            logger.error(f"Error getting variable sets for {name}: {e}")
            return jsonify({"variableSetIds": [], "overrides": {}}), 200
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    logger.debug(f"Error closing cursor: {e}")

    @app.route("/api/prompts/<name>/variable-sets", methods=["POST"])
    def save_prompt_variable_sets(name):
        """Save variable set subscriptions for a prompt/document."""
        if not hasattr(app.prompt_source, 'connection'):
            return jsonify({"error": "Database source not available"}), 400

        cursor = None
        try:
            data = request.json
            variable_set_ids = data.get("variableSetIds", [])
            overrides = data.get("overrides", {})

            cursor = app.prompt_source.connection.cursor()
            table_prefix = getattr(app.prompt_source, 'table_prefix', '')

            # Get the prompt ID
            cursor.execute(
                f"SELECT id FROM {table_prefix}prompts WHERE name = %s",
                (name,)
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Prompt not found"}), 404

            prompt_id = row[0]

            # Clear existing subscriptions
            cursor.execute(
                f"DELETE FROM {table_prefix}variable_set_selections WHERE prompt_id = %s",
                (prompt_id,)
            )

            # Insert new subscriptions
            for order, var_set_id in enumerate(variable_set_ids):
                cursor.execute(
                    f"INSERT INTO {table_prefix}variable_set_selections (id, prompt_id, variable_set_id, list_order, created_at, updated_at) VALUES (gen_random_uuid(), %s, %s, %s, NOW(), NOW())",
                    (prompt_id, var_set_id, order)
                )

            # Clear existing overrides
            cursor.execute(
                f"DELETE FROM {table_prefix}variable_set_overrides WHERE prompt_id = %s",
                (prompt_id,)
            )

            # Insert new overrides
            for var_set_id, var_overrides in overrides.items():
                for key, value in var_overrides.items():
                    cursor.execute(
                        f"INSERT INTO {table_prefix}variable_set_overrides (id, prompt_id, variable_set_id, key, override_value, created_at, updated_at) VALUES (gen_random_uuid(), %s, %s, %s, %s, NOW(), NOW())",
                        (prompt_id, var_set_id, key, value)
                    )

            app.prompt_source.connection.commit()
            return jsonify({"success": True, "name": name}), 200
        except Exception as e:
            logger.error(f"Error saving variable sets for {name}: {e}")
            try:
                app.prompt_source.connection.rollback()
            except:
                pass
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    logger.debug(f"Error closing cursor: {e}")

    @app.route("/api/prompts/<name>/revert/<int:version>", methods=["POST"])
    def revert_prompt(name, version):
        """Revert a prompt to a previous version."""
        if not hasattr(app.prompt_source, 'connection'):
            return jsonify({"error": "Database not available"}), 500

        cursor = None
        try:
            cursor = app.prompt_source.connection.cursor()
            table_prefix = getattr(app.prompt_source, 'table_prefix', '')

            # Get the prompt ID
            cursor.execute(
                f"SELECT id FROM {table_prefix}prompts WHERE name = %s",
                (name,)
            )
            row = cursor.fetchone()
            if not row:
                return jsonify({"error": "Prompt not found"}), 404

            prompt_id = row[0]
            logger.debug(f"[revert_prompt] Reverting {name} to version {version}")

            # Get the specified version's content
            cursor.execute(
                f"SELECT content FROM {table_prefix}prompt_versions WHERE prompt_id = %s AND version = %s",
                (prompt_id, version)
            )
            version_row = cursor.fetchone()
            if not version_row:
                return jsonify({"error": f"Version {version} not found"}), 404

            old_content = version_row[0]
            revision_comment = f"Reverted to version {version}"

            # Get current version number to determine new version
            cursor.execute(
                f"SELECT version FROM {table_prefix}prompts WHERE id = %s",
                (prompt_id,)
            )
            current_version = cursor.fetchone()[0]
            new_version = current_version + 1

            # Update prompt with old content and new version
            cursor.execute(
                f"UPDATE {table_prefix}prompts SET content = %s, version = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (old_content, new_version, prompt_id)
            )

            # Create new version history entry
            cursor.execute(
                f"INSERT INTO {table_prefix}prompt_versions (id, prompt_id, version, content, revision_comment) VALUES (%s, %s, %s, %s, %s)",
                (str(__import__('uuid').uuid4()), prompt_id, new_version, old_content, revision_comment)
            )

            app.prompt_source.connection.commit()

            logger.info(f"[revert_prompt] Successfully reverted {name} to version {version} (new version: {new_version})")
            return jsonify({
                "success": True,
                "name": name,
                "newVersion": new_version,
                "content": old_content,
                "revisionComment": revision_comment,
                "timestamp": datetime.utcnow().isoformat()
            }), 200

        except Exception as e:
            logger.error(f"[revert_prompt] Error reverting {name} to version {version}: {e}", exc_info=True)
            try:
                if hasattr(app.prompt_source, 'connection'):
                    app.prompt_source.connection.rollback()
            except:
                pass
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    logger.debug(f"Error closing cursor: {e}")

    @app.route("/api/prompts/<name>/history", methods=["GET"])
    def get_prompt_history(name):
        """Get version history for a prompt (max 20 revisions)."""
        if not hasattr(app.prompt_source, 'connection'):
            logger.debug(f"[get_prompt_history] No database connection for {name}")
            return jsonify({"versions": []}), 200

        cursor = None
        try:
            import uuid
            cursor = app.prompt_source.connection.cursor()
            table_prefix = getattr(app.prompt_source, 'table_prefix', '')
            logger.debug(f"[get_prompt_history] Fetching history for {name} (prefix: '{table_prefix}')")

            # Get the prompt ID and current version
            cursor.execute(
                f"SELECT id, content, version FROM {table_prefix}prompts WHERE name = %s",
                (name,)
            )
            row = cursor.fetchone()
            if not row:
                logger.debug(f"[get_prompt_history] Prompt not found: {name}")
                return jsonify({"versions": []}), 200

            prompt_id, current_content, current_version = row[0], row[1], row[2]
            logger.debug(f"[get_prompt_history] Found prompt {name} with id {prompt_id}, version {current_version}")

            # Check if this prompt has any version history
            cursor.execute(
                f"SELECT COUNT(*) FROM {table_prefix}prompt_versions WHERE prompt_id = %s",
                (prompt_id,)
            )
            version_count = cursor.fetchone()[0]
            logger.debug(f"[get_prompt_history] Prompt has {version_count} version history entries")

            # If no version history exists, create an initial entry for the current state
            if version_count == 0:
                logger.info(f"[get_prompt_history] Creating initial version history for {name}")
                cursor.execute(
                    f"INSERT INTO {table_prefix}prompt_versions (id, prompt_id, version, content, revision_comment, created_at) VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)",
                    (str(uuid.uuid4()), prompt_id, current_version, current_content, '')
                )
                app.prompt_source.connection.commit()
                version_count = 1

            # Get all versions ordered by version descending (most recent first), limited to 20
            cursor.execute(
                f"SELECT version, content, created_at, revision_comment FROM {table_prefix}prompt_versions WHERE prompt_id = %s ORDER BY version DESC LIMIT 20",
                (prompt_id,)
            )

            rows = cursor.fetchall()
            logger.debug(f"[get_prompt_history] Returning {len(rows)} versions for {name}")

            versions = []
            for version, content, created_at, revision_comment in rows:
                versions.append({
                    "version": version,
                    "content": content,
                    "createdAt": created_at.isoformat() if created_at else None,
                    "revisionComment": revision_comment or ""
                })

            return jsonify({"versions": versions}), 200
        except Exception as e:
            logger.error(f"[get_prompt_history] Error getting version history for {name}: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    logger.debug(f"Error closing cursor: {e}")

    @app.route("/api/tags", methods=["GET"])
    def list_tags():
        """List all available tags."""
        if not app.prompt_source:
            return jsonify({"error": "No prompt source configured"}), 500

        try:
            tags = set()
            all_prompts = app.prompt_source.list()
            logger.info(f"[list_tags] Processing {len(all_prompts)} prompts to gather tags")

            for name in all_prompts:
                try:
                    metadata = _get_prompt_metadata(app.prompt_source, name)
                    tags.update(metadata.get("tags", []))
                except Exception as metadata_error:
                    logger.error(f"[list_tags] DATABASE ERROR getting metadata for '{name}': {type(metadata_error).__name__}: {metadata_error}")
                    # Continue with other prompts rather than failing completely
                    continue

            logger.info(f"[list_tags] Successfully gathered {len(tags)} unique tags")
            return jsonify({"tags": sorted(list(tags))})
        except Exception as e:
            logger.error(f"[list_tags] Error listing tags: {type(e).__name__}: {e}", exc_info=True)
            return jsonify({"error": str(e)}), 500

    @app.route("/api/variable-sets", methods=["GET"])
    def list_variable_sets():
        """List all available variable sets."""
        cursor = None
        try:
            # Check if source is database-backed and has connection
            if not hasattr(app.prompt_source, 'connection'):
                # For file-based sources, return empty list
                return jsonify({"variable_sets": []})

            connection = app.prompt_source.connection

            # Try to query variable sets - if tables don't exist, return empty list
            try:
                cursor = connection.cursor()

                # Query all variable sets ordered by updated_at descending
                table_prefix = getattr(app.prompt_source, 'table_prefix', '')
                table_name = f"{table_prefix}variable_sets" if table_prefix else "variable_sets"
                var_table_name = f"{table_prefix}variable_set_variables" if table_prefix else "variable_set_variables"

                cursor.execute(f"SELECT id, name, updated_at FROM {table_name} ORDER BY updated_at DESC")
                rows = cursor.fetchall()

                variable_sets = []
                for row in rows:
                    set_id = row[0]
                    set_name = row[1]

                    # Fetch variables for this set
                    cursor.execute(
                        f"SELECT key, value FROM {var_table_name} WHERE variable_set_id = %s ORDER BY key",
                        (set_id,)
                    )
                    variables = {}
                    for var_row in cursor.fetchall():
                        variables[var_row[0]] = var_row[1]

                    variable_sets.append({
                        "id": set_id,
                        "name": set_name,
                        "variables": variables
                    })

                return jsonify({"variable_sets": variable_sets})
            except Exception as query_error:
                # If tables don't exist or query fails, reset transaction and return empty
                try:
                    connection.rollback()
                except:
                    pass
                logger.debug(f"Variable sets not available: {query_error}")
                return jsonify({"variable_sets": []})
        except Exception as e:
            logger.error(f"Error listing variable sets: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    logger.debug(f"Error closing cursor: {e}")

    @app.route("/api/variable-sets", methods=["POST"])
    def create_variable_set():
        """Create or update a variable set."""
        cursor = None
        try:
            if not hasattr(app.prompt_source, 'connection'):
                return jsonify({"error": "Database not available"}), 500

            connection = app.prompt_source.connection
            data = request.json
            set_id = data.get('id')
            set_name = data.get('name')
            variables = data.get('variables', {})

            if not set_id or not set_name:
                return jsonify({"error": "Missing id or name"}), 400

            cursor = connection.cursor()
            table_prefix = getattr(app.prompt_source, 'table_prefix', '')
            vs_table = f"{table_prefix}variable_sets" if table_prefix else "variable_sets"
            vsv_table = f"{table_prefix}variable_set_variables" if table_prefix else "variable_set_variables"

            try:
                # Check if set exists
                cursor.execute(f"SELECT id FROM {vs_table} WHERE id = %s", (set_id,))
                exists = cursor.fetchone() is not None

                if exists:
                    # Update existing set name
                    cursor.execute(
                        f"UPDATE {vs_table} SET name = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                        (set_name, set_id)
                    )
                else:
                    # Insert new set
                    cursor.execute(
                        f"INSERT INTO {vs_table} (id, name) VALUES (%s, %s)",
                        (set_id, set_name)
                    )

                # Clear existing variables and insert new ones
                cursor.execute(f"DELETE FROM {vsv_table} WHERE variable_set_id = %s", (set_id,))

                for key, value in variables.items():
                    var_id = f"{set_id}-{key}"
                    cursor.execute(
                        f"INSERT INTO {vsv_table} (id, variable_set_id, key, value) VALUES (%s, %s, %s, %s)",
                        (var_id, set_id, key, value)
                    )

                connection.commit()
                return jsonify({"id": set_id, "name": set_name, "variables": variables}), 201

            except Exception as query_error:
                try:
                    connection.rollback()
                except:
                    pass
                logger.debug(f"Could not create variable set: {query_error}")
                return jsonify({"error": str(query_error)}), 500
        except Exception as e:
            logger.error(f"Error creating variable set: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    logger.debug(f"Error closing cursor: {e}")

    @app.route("/api/variable-sets/<set_id>", methods=["DELETE"])
    def delete_variable_set(set_id):
        """Delete a variable set."""
        cursor = None
        try:
            if not hasattr(app.prompt_source, 'connection'):
                return jsonify({"error": "Database not available"}), 500

            connection = app.prompt_source.connection
            cursor = connection.cursor()
            table_prefix = getattr(app.prompt_source, 'table_prefix', '')
            vs_table = f"{table_prefix}variable_sets" if table_prefix else "variable_sets"
            vsv_table = f"{table_prefix}variable_set_variables" if table_prefix else "variable_set_variables"

            try:
                # Delete variables first (cascade)
                cursor.execute(f"DELETE FROM {vsv_table} WHERE variable_set_id = %s", (set_id,))
                # Delete the set
                cursor.execute(f"DELETE FROM {vs_table} WHERE id = %s", (set_id,))
                connection.commit()
                return jsonify({"success": True}), 200
            except Exception as query_error:
                try:
                    connection.rollback()
                except:
                    pass
                logger.debug(f"Could not delete variable set: {query_error}")
                return jsonify({"error": str(query_error)}), 500
        except Exception as e:
            logger.error(f"Error deleting variable set: {e}")
            return jsonify({"error": str(e)}), 500
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception as e:
                    logger.debug(f"Error closing cursor: {e}")

    @app.route("/api/export", methods=["POST"])
    def export_prompts():
        """Export prompts as JSON."""
        if not app.prompt_source:
            return jsonify({"error": "No prompt source configured"}), 500

        try:
            data = request.json
            filter_tags = data.get("tags", [])
            filter_names = data.get("names", [])

            results = []
            for name in app.prompt_source.list():
                # Filter by name
                if filter_names:
                    if not any(fn in name for fn in filter_names):
                        continue

                # Filter by tags
                if filter_tags:
                    tagged = app.prompt_source.find_by_tag(*filter_tags)
                    if name not in tagged:
                        continue

                prompt_data = _get_prompt_metadata(app.prompt_source, name)
                content = app.prompt_source.get_raw(name)

                results.append(
                    {
                        "name": name,
                        "content": content,
                        "metadata": prompt_data,
                    }
                )

            return jsonify(
                {
                    "export": results,
                    "count": len(results),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Error exporting prompts: {e}")
            return jsonify({"error": str(e)}), 500

    return app


def _get_prompt_metadata(source, name: str) -> Dict[str, Any]:
    """Extract metadata from a prompt using the registry."""
    try:
        if hasattr(source, "_registry"):
            entry = source._registry.get(name)
            if entry:
                return {
                    "name": name,
                    "description": entry.description,
                    "tags": entry.tags,
                    "owner": entry.owner,
                    "source_ref": entry.source_ref,
                }
    except Exception:
        pass

    return {"name": name, "description": "", "tags": [], "owner": None}


def _get_index_html() -> str:
    """Get the React app HTML."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Prompt Manager</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #f5f5f5;
                color: #333;
            }
            #app { height: 100vh; }
        </style>
    </head>
    <body>
        <div id="app"></div>
        <script src="/static/app.js" defer></script>
    </body>
    </html>
    """


def run_server(
    source=None, host: str = "127.0.0.1", port: int = None, debug: bool = False
):
    """
    Run the UI server.

    Args:
        source: PromptSource instance (if None, auto-creates from env vars)
        host: Server host
        port: Server port (defaults to env var PORT or 8000)
        debug: Enable debug mode

    Environment Variables:
        PROMPT_ASSEMBLE_UI: Must be 'true' to enable UI
        PORT: Server port (default: 8000)
        DB_HOSTNAME: PostgreSQL hostname (for auto-created DatabaseSource)
        DB_PASSWORD: PostgreSQL password (required if DB_HOSTNAME set)
    """
    if not os.getenv("PROMPT_ASSEMBLE_UI", "").lower() == "true":
        logger.warning(
            "Set PROMPT_ASSEMBLE_UI=true environment variable to enable UI"
        )
        return

    # If no source provided, try to auto-create from environment
    if source is None and os.getenv("DB_HOSTNAME"):
        try:
            from ..sources import create_database_source_from_env
            db_hostname = os.getenv("DB_HOSTNAME")
            db_port = os.getenv("DB_PORT", "5432")
            db_name = os.getenv("DB_DATABASE", "prompts")
            logger.info(f"Auto-creating DatabaseSource from environment: {db_hostname}:{db_port}/{db_name}")
            source = create_database_source_from_env()
            logger.info("DatabaseSource created successfully")
        except Exception as e:
            logger.error(f"DATABASE ERROR: Could not auto-create DatabaseSource: {type(e).__name__}: {e}")
            logger.warning("Proceeding without database - this may cause API errors")

    # Determine port: command line arg > env var > default
    if port is None:
        port = int(os.getenv("PORT", "8000"))

    app = create_app(source=source)
    if app:
        logger.info(f"Starting Prompt Manager UI at http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
