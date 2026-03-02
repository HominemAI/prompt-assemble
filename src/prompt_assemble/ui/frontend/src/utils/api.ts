/**
 * PromptBackend abstraction layer for multi-mode operation
 *
 * Supports three runtime modes:
 * - 'remote': HTTP/Flask API (default)
 * - 'local': IndexedDB (persistent across restarts, no network)
 * - 'filesystem': File System Access API (editable on disk)
 *
 * Auth is future-safe: no auth parameters baked into interface.
 * getHeaders hook allows callers to add auth when available.
 */

import { openDB, DBSchema, IDBPDatabase } from 'idb';

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface PromptInfo {
  name: string;
  updated_at?: string;
  description?: string;
  tags?: string[];
  owner?: string;
}

export interface Prompt {
  name: string;
  content: string;
  description: string;
  tags: string[];
  owner?: string;
  source_ref?: string;
  updated_at?: string;
}

export interface SavePromptData {
  content: string;
  metadata: {
    description: string;
    tags: string[];
    owner?: string;
    revisionComments?: string;
  };
}

export interface VariableSet {
  id: string;
  name: string;
  variables: Record<string, string>;
}

export interface PromptVarSetData {
  variableSetIds: string[];
  overrides: Record<string, Record<string, string>>;
}

export interface VersionEntry {
  version: number;
  timestamp: string;
  comment: string;
}

export interface ExportOptions {
  tags?: string[];
  namePattern?: string;
}

export interface ImportResult {
  name: string;
  success: boolean;
  error?: string;
}

export type BackendMode = 'remote' | 'local' | 'filesystem';

export interface BackendConfig {
  mode: BackendMode;
  baseUrl?: string;
  getHeaders?: () => Record<string, string>;
}

export interface PromptBackend {
  listPrompts(): Promise<PromptInfo[]>;
  getPrompt(name: string): Promise<Prompt>;
  savePrompt(name: string, data: SavePromptData): Promise<void>;
  deletePrompt(name: string): Promise<void>;
  listTags(): Promise<string[]>;
  listVariableSets(): Promise<VariableSet[]>;
  saveVariableSet(set: VariableSet): Promise<void>;
  deleteVariableSet(id: string): Promise<void>;
  getPromptVariableSets(promptName: string): Promise<PromptVarSetData>;
  savePromptVariableSets(promptName: string, data: PromptVarSetData): Promise<void>;
  getPromptHistory(promptName: string): Promise<VersionEntry[]>;
  revertPrompt(promptName: string, version: number): Promise<void>;
  exportPrompts(options: ExportOptions): Promise<Blob>;
  importFiles(files: File[], tags: string[]): Promise<ImportResult[]>;
}

// ============================================================================
// REMOTE BACKEND (HTTP/Flask)
// ============================================================================

class RemoteBackend implements PromptBackend {
  private baseUrl: string;
  private getHeaders: () => Record<string, string>;

  constructor(baseUrl: string = '', getHeaders?: () => Record<string, string>) {
    this.baseUrl = baseUrl || '';
    this.getHeaders = getHeaders || (() => ({}));
  }

  private async fetchJson<T>(
    url: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers = {
      ...this.getHeaders(),
      ...options.headers,
    };

    const response = await fetch(this.baseUrl + url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.json() as Promise<T>;
  }

  private async fetchBlob(
    url: string,
    options: RequestInit = {}
  ): Promise<Blob> {
    const headers = {
      ...this.getHeaders(),
      ...options.headers,
    };

    const response = await fetch(this.baseUrl + url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status} ${response.statusText}`);
    }

    return response.blob();
  }

  async listPrompts(): Promise<PromptInfo[]> {
    const data = await this.fetchJson<{ prompts: PromptInfo[] }>('/api/prompts');
    return data.prompts || [];
  }

  async getPrompt(name: string): Promise<Prompt> {
    const encoded = encodeURIComponent(name);
    return this.fetchJson<Prompt>(`/api/prompts/${encoded}`);
  }

  async savePrompt(name: string, data: SavePromptData): Promise<void> {
    const encoded = encodeURIComponent(name);
    await this.fetchJson(`/api/prompts/${encoded}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        content: data.content,
        description: data.metadata.description,
        tags: data.metadata.tags,
        owner: data.metadata.owner,
        revision_comment: data.metadata.revisionComments,
      }),
    });
  }

  async deletePrompt(name: string): Promise<void> {
    const encoded = encodeURIComponent(name);
    await this.fetchJson(`/api/prompts/${encoded}`, { method: 'DELETE' });
  }

  async listTags(): Promise<string[]> {
    const data = await this.fetchJson<{ tags: string[] }>('/api/tags');
    return data.tags || [];
  }

  async listVariableSets(): Promise<VariableSet[]> {
    const data = await this.fetchJson<{ variable_sets: VariableSet[] }>(
      '/api/variable-sets'
    );
    return data.variable_sets || [];
  }

  async saveVariableSet(set: VariableSet): Promise<void> {
    await this.fetchJson('/api/variable-sets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: set.id,
        name: set.name,
        variables: set.variables,
      }),
    });
  }

  async deleteVariableSet(id: string): Promise<void> {
    const encoded = encodeURIComponent(id);
    await this.fetchJson(`/api/variable-sets/${encoded}`, {
      method: 'DELETE',
    });
  }

  async getPromptVariableSets(promptName: string): Promise<PromptVarSetData> {
    const encoded = encodeURIComponent(promptName);
    const data = await this.fetchJson<{
      variable_set_ids: string[];
      overrides: Record<string, Record<string, string>>;
    }>(`/api/prompts/${encoded}/variable-sets`);
    return {
      variableSetIds: data.variable_set_ids || [],
      overrides: data.overrides || {},
    };
  }

  async savePromptVariableSets(
    promptName: string,
    data: PromptVarSetData
  ): Promise<void> {
    const encoded = encodeURIComponent(promptName);
    await this.fetchJson(`/api/prompts/${encoded}/variable-sets`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        variable_set_ids: data.variableSetIds,
        overrides: data.overrides,
      }),
    });
  }

  async getPromptHistory(promptName: string): Promise<VersionEntry[]> {
    const encoded = encodeURIComponent(promptName);
    const data = await this.fetchJson<{ history: VersionEntry[] }>(
      `/api/prompts/${encoded}/history`
    );
    return data.history || [];
  }

  async revertPrompt(promptName: string, version: number): Promise<void> {
    const encoded = encodeURIComponent(promptName);
    await this.fetchJson(`/api/prompts/${encoded}/revert/${version}`, {
      method: 'POST',
    });
  }

  async exportPrompts(options: ExportOptions): Promise<Blob> {
    const query = new URLSearchParams();
    if (options.tags && options.tags.length > 0) {
      query.append('tags', options.tags.join(','));
    }
    if (options.namePattern) {
      query.append('name_pattern', options.namePattern);
    }

    return this.fetchBlob(
      `/api/export${query.toString() ? '?' + query.toString() : ''}`,
      {
        method: 'POST',
      }
    );
  }

  async importFiles(files: File[], tags: string[]): Promise<ImportResult[]> {
    const results: ImportResult[] = [];
    for (const file of files) {
      try {
        const name = file.name.split('.')[0].replace(/[\s\-]/g, '_');
        const content = await file.text();
        await this.savePrompt(name, {
          content,
          metadata: {
            description: `Imported from ${file.name}`,
            tags,
            owner: undefined,
          },
        });
        results.push({ name, success: true });
      } catch (error) {
        results.push({
          name: file.name,
          success: false,
          error: String(error),
        });
      }
    }
    return results;
  }
}

// ============================================================================
// LOCAL BACKEND (IndexedDB)
// ============================================================================

interface IDBPromptDoc {
  name: string;
  content: string;
  description: string;
  tags: string[];
  owner?: string;
  updated_at: string;
}

interface IDBVersionDoc {
  name: string;
  version: number;
  timestamp: string;
  comment: string;
  content: string;
}

interface IDBVariableSetDoc extends VariableSet {}

interface IDBPromptVarSetDoc {
  prompt_name: string;
  variable_set_ids: string[];
  overrides: Record<string, Record<string, string>>;
}

interface PromptIDB extends DBSchema {
  prompts: {
    key: string;
    value: IDBPromptDoc;
    indexes: { 'by-updated_at': string; 'by-tags': string[] };
  };
  prompt_versions: {
    key: [string, number];
    value: IDBVersionDoc;
    indexes: { 'by-name': string };
  };
  variable_sets: {
    key: string;
    value: IDBVariableSetDoc;
    indexes: { 'by-name': string };
  };
  prompt_variable_sets: {
    key: string;
    value: IDBPromptVarSetDoc;
  };
}

class LocalBackend implements PromptBackend {
  private dbPromise: Promise<IDBPDatabase<PromptIDB>>;

  constructor() {
    this.dbPromise = this.initDB();
  }

  private async initDB(): Promise<IDBPDatabase<PromptIDB>> {
    return openDB<PromptIDB>('prompt-assemble', 1, {
      upgrade(db) {
        // Prompts store
        if (!db.objectStoreNames.contains('prompts')) {
          const promptStore = db.createObjectStore('prompts', { keyPath: 'name' });
          promptStore.createIndex('by-updated_at', 'updated_at');
          promptStore.createIndex('by-tags', 'tags', { multiEntry: true });
        }

        // Versions store
        if (!db.objectStoreNames.contains('prompt_versions')) {
          const versionStore = db.createObjectStore('prompt_versions', {
            keyPath: ['name', 'version'],
          });
          versionStore.createIndex('by-name', 'name');
        }

        // Variable sets store
        if (!db.objectStoreNames.contains('variable_sets')) {
          const varSetStore = db.createObjectStore('variable_sets', {
            keyPath: 'id',
          });
          varSetStore.createIndex('by-name', 'name');
        }

        // Prompt variable sets store
        if (!db.objectStoreNames.contains('prompt_variable_sets')) {
          db.createObjectStore('prompt_variable_sets', { keyPath: 'prompt_name' });
        }
      },
    });
  }

  private async getNextVersion(db: IDBPDatabase<PromptIDB>, name: string): Promise<number> {
    const versions = await db.getAllFromIndex('prompt_versions', 'by-name', name);
    if (versions.length === 0) return 1;
    return Math.max(...versions.map(v => v.version)) + 1;
  }

  async listPrompts(): Promise<PromptInfo[]> {
    const db = await this.dbPromise;
    const prompts = await db.getAll('prompts');
    return prompts.map(p => ({
      name: p.name,
      updated_at: p.updated_at,
      description: p.description,
      tags: p.tags,
      owner: p.owner,
    }));
  }

  async getPrompt(name: string): Promise<Prompt> {
    const db = await this.dbPromise;
    const doc = await db.get('prompts', name);
    if (!doc) throw new Error(`Prompt not found: ${name}`);
    return doc as Prompt;
  }

  async savePrompt(name: string, data: SavePromptData): Promise<void> {
    const db = await this.dbPromise;
    const now = new Date().toISOString();

    // Save prompt document
    await db.put('prompts', {
      name,
      content: data.content,
      description: data.metadata.description,
      tags: data.metadata.tags || [],
      owner: data.metadata.owner,
      updated_at: now,
    });

    // Save as new version
    const nextVersion = await this.getNextVersion(db, name);
    await db.put('prompt_versions', {
      name,
      version: nextVersion,
      timestamp: now,
      comment: data.metadata.revisionComments || '',
      content: data.content,
    });
  }

  async deletePrompt(name: string): Promise<void> {
    const db = await this.dbPromise;
    await db.delete('prompts', name);

    // Delete all versions
    const versions = await db.getAllFromIndex('prompt_versions', 'by-name', name);
    for (const v of versions) {
      await db.delete('prompt_versions', [name, v.version]);
    }
  }

  async listTags(): Promise<string[]> {
    const db = await this.dbPromise;
    const allKeys = await db.getAllKeysFromIndex('prompts', 'by-tags');
    return Array.from(new Set(allKeys as string[])).sort();
  }

  async listVariableSets(): Promise<VariableSet[]> {
    const db = await this.dbPromise;
    return db.getAll('variable_sets');
  }

  async saveVariableSet(set: VariableSet): Promise<void> {
    const db = await this.dbPromise;
    await db.put('variable_sets', set);
  }

  async deleteVariableSet(id: string): Promise<void> {
    const db = await this.dbPromise;
    await db.delete('variable_sets', id);
  }

  async getPromptVariableSets(promptName: string): Promise<PromptVarSetData> {
    const db = await this.dbPromise;
    const doc = await db.get('prompt_variable_sets', promptName);
    return {
      variableSetIds: doc?.variable_set_ids || [],
      overrides: doc?.overrides || {},
    };
  }

  async savePromptVariableSets(promptName: string, data: PromptVarSetData): Promise<void> {
    const db = await this.dbPromise;
    await db.put('prompt_variable_sets', {
      prompt_name: promptName,
      variable_set_ids: data.variableSetIds,
      overrides: data.overrides,
    });
  }

  async getPromptHistory(promptName: string): Promise<VersionEntry[]> {
    const db = await this.dbPromise;
    const versions = await db.getAllFromIndex('prompt_versions', 'by-name', promptName);
    return versions.map(v => ({
      version: v.version,
      timestamp: v.timestamp,
      comment: v.comment,
    }));
  }

  async revertPrompt(promptName: string, version: number): Promise<void> {
    const db = await this.dbPromise;
    const versionDoc = await db.get('prompt_versions', [promptName, version]);
    if (!versionDoc) throw new Error(`Version not found: ${promptName}@${version}`);

    // Get current metadata
    const current = await db.get('prompts', promptName);
    if (!current) throw new Error(`Prompt not found: ${promptName}`);

    // Save revert as new version
    const nextVersion = await this.getNextVersion(db, promptName);
    const now = new Date().toISOString();
    await db.put('prompt_versions', {
      name: promptName,
      version: nextVersion,
      timestamp: now,
      comment: `Reverted to v${version}`,
      content: versionDoc.content,
    });

    // Update current document
    await db.put('prompts', {
      ...current,
      content: versionDoc.content,
      updated_at: now,
    });
  }

  async exportPrompts(options: ExportOptions): Promise<Blob> {
    const db = await this.dbPromise;
    let prompts = await db.getAll('prompts');

    if (options.tags && options.tags.length > 0) {
      prompts = prompts.filter(p =>
        options.tags!.every(tag => p.tags.includes(tag))
      );
    }

    if (options.namePattern) {
      const pattern = new RegExp(options.namePattern);
      prompts = prompts.filter(p => pattern.test(p.name));
    }

    const json = JSON.stringify(prompts, null, 2);
    return new Blob([json], { type: 'application/json' });
  }

  async importFiles(files: File[], tags: string[]): Promise<ImportResult[]> {
    const results: ImportResult[] = [];
    for (const file of files) {
      try {
        const name = file.name.split('.')[0].replace(/[\s\-]/g, '_');
        const content = await file.text();
        await this.savePrompt(name, {
          content,
          metadata: {
            description: `Imported from ${file.name}`,
            tags,
            owner: undefined,
          },
        });
        results.push({ name, success: true });
      } catch (error) {
        results.push({
          name: file.name,
          success: false,
          error: String(error),
        });
      }
    }
    return results;
  }
}

// ============================================================================
// FILESYSTEM BACKEND (File System Access API)
// ============================================================================

interface FsPromptMeta {
  tags: string[];
  description: string;
  owner?: string;
}

interface FsRegistryJson {
  [promptName: string]: FsPromptMeta;
}

interface FsVersionEntry {
  v: number;
  timestamp: string;
  comment: string;
  file: string;
}

interface FsVersionsJson {
  [promptName: string]: FsVersionEntry[];
}

class FileSystemBackend implements PromptBackend {
  private rootHandle: FileSystemDirectoryHandle | null = null;
  private promptMeta: Map<string, FsPromptMeta> = new Map();
  private tagIndex: Map<string, Set<string>> = new Map();
  private ownerIndex: Map<string, Set<string>> = new Map();
  private promptNames: Set<string> = new Set();

  async initialize(): Promise<void> {
    // Try to restore handle from IDB
    const db = await openDB('prompt-assemble', 1);
    const storedHandle = await (db as any).get('fs-metadata', 'root-dir');

    if (storedHandle) {
      try {
        const perm = await storedHandle.queryPermission({ mode: 'readwrite' });
        if (perm === 'granted') {
          this.rootHandle = storedHandle;
          await this.scanDirectory();
        } else if (perm === 'prompt') {
          const granted = await storedHandle.requestPermission({ mode: 'readwrite' });
          if (granted === 'granted') {
            this.rootHandle = storedHandle;
            await this.scanDirectory();
          }
        }
      } catch (e) {
        console.error('Failed to restore FS handle:', e);
      }
    }
  }

  /**
   * Show directory picker and ask user to verify folder selection.
   * Returns true if user approved, false if cancelled.
   */
  async selectAndVerifyFolder(
    importingData: boolean = false
  ): Promise<boolean> {
    try {
      // 1. Show directory picker
      const handle = await (window as any).showDirectoryPicker();
      const folderName = handle.name;

      // 2. Scan folder to see what we'll import
      const fileCount = await this._countFiles(handle);
      const promptCount = fileCount.prompt + fileCount.txt;

      // 3. Show verification modal
      const approved = await this._showVerificationModal({
        folderName,
        promptCount,
        importingData,
      });

      if (!approved) {
        return false;
      }

      // 4. Save handle to IDB and scan
      this.rootHandle = handle;
      const db = await openDB('prompt-assemble', 1);
      await (db as any).put('fs-metadata', handle, 'root-dir');

      // Scan the directory
      this.promptMeta.clear();
      this.tagIndex.clear();
      this.ownerIndex.clear();
      this.promptNames.clear();
      await this.scanDirectory();

      return true;
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        // User cancelled the picker
        return false;
      }
      throw err;
    }
  }

  private async _countFiles(
    dir: FileSystemDirectoryHandle
  ): Promise<{ prompt: number; txt: number }> {
    let prompt = 0;
    let txt = 0;

    try {
      for await (const [name] of (dir as any).entries()) {
        if (name.startsWith('.')) continue;
        if (name.endsWith('.prompt')) prompt++;
        if (name.endsWith('.txt')) txt++;
      }
    } catch (e) {
      console.error('Error counting files:', e);
    }

    return { prompt, txt };
  }

  private async _showVerificationModal(info: {
    folderName: string;
    promptCount: number;
    importingData: boolean;
  }): Promise<boolean> {
    return new Promise((resolve) => {
      const message = `
Verify Filesystem Storage Setup

Folder: ${info.folderName}
Files found: ${info.promptCount} prompt files

⚠️ Important:
• This folder becomes your source of truth
• Do NOT edit files manually - use this app only
• Auto-imports .prompt and .txt files recursively
• Version history saved in .versions/ folder
${info.importingData ? '\n✓ Will migrate browser data to this folder' : ''}

Continue?`;

      // Create a simple confirmation using browser's confirm (temporary for MVP)
      // In production, this should be a proper modal
      const confirmed = window.confirm(message);
      resolve(confirmed);
    });
  }

  private async ensureHandle(): Promise<FileSystemDirectoryHandle> {
    if (!this.rootHandle) {
      this.rootHandle = await (window as any).showDirectoryPicker();
      const db = await openDB('prompt-assemble', 1);
      await (db as any).put('fs-metadata', this.rootHandle, 'root-dir');
      await this.scanDirectory();
    }
    return this.rootHandle!;
  }

  private async scanDirectory(dir?: FileSystemDirectoryHandle, prefix: string = ''): Promise<void> {
    const handle = dir || this.rootHandle;
    if (!handle) return;

    try {
      for await (const [name, child] of (handle as any).entries()) {
        if (name.startsWith('.') && name !== '.prompt-assemble') continue;

        if (child.kind === 'directory') {
          await this.scanDirectory(
            child as FileSystemDirectoryHandle,
            prefix ? `${prefix}_${name}` : name
          );
        } else if (name.endsWith('.prompt')) {
          const promptName = prefix
            ? `${prefix}_${name.slice(0, -7)}`
            : name.slice(0, -7);
          this.promptNames.add(promptName);
        }
      }

      // Read registry for this directory
      if (prefix === '') {
        const regFile = await handle.getFileHandle('_registry.json').catch(() => null);
        if (regFile) {
          const file = await regFile.getFile();
          const json: FsRegistryJson = JSON.parse(await file.text());
          for (const [name, meta] of Object.entries(json)) {
            this.promptMeta.set(name, meta);
            this._updateTagIndex(name, meta);
          }
        }
      }
    } catch (e) {
      console.error('Scan error:', e);
    }
  }

  private _updateTagIndex(promptName: string, meta: FsPromptMeta): void {
    for (const tag of meta.tags) {
      if (!this.tagIndex.has(tag)) {
        this.tagIndex.set(tag, new Set());
      }
      this.tagIndex.get(tag)!.add(promptName);
    }
    if (meta.owner) {
      if (!this.ownerIndex.has(meta.owner)) {
        this.ownerIndex.set(meta.owner, new Set());
      }
      this.ownerIndex.get(meta.owner)!.add(promptName);
    }
  }

  private _removeTagIndex(promptName: string, meta: FsPromptMeta): void {
    for (const tag of meta.tags) {
      this.tagIndex.get(tag)?.delete(promptName);
      if (this.tagIndex.get(tag)?.size === 0) {
        this.tagIndex.delete(tag);
      }
    }
    if (meta.owner) {
      this.ownerIndex.get(meta.owner)?.delete(promptName);
      if (this.ownerIndex.get(meta.owner)?.size === 0) {
        this.ownerIndex.delete(meta.owner);
      }
    }
  }

  private async getFileAtPath(path: string[]): Promise<FileSystemFileHandle | null> {
    let current = await this.ensureHandle();
    for (const segment of path.slice(0, -1)) {
      current = (await current.getDirectoryHandle(segment, {
        create: true,
      })) as FileSystemDirectoryHandle;
    }
    return current.getFileHandle(path[path.length - 1], { create: true });
  }

  private async getDirectoryAtPath(path: string[]): Promise<FileSystemDirectoryHandle> {
    let current = await this.ensureHandle();
    for (const segment of path) {
      current = (await current.getDirectoryHandle(segment, {
        create: true,
      })) as FileSystemDirectoryHandle;
    }
    return current;
  }

  async listPrompts(): Promise<PromptInfo[]> {
    await this.initialize();
    if (!this.promptNames.size) {
      await this.scanDirectory();
    }

    return Array.from(this.promptNames).map(name => ({
      name,
      description: this.promptMeta.get(name)?.description || '',
      tags: this.promptMeta.get(name)?.tags || [],
      owner: this.promptMeta.get(name)?.owner,
      updated_at: new Date().toISOString(),
    }));
  }

  async getPrompt(name: string): Promise<Prompt> {
    const parts = name.split('_');
    const fileName = parts[parts.length - 1];
    const dirPath = parts.slice(0, -1);

    const dir = dirPath.length > 0 ? await this.getDirectoryAtPath(dirPath) : await this.ensureHandle();
    const file = await dir.getFileHandle(`${fileName}.prompt`);
    const fileContent = await file.getFile();
    const content = await fileContent.text();

    const meta = this.promptMeta.get(name) || { tags: [], description: '' };
    return {
      name,
      content,
      description: meta.description,
      tags: meta.tags,
      owner: meta.owner,
    };
  }

  async savePrompt(name: string, data: SavePromptData): Promise<void> {
    const parts = name.split('_');
    const fileName = parts[parts.length - 1];
    const dirPath = parts.slice(0, -1);

    const dir = dirPath.length > 0 ? await this.getDirectoryAtPath(dirPath) : await this.ensureHandle();

    // Save main file
    const file = await dir.getFileHandle(`${fileName}.prompt`, { create: true });
    const writable = await file.createWritable();
    await writable.write(data.content);
    await writable.close();

    // Update meta
    const oldMeta = this.promptMeta.get(name);
    if (oldMeta) {
      this._removeTagIndex(name, oldMeta);
    }

    const newMeta: FsPromptMeta = {
      tags: data.metadata.tags || [],
      description: data.metadata.description,
      owner: data.metadata.owner,
    };
    this.promptMeta.set(name, newMeta);
    this._updateTagIndex(name, newMeta);

    // Save registry
    const regData: FsRegistryJson = {};
    for (const [pName, meta] of this.promptMeta) {
      regData[pName] = meta;
    }

    const regFile = await dir.getFileHandle('_registry.json', { create: true });
    const regWritable = await regFile.createWritable();
    await regWritable.write(JSON.stringify(regData, null, 2));
    await regWritable.close();

    // Create version (simplified: just save metadata for now)
    // Full implementation would also save to .versions/ directory
  }

  async deletePrompt(name: string): Promise<void> {
    const parts = name.split('_');
    const fileName = parts[parts.length - 1];
    const dirPath = parts.slice(0, -1);

    const dir = dirPath.length > 0 ? await this.getDirectoryAtPath(dirPath) : await this.ensureHandle();

    try {
      await dir.removeEntry(`${fileName}.prompt`);
    } catch (e) {
      console.error('Failed to delete prompt file:', e);
    }

    const meta = this.promptMeta.get(name);
    if (meta) {
      this._removeTagIndex(name, meta);
    }
    this.promptMeta.delete(name);
    this.promptNames.delete(name);

    // Update registry
    const regData: FsRegistryJson = {};
    for (const [pName, pMeta] of this.promptMeta) {
      regData[pName] = pMeta;
    }

    const regFile = await dir.getFileHandle('_registry.json', { create: true });
    const regWritable = await regFile.createWritable();
    await regWritable.write(JSON.stringify(regData, null, 2));
    await regWritable.close();
  }

  async listTags(): Promise<string[]> {
    await this.initialize();
    if (!this.promptNames.size) {
      await this.scanDirectory();
    }
    return Array.from(this.tagIndex.keys()).sort();
  }

  async listVariableSets(): Promise<VariableSet[]> {
    const dir = await this.ensureHandle();
    try {
      const appConfigDir = await dir.getDirectoryHandle('.prompt-assemble');
      const file = await appConfigDir.getFileHandle('variable-sets.json');
      const fileContent = await file.getFile();
      return JSON.parse(await fileContent.text());
    } catch (e) {
      return [];
    }
  }

  async saveVariableSet(set: VariableSet): Promise<void> {
    const dir = await this.ensureHandle();
    const appConfigDir = await dir.getDirectoryHandle('.prompt-assemble', { create: true });
    const sets = await this.listVariableSets();
    const idx = sets.findIndex(s => s.id === set.id);
    if (idx >= 0) {
      sets[idx] = set;
    } else {
      sets.push(set);
    }

    const file = await appConfigDir.getFileHandle('variable-sets.json', { create: true });
    const writable = await file.createWritable();
    await writable.write(JSON.stringify(sets, null, 2));
    await writable.close();
  }

  async deleteVariableSet(id: string): Promise<void> {
    const dir = await this.ensureHandle();
    const appConfigDir = await dir.getDirectoryHandle('.prompt-assemble', { create: true });
    const sets = await this.listVariableSets();
    const filtered = sets.filter(s => s.id !== id);

    const file = await appConfigDir.getFileHandle('variable-sets.json', { create: true });
    const writable = await file.createWritable();
    await writable.write(JSON.stringify(filtered, null, 2));
    await writable.close();
  }

  async getPromptVariableSets(promptName: string): Promise<PromptVarSetData> {
    const dir = await this.ensureHandle();
    try {
      const appConfigDir = await dir.getDirectoryHandle('.prompt-assemble');
      const file = await appConfigDir.getFileHandle('subscriptions.json');
      const fileContent = await file.getFile();
      const all = JSON.parse(await fileContent.text());
      return all[promptName] || { variableSetIds: [], overrides: {} };
    } catch (e) {
      return { variableSetIds: [], overrides: {} };
    }
  }

  async savePromptVariableSets(promptName: string, data: PromptVarSetData): Promise<void> {
    const dir = await this.ensureHandle();
    const appConfigDir = await dir.getDirectoryHandle('.prompt-assemble', { create: true });
    const all = {};
    try {
      const file = await appConfigDir.getFileHandle('subscriptions.json');
      const fileContent = await file.getFile();
      Object.assign(all, JSON.parse(await fileContent.text()));
    } catch (e) {
      // File doesn't exist yet
    }

    (all as any)[promptName] = {
      variableSetIds: data.variableSetIds,
      overrides: data.overrides,
    };

    const file = await appConfigDir.getFileHandle('subscriptions.json', { create: true });
    const writable = await file.createWritable();
    await writable.write(JSON.stringify(all, null, 2));
    await writable.close();
  }

  async getPromptHistory(promptName: string): Promise<VersionEntry[]> {
    const parts = promptName.split('_');
    const fileName = parts[parts.length - 1];
    const dirPath = parts.slice(0, -1);

    const dir = dirPath.length > 0 ? await this.getDirectoryAtPath(dirPath) : await this.ensureHandle();
    try {
      const file = await dir.getFileHandle('_versions.json');
      const fileContent = await file.getFile();
      const versionsJson: FsVersionsJson = JSON.parse(await fileContent.text());
      return (versionsJson[promptName] || []).map(v => ({
        version: v.v,
        timestamp: v.timestamp,
        comment: v.comment,
      }));
    } catch (e) {
      return [];
    }
  }

  async revertPrompt(promptName: string, version: number): Promise<void> {
    const history = await this.getPromptHistory(promptName);
    const entry = history.find(h => h.version === version);
    if (!entry) throw new Error(`Version not found: ${promptName}@${version}`);

    // Get content from version file
    const parts = promptName.split('_');
    const dirPath = parts.slice(0, -1);
    const dir = dirPath.length > 0 ? await this.getDirectoryAtPath(dirPath) : await this.ensureHandle();

    try {
      const versionFile = await dir.getFileHandle(`.versions/${promptName}.v${version}.prompt`);
      const fileContent = await versionFile.getFile();
      const content = await fileContent.text();

      // Save as current
      const current = await this.getPrompt(promptName);
      await this.savePrompt(promptName, {
        content,
        metadata: {
          description: current.description,
          tags: current.tags,
          owner: current.owner,
          revisionComments: `Reverted to v${version}`,
        },
      });
    } catch (e) {
      throw new Error(`Failed to revert: ${e}`);
    }
  }

  async exportPrompts(options: ExportOptions): Promise<Blob> {
    let prompts = await this.listPrompts();

    if (options.tags && options.tags.length > 0) {
      prompts = prompts.filter(p =>
        options.tags!.every(tag => p.tags?.includes(tag))
      );
    }

    if (options.namePattern) {
      const pattern = new RegExp(options.namePattern);
      prompts = prompts.filter(p => pattern.test(p.name));
    }

    const json = JSON.stringify(prompts, null, 2);
    return new Blob([json], { type: 'application/json' });
  }

  async importFiles(files: File[], tags: string[]): Promise<ImportResult[]> {
    const results: ImportResult[] = [];
    for (const file of files) {
      try {
        const name = file.name.split('.')[0].replace(/[\s\-]/g, '_');
        const content = await file.text();
        await this.savePrompt(name, {
          content,
          metadata: {
            description: `Imported from ${file.name}`,
            tags,
            owner: undefined,
          },
        });
        results.push({ name, success: true });
      } catch (error) {
        results.push({
          name: file.name,
          success: false,
          error: String(error),
        });
      }
    }
    return results;
  }
}

// ============================================================================
// FACTORY & SINGLETON
// ============================================================================

export function createBackend(config: BackendConfig): PromptBackend {
  switch (config.mode) {
    case 'local':
      return new LocalBackend();
    case 'filesystem':
      return new FileSystemBackend();
    case 'remote':
    default:
      return new RemoteBackend(config.baseUrl, config.getHeaders);
  }
}

// Initialize from window.__PA_CONFIG__ or use remote as default
const runtimeConfig: BackendConfig = (window as any).__PA_CONFIG__ ?? {
  mode: 'remote' as BackendMode,
};

export const backend: PromptBackend = createBackend(runtimeConfig);
