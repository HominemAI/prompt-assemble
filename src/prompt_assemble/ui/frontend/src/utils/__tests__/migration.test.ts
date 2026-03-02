import { describe, it, expect, beforeEach, vi } from 'vitest'
import { migrateBackends, clearBackendData } from '../migration'

const createMockBackend = () => ({
  listPrompts: vi.fn(),
  getPrompt: vi.fn(),
  savePrompt: vi.fn(),
  deletePrompt: vi.fn(),
  listTags: vi.fn(),
  listVariableSets: vi.fn(),
  saveVariableSet: vi.fn(),
  deleteVariableSet: vi.fn(),
  getPromptVariableSets: vi.fn(),
  savePromptVariableSets: vi.fn(),
  getPromptHistory: vi.fn(),
  revertPrompt: vi.fn(),
  exportPrompts: vi.fn(),
  importFiles: vi.fn(),
})

describe('migrateBackends()', () => {
  let fromBackend: any
  let toBackend: any

  beforeEach(() => {
    fromBackend = createMockBackend()
    toBackend = createMockBackend()
  })

  it('migrates prompts from source to target', async () => {
    const mockPrompts = [
      { name: 'prompt1', description: 'Test', tags: [], updated_at: '2025-01-01T00:00:00Z' },
    ]
    fromBackend.listPrompts.mockResolvedValue(mockPrompts)
    fromBackend.getPrompt.mockResolvedValue({
      name: 'prompt1',
      content: 'Content',
      description: 'Test',
      tags: [],
    })
    fromBackend.listVariableSets.mockResolvedValue([])
    toBackend.savePrompt.mockResolvedValue(undefined)

    await migrateBackends(fromBackend, toBackend)

    expect(fromBackend.listPrompts).toHaveBeenCalled()
    expect(toBackend.savePrompt).toHaveBeenCalled()
  })

  it('handles empty source backend', async () => {
    fromBackend.listPrompts.mockResolvedValue([])
    fromBackend.listVariableSets.mockResolvedValue([])
    toBackend.savePrompt.mockResolvedValue(undefined)

    await migrateBackends(fromBackend, toBackend)

    expect(fromBackend.listPrompts).toHaveBeenCalled()
  })

  it('calls progress callback if provided', async () => {
    const onProgress = vi.fn()
    fromBackend.listPrompts.mockResolvedValue([
      { name: 'prompt1', description: '', tags: [], updated_at: '2025-01-01T00:00:00Z' },
    ])
    fromBackend.getPrompt.mockResolvedValue({
      name: 'prompt1',
      content: 'Content',
      description: '',
      tags: [],
    })
    fromBackend.listVariableSets.mockResolvedValue([])

    await migrateBackends(fromBackend, toBackend, onProgress)

    expect(onProgress).toHaveBeenCalled()
  })

  it('returns promise that resolves', async () => {
    fromBackend.listPrompts.mockResolvedValue([])
    fromBackend.listVariableSets.mockResolvedValue([])

    const result = migrateBackends(fromBackend, toBackend)

    await expect(result).resolves.not.toThrow()
  })

  it('migrates variable sets', async () => {
    const mockSets = [
      { id: 'set1', name: 'Set 1', variables: { VAR1: 'value1' } },
    ]
    fromBackend.listPrompts.mockResolvedValue([])
    fromBackend.listVariableSets.mockResolvedValue(mockSets)
    toBackend.saveVariableSet.mockResolvedValue(undefined)

    await migrateBackends(fromBackend, toBackend)

    expect(toBackend.saveVariableSet).toHaveBeenCalled()
  })
})

describe('clearBackendData()', () => {
  let backend: any

  beforeEach(() => {
    backend = createMockBackend()
  })

  it('deletes all prompts and variable sets', async () => {
    backend.listPrompts.mockResolvedValue([
      { name: 'prompt1', description: '', tags: [], updated_at: '2025-01-01T00:00:00Z' },
    ])
    backend.listVariableSets.mockResolvedValue([
      { id: 'set1', name: 'Set 1', variables: {} },
    ])
    backend.deletePrompt.mockResolvedValue(undefined)
    backend.deleteVariableSet.mockResolvedValue(undefined)

    await clearBackendData(backend)

    expect(backend.deletePrompt).toHaveBeenCalled()
    expect(backend.deleteVariableSet).toHaveBeenCalled()
  })

  it('handles empty backend', async () => {
    backend.listPrompts.mockResolvedValue([])
    backend.listVariableSets.mockResolvedValue([])

    await clearBackendData(backend)

    expect(backend.deletePrompt).not.toHaveBeenCalled()
    expect(backend.deleteVariableSet).not.toHaveBeenCalled()
  })

  it('calls progress callback if provided', async () => {
    const onProgress = vi.fn()
    backend.listPrompts.mockResolvedValue([
      { name: 'prompt1', description: '', tags: [], updated_at: '2025-01-01T00:00:00Z' },
    ])
    backend.listVariableSets.mockResolvedValue([])
    backend.deletePrompt.mockResolvedValue(undefined)

    await clearBackendData(backend, onProgress)

    expect(onProgress).toHaveBeenCalled()
  })

  it('returns promise that resolves', async () => {
    backend.listPrompts.mockResolvedValue([])
    backend.listVariableSets.mockResolvedValue([])

    const result = clearBackendData(backend)

    await expect(result).resolves.not.toThrow()
  })
})
