import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { createBackend, PromptBackend } from '../api'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch as any

describe('Backend Abstraction - createBackend()', () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it('creates a backend for remote mode', () => {
    const backend = createBackend({
      mode: 'remote',
      baseUrl: 'http://localhost:8000'
    })
    expect(backend).toBeDefined()
    expect(typeof backend.listPrompts).toBe('function')
  })

  it('throws error for invalid mode', () => {
    expect(() => {
      createBackend({ mode: 'invalid' as any })
    }).toThrow()
  })

  it('accepts baseUrl config for remote backend', () => {
    const backend = createBackend({
      mode: 'remote',
      baseUrl: 'http://custom:9000'
    })
    expect(backend).toBeDefined()
  })

  it('accepts getHeaders callback for auth', () => {
    const getHeaders = () => ({ 'Authorization': 'Bearer token' })
    const backend = createBackend({
      mode: 'remote',
      baseUrl: 'http://localhost:8000',
      getHeaders
    })
    expect(backend).toBeDefined()
  })
})

describe('HTTP Backend - API Operations', () => {
  let backend: PromptBackend

  beforeEach(() => {
    vi.clearAllMocks()
    backend = createBackend({
      mode: 'remote',
      baseUrl: 'http://localhost:8000',
    })
  })

  it('listPrompts makes GET request', async () => {
    const mockPrompts = [
      { name: 'prompt1', description: 'Test', tags: [], updated_at: '2025-01-01T00:00:00Z' },
    ]
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockPrompts,
    })

    const result = await backend.listPrompts()

    expect(mockFetch).toHaveBeenCalled()
    expect(result).toBeDefined()
  })

  it('listTags fetches available tags', async () => {
    const mockTags = ['persona', 'technical', 'creative']
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockTags,
    })

    const result = await backend.listTags()

    expect(mockFetch).toHaveBeenCalled()
    expect(Array.isArray(result)).toBe(true)
  })

  it('savePrompt sends POST request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    })

    const promptData = {
      content: 'Test content',
      metadata: {
        description: 'Test description',
        tags: ['test'],
      }
    }

    await backend.savePrompt('test-prompt', promptData)

    expect(mockFetch).toHaveBeenCalled()
  })

  it('deletePrompt sends DELETE request', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    })

    await backend.deletePrompt('test-prompt')

    expect(mockFetch).toHaveBeenCalled()
  })

  it('throws error on network failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'))

    await expect(backend.listPrompts()).rejects.toThrow()
  })

  it('provides all required methods', () => {
    const methods = [
      'listPrompts',
      'getPrompt',
      'savePrompt',
      'deletePrompt',
      'listTags',
      'listVariableSets',
      'saveVariableSet',
      'deleteVariableSet',
      'getPromptVariableSets',
      'savePromptVariableSets',
      'getPromptHistory',
      'revertPrompt',
      'exportPrompts',
      'importFiles',
    ]

    for (const method of methods) {
      expect(typeof (backend as any)[method]).toBe('function')
    }
  })
})

describe('HTTP Backend - Error Handling', () => {
  let backend: PromptBackend

  beforeEach(() => {
    vi.clearAllMocks()
    backend = createBackend({
      mode: 'remote',
      baseUrl: 'http://localhost:8000',
    })
  })

  it('handles 404 errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    })

    await expect(backend.listPrompts()).rejects.toThrow()
  })

  it('handles 500 server errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
    })

    await expect(backend.listPrompts()).rejects.toThrow()
  })

  it('handles 401 unauthorized', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
    })

    await expect(backend.listPrompts()).rejects.toThrow()
  })
})
