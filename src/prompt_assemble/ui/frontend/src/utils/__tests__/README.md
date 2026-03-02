# Frontend Unit Tests

Comprehensive unit test suite for all main JavaScript/TypeScript functions.

## Test Files

### `api.test.ts` - Backend Abstraction Layer
Tests for the `PromptBackend` interface and its three implementations:

- **createBackend()** — Factory function that creates the correct backend based on config
- **RemoteBackend** — HTTP client with fetch-based API calls
- **LocalBackend** — IndexedDB browser storage
- **FileSystemBackend** — File System Access API

**Coverage:**
- Backend factory and type checking
- HTTP error handling and URL encoding
- Mock fetch calls for all CRUD operations
- Auth header injection (getHeaders hook)
- All 14 PromptBackend interface methods

### `renderer.test.ts` - Prompt Rendering & Substitution
Tests for the `substitute()` function that processes prompt templates with sigils.

**Coverage:**
- `[[VAR_NAME]]` — Variable substitution
- `[[PROMPT: name]]` — Prompt injection
- `[[PROMPT_TAG: tag1, tag2]]` — Tag-based prompt injection
- `[[PROMPT_TAG:N: tag]]` — Limit results to N
- Comment stripping (HTML `<!-- -->` and shell `#!`)
- Complex nesting scenarios (variables in prompts, prompts in tags)
- Error handling (missing prompts, failed lookups)

### `migration.test.ts` - Backend Data Migration
Tests for migration utilities between backends.

**Coverage:**
- `migrateBackends()` — Transfer all data from source to target backend
  - Prompt migration
  - Variable set migration
  - Prompt-variable set mapping migration
  - Progress callbacks
  - Error recovery (continues on individual failures)
- `clearBackendData()` — Delete all data from a backend
  - Delete all prompts
  - Delete all variable sets
  - Progress callbacks
  - Error recovery

### `xmlToJson.test.ts` - XML to JSON Conversion
Tests for the `xmlToJson()` utility that converts XML structures to JSON.

**Coverage:**
- Simple and nested element conversion
- Attribute handling
- Text content preservation
- Array detection (multiple siblings)
- Empty and self-closing elements
- Special characters and CDATA sections
- Deep nesting
- Mixed content (text + elements)
- Error handling for malformed XML
- Prompt-like XML structures

## Running Tests

```bash
# Run all tests
npm run test

# Run tests in watch mode
npm run test -- --watch

# Run specific test file
npm run test -- api.test.ts

# Generate coverage report
npm run test:coverage

# Open interactive test UI
npm run test:ui
```

## Test Framework

- **Vitest** — Modern test runner for Vite projects
- **happy-dom** — Lightweight DOM implementation for Node.js
- **vi.fn()** — Mock functions for isolating dependencies

## Test Structure

Each test file follows this pattern:

```typescript
import { describe, it, expect, beforeEach, vi } from 'vitest'

describe('Feature', () => {
  beforeEach(() => {
    // Setup before each test
  })

  it('should do something', () => {
    // Arrange
    // Act
    // Assert
  })
})
```

## Mocking Strategy

### RemoteBackend Tests
- Mock `global.fetch` to simulate HTTP requests
- Verify correct URLs, methods, headers
- Test error responses

### LocalBackend & FileSystemBackend Tests
- Basic instantiation tests
- Interface completeness checks
- Full integration tests would require real browser APIs

### Migration Tests
- Mock backend instances with all methods
- Test data transfer scenarios
- Verify progress callbacks
- Test error recovery

## Coverage Goals

| Module | Methods | Tests | Goal |
|--------|---------|-------|------|
| api.ts | 14+ | ~30 | Backend interface completeness |
| renderer.ts | 1 | ~40 | All sigil types and combinations |
| migration.ts | 2 | ~20 | Data transfer and cleanup |
| xmlToJson.ts | 1 | ~30 | XML parsing accuracy |
| **Total** | **18+** | **~120** | **High coverage** |

## Known Limitations

1. **IndexedDB Testing** — Full IndexedDB tests require browser environment or heavy mocking
   - Current tests verify interface completeness
   - Integration tests would need e2e setup

2. **File System Access API** — Requires browser with FSAA support
   - Current tests verify interface completeness
   - Real directory operations tested manually

3. **React Components** — Component tests would use React Testing Library
   - Not included in this suite
   - Would be in separate `__tests__/components/` directory

## Future Enhancements

- [ ] Add integration tests with real IndexedDB
- [ ] Add e2e tests with actual File System API
- [ ] Add component tests for SettingsModal, RenderModal
- [ ] Add performance benchmarks
- [ ] Add coverage thresholds (e.g., 80% minimum)

## CI/CD Integration

Tests can be integrated into GitHub Actions:

```yaml
- name: Run tests
  run: npm run test

- name: Generate coverage
  run: npm run test:coverage

- name: Upload coverage
  uses: codecov/codecov-action@v3
```
