# Contributing to prompt-assemble

Thank you for your interest in contributing! Here's how to get started.

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/prompt-assemble.git
   cd prompt-assemble
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install in development mode with dev dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

```bash
pytest tests/ -v
```

## Code Quality

Format code with black:
```bash
black src/prompt_assemble tests
```

Sort imports with isort:
```bash
isort src/prompt_assemble tests
```

Lint with flake8:
```bash
flake8 src/prompt_assemble tests
```

Type check with mypy:
```bash
mypy src/prompt_assemble
```

## Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature
   ```

2. Make your changes and add tests

3. Ensure all tests pass:
   ```bash
   pytest tests/ -v
   ```

4. Commit with clear messages:
   ```bash
   git commit -m "Brief description of changes"
   ```

5. Push and create a pull request

## Reporting Issues

Please use GitHub Issues to report bugs or suggest features. Include:
- Clear description of the issue
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Python version and environment details

## Style Guide

- Follow PEP 8
- Use type hints where possible
- Write docstrings for public functions/classes
- Keep functions focused and small
- Add tests for new features

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
