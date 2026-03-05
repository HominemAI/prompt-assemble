"""
Example: Running the Prompt Manager UI

This demonstrates how to set up and run the full UI with the prompt-assemble library.
"""

import os
from pathlib import Path

# Set environment variable to enable UI
os.environ["PROMPT_ASSEMBLE_UI"] = "true"

from prompt_assemble.sources import FileSystemSource, DatabaseSource
from prompt_assemble.api import run_server
import sqlite3


def example_with_filesystem():
    """Run UI with filesystem-based prompts."""
    print("=" * 60)
    print("Prompt Manager UI - Filesystem Source Example")
    print("=" * 60)

    # Create a source pointing to prompts directory
    prompt_dir = Path("./examples")
    if not prompt_dir.exists():
        print(f"Creating example directory: {prompt_dir}")
        prompt_dir.mkdir(parents=True)

        # Create some example prompts
        (prompt_dir / "greeting.prompt").write_text(
            "You are a friendly greeting bot.\nGreet the user warmly."
        )

        personas_dir = prompt_dir / "personas"
        personas_dir.mkdir()
        (personas_dir / "expert.prompt").write_text(
            "You are an expert in [[DOMAIN]].\nProvide expert-level guidance."
        )

    # Initialize the source
    source = FileSystemSource(prompt_dir)

    print(f"✓ Loaded {len(source.list())} prompts from {prompt_dir}")
    print(f"  Prompts: {source.list()}")

    # Add listeners to track events
    def on_source_change(event_type: str):
        print(f"  [EVENT] {event_type}")

    source.add_listener(on_source_change)

    # Start the server
    print("\n🚀 Starting Prompt Manager UI...")
    print("   Open browser to: http://127.0.0.1:5000")
    print("   Press Ctrl+C to stop\n")

    run_server(source=source, host="127.0.0.1", port=5000, debug=True)


def example_with_database():
    """Run UI with database-based prompts."""
    print("=" * 60)
    print("Prompt Manager UI - Database Source Example")
    print("=" * 60)

    # Create an in-memory or file-based database
    conn = sqlite3.connect("prompts.db")

    # Initialize the source
    source = DatabaseSource(conn)

    # Add some example prompts
    if not source.list():
        print("✓ Creating example prompts...")

        source.save_prompt(
            name="greeting",
            content="You are a friendly greeting bot.\nGreet the user warmly.",
            description="Friendly greeting prompt",
            tags=["greeting", "basic"],
            owner="team-chatbot",
        )

        source.save_prompt(
            name="expert",
            content="You are an expert in [[DOMAIN]].\nProvide expert-level guidance.",
            description="Expert persona for domain-specific tasks",
            tags=["persona", "professional"],
            owner="team-platform",
        )

        source.save_prompt(
            name="system_instructions",
            content="<!-- Important: Always be helpful and honest -->\nAlways prioritize user safety.",
            description="Global system instructions",
            tags=["system"],
        )

    print(f"✓ Loaded {len(source.list())} prompts from database")
    print(f"  Prompts: {source.list()}")

    # Add listeners to track events
    def on_db_change(event_type: str):
        if event_type == "refreshed":
            print("  [EVENT] Database metadata refreshed")
        elif event_type == "prompt_saved":
            print("  [EVENT] Prompt saved to database")

    source.add_listener(on_db_change)

    # Start the server
    print("\n🚀 Starting Prompt Manager UI...")
    print("   Open browser to: http://127.0.0.1:5000")
    print("   Press Ctrl+C to stop\n")

    run_server(source=source, host="127.0.0.1", port=5000, debug=True)


def example_with_listeners():
    """Demonstrate using listeners with the UI."""
    print("=" * 60)
    print("Prompt Manager UI - With Event Listeners")
    print("=" * 60)

    source = FileSystemSource("./examples")

    # Track all registry changes
    change_log = []

    def on_registry_change(event_type: str):
        change_log.append(event_type)
        print(f"  📝 Registry event: {event_type}")

    source.add_listener(on_registry_change)

    print(f"\n✓ Listener attached to source")

    # Start the server
    print("\n🚀 Starting Prompt Manager UI...")
    print("   Changes will be logged above")
    print("   Open browser to: http://127.0.0.1:5000")
    print("   Press Ctrl+C to stop\n")

    run_server(source=source, host="127.0.0.1", port=5000, debug=True)

    print(f"\n📊 Total changes recorded: {len(change_log)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "database":
            example_with_database()
        elif sys.argv[1] == "listeners":
            example_with_listeners()
        else:
            print("Usage: python example_usage.py [filesystem|database|listeners]")
            sys.exit(1)
    else:
        example_with_filesystem()
