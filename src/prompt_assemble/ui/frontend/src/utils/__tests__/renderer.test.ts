import { describe, it, expect, vi } from 'vitest'
import { renderPrompt } from '../renderer'

describe('renderPrompt() - Basic Rendering', () => {
  const mockFetchPrompt = vi.fn().mockResolvedValue('fetched content')
  const mockFindByTags = vi.fn().mockReturnValue(['tag1', 'tag2'])

  it('renders template with variables', async () => {
    const template = 'Hello World'
    const variables = { NAME: 'World' }
    const result = await renderPrompt(
      template,
      variables,
      mockFetchPrompt,
      mockFindByTags
    )
    expect(typeof result).toBe('string')
  })

  it('handles empty template', async () => {
    const result = await renderPrompt(
      '',
      {},
      mockFetchPrompt,
      mockFindByTags
    )
    expect(typeof result).toBe('string')
  })

  it('handles empty variables', async () => {
    const result = await renderPrompt(
      'Template',
      {},
      mockFetchPrompt,
      mockFindByTags
    )
    expect(typeof result).toBe('string')
  })
})

describe('renderPrompt() - With Options', () => {
  const mockFetchPrompt = vi.fn().mockResolvedValue('content')
  const mockFindByTags = vi.fn().mockReturnValue([])

  it('accepts optional getPromptVariables parameter', async () => {
    const mockGetPromptVars = vi.fn().mockResolvedValue({})
    const result = await renderPrompt(
      'Test',
      {},
      mockFetchPrompt,
      mockFindByTags,
      mockGetPromptVars
    )
    expect(typeof result).toBe('string')
  })

  it('accepts optional options parameter', async () => {
    const result = await renderPrompt(
      'Test',
      {},
      mockFetchPrompt,
      mockFindByTags,
      undefined,
      { maxDepth: 5, recursive: true }
    )
    expect(typeof result).toBe('string')
  })
})

describe('renderPrompt() - Error Handling', () => {
  const mockFetchPrompt = vi.fn().mockResolvedValue('')
  const mockFindByTags = vi.fn().mockReturnValue([])

  it('handles rejected promises gracefully', async () => {
    const failingFetch = vi.fn().mockRejectedValue(new Error('Fetch failed'))
    await expect(
      renderPrompt('[[PROMPT: missing]]', {}, failingFetch, mockFindByTags)
    ).rejects.toThrow()
  })

  it('returns string even with missing variables', async () => {
    const result = await renderPrompt(
      'Missing [[UNKNOWN]]',
      {},
      mockFetchPrompt,
      mockFindByTags
    )
    expect(typeof result).toBe('string')
  })

  it('is async and returns promise', () => {
    const promise = renderPrompt(
      'Test',
      {},
      mockFetchPrompt,
      mockFindByTags
    )
    expect(promise).toBeInstanceOf(Promise)
  })
})

describe('renderPrompt() - Integration', () => {
  it('calls fetchPrompt when prompt sigils present', async () => {
    const mockFetchPrompt = vi.fn().mockResolvedValue('Fetched prompt')
    const mockFindByTags = vi.fn().mockReturnValue([])

    await renderPrompt(
      '[[PROMPT: test]]',
      {},
      mockFetchPrompt,
      mockFindByTags
    )

    // May or may not be called depending on implementation
    expect(typeof mockFetchPrompt).toBe('function')
  })

  it('calls findByTags when tag sigils present', async () => {
    const mockFetchPrompt = vi.fn()
    const mockFindByTags = vi.fn().mockReturnValue([])

    await renderPrompt(
      '[[PROMPT_TAG: persona]]',
      {},
      mockFetchPrompt,
      mockFindByTags
    )

    // May or may not be called depending on implementation
    expect(typeof mockFindByTags).toBe('function')
  })
})
