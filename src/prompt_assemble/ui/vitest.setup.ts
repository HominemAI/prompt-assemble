import { vi } from 'vitest'

// Mock IndexedDB
class MockIDBObjectStore {
  add = vi.fn().mockResolvedValue(undefined)
  clear = vi.fn().mockResolvedValue(undefined)
  delete = vi.fn().mockResolvedValue(undefined)
  get = vi.fn().mockResolvedValue(undefined)
  put = vi.fn().mockResolvedValue(undefined)
  getAll = vi.fn().mockResolvedValue([])
  getAllKeys = vi.fn().mockResolvedValue([])
  getKey = vi.fn().mockResolvedValue(undefined)
  index = vi.fn().return
  count = vi.fn().mockResolvedValue(0)
}

class MockIDBDatabase {
  transaction = vi.fn().mockReturnValue({
    objectStore: vi.fn().mockReturnValue(new MockIDBObjectStore()),
    abort: vi.fn(),
    oncomplete: null,
    onerror: null,
  })
  objectStoreNames = {
    contains: vi.fn().mockReturnValue(false),
    item: vi.fn().mockReturnValue(null),
    length: 0,
  }
  close = vi.fn()
  deleteObjectStore = vi.fn()
  createObjectStore = vi.fn()
}

global.indexedDB = {
  open: vi.fn().mockReturnValue({
    onsuccess: null,
    onerror: null,
    onupgradeneeded: null,
  }),
  deleteDatabase: vi.fn(),
} as any

// Mock File System Access API
global.showDirectoryPicker = vi.fn().mockResolvedValue({
  getFileHandle: vi.fn(),
  getDirectoryHandle: vi.fn(),
  entries: vi.fn().mockImplementation(function* () {
    yield ['test', { kind: 'file' }]
  }),
  queryPermission: vi.fn().mockResolvedValue('granted'),
  requestPermission: vi.fn().mockResolvedValue('granted'),
})

// Mock fetch
global.fetch = vi.fn()
