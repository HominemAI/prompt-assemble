# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
