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

    # ====== API Routes ======

    @app.route("/api/prompts", methods=["GET"])
    def list_prompts():
        """List all available prompts with metadata."""
        if not app.prompt_source:
            return jsonify({"error": "No prompt source configured"}), 500

        try:
            prompts = []
            for name in app.prompt_source.list():
                # Filter out "Untitled" or "untitled" prompts
                if name.lower() == "untitled":
                    logger.debug(f"Skipping 'untitled' prompt in list")
                    continue

                prompt_data = _get_prompt_metadata(app.prompt_source, name)
                # Add updated_at timestamp if available
                if hasattr(app.prompt_source, 'connection'):
                    cursor = app.prompt_source.connection.cursor()
                    try:
                        cursor.execute(
                            f"SELECT updated_at FROM {app.prompt_source._table('prompts')} WHERE name = %s",
                            (name,)
                        )
                        row = cursor.fetchone()
                        if row and row[0]:
                            prompt_data['updated_at'] = row[0].isoformat()
                    finally:
                        cursor.close()
                prompts.append(prompt_data)

            return jsonify({"prompts": prompts})
        except Exception as e:
            logger.error(f"Error listing prompts: {e}")
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

    @app.route("/api/tags", methods=["GET"])
    def list_tags():
        """List all available tags."""
        if not app.prompt_source:
            return jsonify({"error": "No prompt source configured"}), 500

        try:
            tags = set()
            for name in app.prompt_source.list():
                metadata = _get_prompt_metadata(app.prompt_source, name)
                tags.update(metadata.get("tags", []))

            return jsonify({"tags": sorted(list(tags))})
        except Exception as e:
            logger.error(f"Error listing tags: {e}")
            return jsonify({"error": str(e)}), 500

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
        source: PromptSource instance
        host: Server host
        port: Server port (defaults to env var PORT or 8000)
        debug: Enable debug mode
    """
    if not os.getenv("PROMPT_ASSEMBLE_UI", "").lower() == "true":
        logger.warning(
            "Set PROMPT_ASSEMBLE_UI=true environment variable to enable UI"
        )
        return

    # Determine port: command line arg > env var > default
    if port is None:
        port = int(os.getenv("PORT", "8000"))

    app = create_app(source=source)
    if app:
        logger.info(f"Starting Prompt Manager UI at http://{host}:{port}")
        app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
