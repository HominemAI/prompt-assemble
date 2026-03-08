#!/usr/bin/env python3
"""
Comprehensive examples demonstrating all features of prompt-assemble.

This script shows how to use:
- Variable Sets API (create, update, list, delete)
- Owner-based prompt lookup
- Partial name matching
- Enhanced render method with search and filtering
- Scoped variable sets
- Empty render fallback content
"""

from prompt_assemble import PromptProvider
from prompt_assemble.sources import FileSystemSource, DatabaseSource
import psycopg2


# ============================================================================
# SETUP: Initialize with FileSystemSource or DatabaseSource
# ============================================================================

def setup_filesystem_source():
    """Initialize with filesystem-based prompts."""
    source = FileSystemSource("./prompts")
    provider = PromptProvider(source)
    return provider


def setup_database_source():
    """Initialize with PostgreSQL database."""
    conn = psycopg2.connect(
        host="localhost",
        database="prompts",
        user="postgres",
        password="secret"
    )
    source = DatabaseSource(conn, table_prefix="demo_")
    provider = PromptProvider(source)
    return provider


# ============================================================================
# FEATURE 1: Variable Sets API
# ============================================================================

def example_variable_sets(provider):
    """Demonstrate variable set management."""
    print("\n=== VARIABLE SETS API ===\n")

    # Create a global variable set
    print("1. Create global variable set (visible to all)")
    global_set_id = provider.create_variable_set(
        name="api_keys",
        variables={
            "PROD_API_KEY": "sk-prod-12345",
            "DEV_API_KEY": "sk-dev-67890",
            "TIMEOUT": "30"
        }
    )
    print(f"   Created: {global_set_id}")

    # Create owner-scoped variable sets
    print("\n2. Create owner-scoped variable sets")
    john_set_id = provider.create_variable_set(
        name="john_config",
        variables={
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "info"
        },
        owner="john"
    )
    print(f"   John's set: {john_set_id}")

    alice_set_id = provider.create_variable_set(
        name="alice_config",
        variables={
            "ENVIRONMENT": "staging",
            "LOG_LEVEL": "debug"
        },
        owner="alice"
    )
    print(f"   Alice's set: {alice_set_id}")

    # List all variable sets
    print("\n3. List all variable sets")
    all_sets = provider.list_variable_sets()
    for vs in all_sets:
        owner_info = f" (owner: {vs['owner']})" if vs.get('owner') else " (global)"
        print(f"   - {vs['name']}{owner_info}: {list(vs['variables'].keys())}")

    # List global variable sets only
    print("\n4. List global (unscoped) variable sets")
    global_sets = provider.list_global_variable_sets()
    for vs in global_sets:
        print(f"   - {vs['name']}: {list(vs['variables'].keys())}")

    # List variable sets by owner
    print("\n5. List variable sets for specific owner")
    john_sets = provider.list_variable_sets_by_owner("john")
    print(f"   John's variable sets:")
    for vs in john_sets:
        print(f"     - {vs['name']}: {list(vs['variables'].keys())}")

    # Get available variable sets for an owner (global + owner-scoped)
    print("\n6. Get available variable sets for owner")
    available = provider.get_available_variable_sets(owner="john")
    print(f"   Available for John: {[vs['name'] for vs in available]}")

    # Update a variable set
    print("\n7. Update variable set")
    provider.update_variable_set(
        john_set_id,
        variables={
            "ENVIRONMENT": "production",
            "LOG_LEVEL": "warning",
            "NEW_VAR": "new_value"
        }
    )
    print(f"   Updated John's config")

    # Get specific variable set
    print("\n8. Get specific variable set")
    vs = provider.get_variable_set(john_set_id)
    print(f"   John's config variables: {vs['variables']}")

    # Delete a variable set
    print("\n9. Delete variable set")
    provider.delete_variable_set(alice_set_id)
    print(f"   Deleted Alice's config")

    return global_set_id, john_set_id


# ============================================================================
# FEATURE 2: Owner-Based Prompt Lookup
# ============================================================================

def example_owner_lookup(provider):
    """Demonstrate finding prompts by owner."""
    print("\n=== OWNER-BASED LOOKUP ===\n")

    # Find prompts by owner
    print("1. Find all prompts by owner")
    john_prompts = provider.find_by_owner("john")
    print(f"   Prompts owned by John: {john_prompts}")

    alice_prompts = provider.find_by_owner("alice")
    print(f"   Prompts owned by Alice: {alice_prompts}")

    # Render prompt by exact match with owner filter
    print("\n2. Render prompt with owner filter")
    if john_prompts:
        result = provider.render(
            john_prompts[0],
            owner="john",
            variables={},
        )
        print(f"   Rendered: {result[:100]}...")


# ============================================================================
# FEATURE 3: Partial Name Matching
# ============================================================================

def example_partial_name_matching(provider):
    """Demonstrate finding prompts by partial name."""
    print("\n=== PARTIAL NAME MATCHING ===\n")

    # Find prompts by partial name
    print("1. Find prompts by partial name (case-insensitive)")
    system_prompts = provider.find_by_name("system")
    print(f"   Prompts matching 'system': {system_prompts}")

    config_prompts = provider.find_by_name("config")
    print(f"   Prompts matching 'config': {config_prompts}")

    # Find with wildcard-like pattern
    print("\n2. Find with specific pattern")
    api_prompts = provider.find_by_name("api")
    print(f"   Prompts matching 'api': {api_prompts}")


# ============================================================================
# FEATURE 4: Enhanced Render with Search and Filtering
# ============================================================================

def example_enhanced_render(provider):
    """Demonstrate enhanced render method with search."""
    print("\n=== ENHANCED RENDER METHOD ===\n")

    # Exact match (original behavior)
    print("1. Exact match render")
    try:
        result = provider.render(
            "my_prompt",
            variables={"name": "World"}
        )
        print(f"   Result: {result[:100]}...")
    except Exception as e:
        print(f"   Note: {e}")

    # Partial name match
    print("\n2. Partial name match render")
    try:
        result = provider.render(
            "system",
            match_type="partial",
            variables={"role": "assistant"}
        )
        print(f"   Result: {result[:100]}...")
    except Exception as e:
        print(f"   Note: {e}")

    # Render by owner
    print("\n3. Render by owner")
    try:
        result = provider.render(
            "prompt",
            owner="john",
            variables={}
        )
        print(f"   Result: {result[:100]}...")
    except Exception as e:
        print(f"   Note: {e}")

    # Render by tags
    print("\n4. Render by tags")
    try:
        result = provider.render(
            "prompt",
            tags=["prod", "critical"],
            variables={}
        )
        print(f"   Result: {result[:100]}...")
    except Exception as e:
        print(f"   Note: {e}")

    # Combined search: partial match + owner + tags
    print("\n5. Combined search (partial + owner + tags)")
    try:
        result = provider.render(
            "system",
            match_type="partial",
            owner="john",
            tags=["prod"],
            variables={"model": "gpt-4"}
        )
        print(f"   Result: {result[:100]}...")
    except Exception as e:
        print(f"   Note: {e}")


# ============================================================================
# FEATURE 5: Empty Render Fallback
# ============================================================================

def example_empty_render(provider):
    """Demonstrate empty_render fallback parameter."""
    print("\n=== EMPTY RENDER FALLBACK ===\n")

    # Default behavior (returns empty string)
    print("1. Default behavior - empty renders as empty string")
    try:
        result = provider.render(
            "nonexistent",
            match_type="partial",
            variables={},
            empty_render=""
        )
        print(f"   Result is empty: {result == ''}")
    except Exception as e:
        print(f"   Note: {e}")

    # With custom fallback
    print("\n2. With custom fallback message")
    try:
        result = provider.render(
            "nonexistent",
            match_type="partial",
            variables={},
            empty_render="[No prompt content available]"
        )
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   Note: {e}")

    # Multi-line fallback
    print("\n3. Multi-line fallback")
    try:
        result = provider.render(
            "missing",
            match_type="partial",
            variables={},
            empty_render="""---
No instructions provided.
Please add content to this prompt.
---"""
        )
        print(f"   Result:\n{result}")
    except Exception as e:
        print(f"   Note: {e}")


# ============================================================================
# FEATURE 6: Scoped Variable Sets with Render
# ============================================================================

def example_scoped_variable_sets(provider):
    """Demonstrate scoped variable sets in action."""
    print("\n=== SCOPED VARIABLE SETS ===\n")

    # Create global and scoped sets
    print("1. Setup global and owner-scoped variable sets")
    global_set = provider.create_variable_set(
        "shared_vars",
        {
            "COMPANY": "Acme Corp",
            "VERSION": "1.0.0"
        }
    )
    print(f"   Global set: {global_set}")

    dev_set = provider.create_variable_set(
        "dev_vars",
        {
            "ENV": "development",
            "DEBUG": "true"
        },
        owner="developer"
    )
    print(f"   Developer set: {dev_set}")

    # Get available sets for developer
    print("\n2. Get available sets for 'developer' owner")
    available = provider.get_available_variable_sets(owner="developer")
    print(f"   Available sets: {[s['name'] for s in available]}")
    print(f"   Includes: global + owner-scoped")

    # Link variable sets to a prompt
    print("\n3. Link variable sets to a prompt")
    try:
        provider.set_active_variable_sets(
            "my_prompt",
            [global_set, dev_set]
        )
        print(f"   Linked variable sets to 'my_prompt'")

        # Get active variable sets for a prompt
        active = provider.get_active_variable_sets("my_prompt")
        print(f"   Active variable sets: {[s['id'] for s in active]}")
    except Exception as e:
        print(f"   Note: {e}")

    # Set variable overrides for specific prompt
    print("\n4. Set variable overrides for a prompt")
    try:
        provider.set_variable_overrides(
            "my_prompt",
            dev_set,
            {
                "DEBUG": "false",  # Override global setting
                "LOG_LEVEL": "error"
            }
        )
        print(f"   Set overrides for 'my_prompt'")

        # Get variable overrides
        overrides = provider.get_variable_overrides("my_prompt", dev_set)
        print(f"   Overrides: {overrides}")
    except Exception as e:
        print(f"   Note: {e}")


# ============================================================================
# ADVANCED EXAMPLE: Complete Workflow
# ============================================================================

def example_complete_workflow(provider):
    """Demonstrate a complete real-world workflow."""
    print("\n=== COMPLETE WORKFLOW ===\n")

    print("Scenario: Multi-team prompt management with scoped variables")
    print("-" * 60)

    # Setup teams and their prompts
    print("\n1. Setup team-specific variable sets")

    # Global variables shared by all teams
    shared_vars = provider.create_variable_set(
        "company_standards",
        {
            "COMPANY": "TechCorp",
            "MODEL": "gpt-4",
            "MAX_TOKENS": "2000"
        }
    )
    print(f"   Created global: company_standards")

    # Backend team variables
    backend_vars = provider.create_variable_set(
        "backend_config",
        {
            "ENVIRONMENT": "production",
            "DB_POOL_SIZE": "20",
            "CACHE_TTL": "3600"
        },
        owner="backend_team"
    )
    print(f"   Created backend team: backend_config")

    # Frontend team variables
    frontend_vars = provider.create_variable_set(
        "frontend_config",
        {
            "ENVIRONMENT": "production",
            "API_TIMEOUT": "30000",
            "RETRY_ATTEMPTS": "3"
        },
        owner="frontend_team"
    )
    print(f"   Created frontend team: frontend_config")

    # Render prompt for backend team
    print("\n2. Render team-specific prompts")
    print("   Backend team available variables:")
    backend_available = provider.get_available_variable_sets(owner="backend_team")
    for vs in backend_available:
        print(f"     - {vs['name']}: {list(vs['variables'].keys())}")

    print("   Frontend team available variables:")
    frontend_available = provider.get_available_variable_sets(owner="frontend_team")
    for vs in frontend_available:
        print(f"     - {vs['name']}: {list(vs['variables'].keys())}")

    # Render with different owners
    print("\n3. Render same prompt with different team contexts")
    try:
        backend_render = provider.render(
            "system",
            match_type="partial",
            owner="backend_team",
            variables={},
            empty_render="[Backend system prompt]"
        )
        print(f"   Backend: {backend_render[:50]}...")
    except Exception as e:
        print(f"   Note: {e}")

    try:
        frontend_render = provider.render(
            "system",
            match_type="partial",
            owner="frontend_team",
            variables={},
            empty_render="[Frontend system prompt]"
        )
        print(f"   Frontend: {frontend_render[:50]}...")
    except Exception as e:
        print(f"   Note: {e}")


# ============================================================================
# MAIN: Run all examples
# ============================================================================

def main():
    """Run all example demonstrations."""
    print("=" * 70)
    print("PROMPT-ASSEMBLE COMPREHENSIVE EXAMPLES")
    print("=" * 70)

    try:
        # Use filesystem source (no database required)
        provider = setup_filesystem_source()
        print("\nInitialized with FileSystemSource")

    except Exception as e:
        print(f"\nNote: Could not initialize FileSystemSource: {e}")
        print("To run database examples, ensure PostgreSQL is running and configured.")
        return

    # Run all examples
    example_variable_sets(provider)
    example_owner_lookup(provider)
    example_partial_name_matching(provider)
    example_enhanced_render(provider)
    example_empty_render(provider)
    example_scoped_variable_sets(provider)
    example_complete_workflow(provider)

    print("\n" + "=" * 70)
    print("EXAMPLES COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()
