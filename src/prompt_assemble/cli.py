"""
Command-line interface for prompt-assemble.

Usage: pambl [options]
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from .core import assemble


def load_json_file(path: str) -> Dict[str, Any]:
    """Load a JSON file."""
    try:
        with open(path, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {path}: {e}", file=sys.stderr)
        sys.exit(1)


def load_template_file(path: str) -> str:
    """Load a template file (.prompt or any text file)."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog='pambl',
        description='Prompt assembly tool - assemble dynamic prompts with sigil substitution',
    )

    parser.add_argument(
        '--template', '-t',
        required=True,
        help='Path to template file (.prompt or text file)',
    )

    parser.add_argument(
        '--components', '-c',
        help='Path to JSON file with prompt components',
    )

    parser.add_argument(
        '--variables', '-v',
        help='Path to JSON file with variables',
    )

    parser.add_argument(
        '--output', '-o',
        help='Output file (default: stdout)',
    )

    parser.add_argument(
        '--format', '-f',
        choices=['text', 'json', 'template'],
        default='text',
        help='Output format (default: text)',
    )

    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0',
    )

    args = parser.parse_args()

    # Load template
    template = load_template_file(args.template)

    # Load components and variables
    components = {}
    if args.components:
        components = load_json_file(args.components)

    variables = {}
    if args.variables:
        variables = load_json_file(args.variables)

    # Assemble
    try:
        result = assemble(
            template,
            variables=variables,
            components=components,
            output_format=args.format,
        )
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except RecursionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    output_text = result if isinstance(result, str) else json.dumps(result, indent=2)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_text)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(output_text)


if __name__ == '__main__':
    main()
