# PyPI Publishing Setup Guide

This guide explains how to set up PyPI publishing for the `prompt-assemble` package.

## Prerequisites

1. **PyPI Account**
   - Sign up at https://pypi.org (or use test PyPI at https://test.pypi.org first)
   - Create an account if you don't have one

2. **API Token**
   - Log in to PyPI
   - Navigate to Account Settings → API tokens
   - Click "Create API token"
   - Scope: Entire account (or specific project)
   - Copy the token (starts with `pypi-`)

## GitHub Secrets Setup

Add the PyPI API token to your GitHub repository:

### Steps:
1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Create secret:
   - **Name:** `PYPI_API_TOKEN`
   - **Value:** Your PyPI API token from above

## Publishing a Release

### 1. Update Version in `pyproject.toml`
```toml
[project]
version = "0.2.0"  # Increment version
```

### 2. Commit and Tag
```bash
git add pyproject.toml
git commit -m "Bump version to 0.2.0"
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

### 3. Automatic Publishing
The GitHub Actions workflow automatically:
- Builds the Python package
- Verifies metadata with twine
- Publishes to PyPI
- Creates a GitHub Release with install instructions

## Verifying Publication

1. Check PyPI: https://pypi.org/project/prompt-assemble/
2. Or search: `pip search prompt-assemble` (if enabled on PyPI)
3. Install and test: `pip install prompt-assemble==0.2.0`

## Installation Instructions

Users can now install your package:

```bash
# Basic installation (core library only)
pip install prompt-assemble

# With PostgreSQL database support
pip install prompt-assemble[db]

# With Flask API server
pip install prompt-assemble[ui]

# With all features
pip install prompt-assemble[ui-full]

# Development setup
pip install prompt-assemble[dev]
```

## Package Metadata

The following is published to PyPI:

**Name:** `prompt-assemble`
**Description:** A lightweight prompt assembly library using sigil-based substitution with no template logic
**Repository:** https://github.com/HominemAI/prompt-assemble
**License:** MIT
**Python:** 3.11+

### Keywords
- prompt
- llm
- template
- assembly
- substitution
- sigil
- ai

## Versioning Strategy

Use [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR:** Breaking changes
- **MINOR:** New features (backwards compatible)
- **PATCH:** Bug fixes

Examples:
- `v0.1.0` - Initial release
- `v0.2.0` - New features
- `v0.2.1` - Bug fixes
- `v1.0.0` - First stable release

## Testing Before Release

### Test PyPI (Optional)

To test on PyPI's test server first:

1. Create test token at https://test.pypi.org/account/api-tokens/
2. Add secret `PYPI_API_TOKEN_TEST`
3. Push to a test tag like `vtest-0.2.0`
4. Manually trigger workflow with test token

### Local Testing

```bash
# Build distribution
python -m build

# Check metadata
twine check dist/*

# Verify it's installable
pip install dist/prompt_assemble-0.2.0-py3-none-any.whl
```

## What Gets Published

Files included in package:
- `src/prompt_assemble/` - Python source code
- `README.md` - Project documentation
- `LICENSE` - MIT license

Files excluded:
- Tests (`tests/`)
- GitHub workflows (`.github/`)
- Docker files
- Development config (`.gitignore`, etc.)

## Troubleshooting

### "Invalid API token"
- Verify token in GitHub secrets matches PyPI token
- Make sure token hasn't expired
- Token should start with `pypi-`

### "Version already exists"
- Each version can only be published once
- Use a new version number or delete on PyPI (if allowed)
- See: https://pypi.org/help/#yanking

### "Metadata validation failed"
- Check `pyproject.toml` syntax
- Run `twine check` locally first
- Ensure README.md exists and is valid

### "Package name already taken"
- Package name `prompt-assemble` is reserved
- Use unique name if publishing elsewhere
- Check: https://pypi.org/project/prompt-assemble/

## Advanced: Custom Package Index

To publish to a custom/private PyPI:

```bash
# In workflow, update the publish step:
python -m twine upload \
  --repository-url https://your-pypi-server.com \
  --username __token__ \
  --password ${{ secrets.PYPI_API_TOKEN }} \
  dist/*
```

## References

- [PyPI Upload Documentation](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-and-trusted-publishers/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [pyproject.toml Specification](https://packaging.python.org/specifications/pyproject-toml/)
- [Semantic Versioning](https://semver.org/)

## Quick Checklist

- [ ] PyPI account created
- [ ] API token generated
- [ ] `PYPI_API_TOKEN` secret added to GitHub
- [ ] `pyproject.toml` updated with correct version
- [ ] `src/prompt_assemble/` exists with `__init__.py`
- [ ] `README.md` exists
- [ ] `LICENSE` file exists
- [ ] Tag created: `git tag v0.1.0`
- [ ] Tag pushed: `git push origin v0.1.0`
- [ ] Workflow runs successfully
- [ ] Package appears on PyPI within seconds
