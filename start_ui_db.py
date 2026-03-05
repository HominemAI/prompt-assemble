#!/usr/bin/env python
"""Start the Prompt Manager UI with PostgreSQL DatabaseSource."""

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    os.environ["PROMPT_ASSEMBLE_UI"] = "true"

    try:
        import psycopg2
        from prompt_assemble.sources import DatabaseSource
        from prompt_assemble.api.server import run_server

        logger.info("Starting Prompt Manager UI Server")

        # Get connection parameters
        db_host = os.getenv("DB_HOSTNAME", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_DATABASE", "prompts")
        db_user = os.getenv("DB_USERNAME", "postgres")
        db_sslmode = os.getenv("DB_SSLMODE", "require")

        logger.info(f"Connecting to PostgreSQL: {db_user}@{db_host}:{db_port}/{db_name}")


        # Create PostgreSQL connection from environment variables
        def create_connection():
            """Factory function to create new database connections."""
            return psycopg2.connect(
                host=db_host,
                port=int(db_port),
                database=db_name,
                user=db_user,
                password=os.getenv("DB_PASSWORD", ""),
                sslmode=db_sslmode,
            )


        conn = create_connection()
        logger.info("✓ Connected to PostgreSQL")

        # Use table prefix (default: pambl_)
        table_prefix = os.getenv("DB_PREFIX", "pambl_")
        if table_prefix and not table_prefix.endswith("_"):
            table_prefix += "_"
        logger.info(f"Using table prefix: '{table_prefix}'")
        logger.info("Tables will be named: pambl_prompts, pambl_prompt_tags, etc.")

        # DatabaseSource automatically initializes schema on first run
        logger.info("Initializing database tables...")
        source = DatabaseSource(conn, table_prefix=table_prefix)

        # Store connection factory in source for reconnection on failure
        source._connection_factory = create_connection

        prompt_count = len(source.list())
        logger.info(f"✓ Database initialized with {prompt_count} prompts")

        # Start server
        port = int(os.getenv("PORT", "8000"))
        logger.info(f"✓ Starting UI server on http://localhost:{port}")
        logger.info("Press CTRL+C to stop")
        run_server(source=source, port=port)

    except psycopg2.OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        logger.error("Check your database credentials and connection settings:")
        logger.error("  DB_HOSTNAME, DB_PORT, DB_DATABASE, DB_USERNAME, DB_PASSWORD, DB_SSLMODE")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
