# Backend Storage Switching Guide

## Overview

The prompt-assemble web app now supports **runtime backend switching**. Users can seamlessly switch between three
storage modes without losing data:

- **🌐 Browser Only** (IndexedDB) - Default, offline-capable, device-isolated
- **📁 Filesystem** (File System Access API) - Disk-based, editable in code editors, version-controllable

## How It Works

### Opening Settings

1. Click the **⚙️ Settings** button in the top-right corner (next to light/dark mode toggle)
2. The Settings modal displays your current backend
3. Select the backend you want to switch to

### Switching to Filesystem Storage

When you click "Filesystem Storage":

1. **Import Decision**: Choose whether to import current browser data
    - ✓ Import browser data → Migrate all prompts, versions, variable sets, and subscriptions
    - ✗ Start fresh → Keep browser data; filesystem starts empty

2. **Folder Selection**: Click "Continue" to select a folder
    - Browser shows directory picker (OS native)
    - Choose an existing folder or create a new one
    - Preview shows file count and formats (.prompt, .txt files)

3. **Verification**: Confirm the folder will be used
   ```
   ⚠️ Important:
   • This folder becomes your source of truth
   • Do NOT edit files manually - use this app only
   • All .prompt and .txt files will be imported recursively
   • Version history saved in .versions/ folder
   ```

4. **Migration** (if importing): Data transfers from IndexedDB to filesystem
5. **Done**: App reloads with new backend

### Switching Back to Browser Storage

When you click "Browser Only":

1. Your filesystem folder remains **untouched** on disk
2. Your previous browser storage (IndexedDB) is **restored**
3. You can switch back to filesystem anytime — no data is lost

### Data Persistence

**Browser Storage (IndexedDB):**

- ✅ Persists across browser restarts
- ✅ Survives power outages
- ✓ Stored in browser's local storage (device-specific)
- ✓ ~100MB+ capacity (browser-dependent)

**Filesystem Storage:**

- ✅ Persists on disk in selected folder
- ✅ Survives all shutdowns
- ✓ Human-readable .prompt files
- ✓ Editable in VS Code, Vim, etc.
- ✓ Can be version-controlled (git)
- ✓ Shareable across devices (Google Drive, Dropbox, etc.)

## File Structure (Filesystem Backend)

When using filesystem storage, your folder looks like:

```
my-prompts/
├── system_prompt.prompt           # Current prompt content
├── user_task.prompt
├── _registry.json                 # Metadata (tags, owner, description)
├── _versions.json                 # Version history index
├── .versions/                     # Version backup files
│   ├── system_prompt.v1.prompt
│   ├── system_prompt.v2.prompt
│   └── user_task.v1.prompt
├── .prompt-assemble/              # App configuration (browser-only)
│   ├── variable-sets.json         # Stored variable sets
│   └── subscriptions.json         # Prompt-level variable subscriptions
└── subfolder/
    ├── nested_prompt.prompt
    ├── _registry.json
    └── _versions.json
```

**Important:**

- Only `.prompt` and `.txt` files are treated as prompts
- `_registry.json`, `_versions.json`, and `.prompt-assemble/` are managed by the app
- Don't manually edit these files — use the app UI only

## Data Migration Details

When switching backends with data import enabled:

### What Gets Migrated

1. **Prompts**
    - Content of each prompt
    - Metadata (description, tags, owner)
    - Revision comments

2. **Version History**
    - All previous versions are backed up
    - Timestamps and revision comments preserved

3. **Variable Sets**
    - Each variable set is recreated
    - Variable values are preserved

4. **Subscriptions**
    - Which prompts are subscribed to which variable sets
    - Per-set overrides are preserved

### Migration Log

During migration, the app logs progress:

```
[Migration] Starting data migration...
[Migration] Loading prompts from source backend...
[Migration] Found 15 prompts
[Migration] Migrating prompt: system_prompt
[Migration] Migrating variable set: team_defaults
[Migration] Migration complete!
```

## Use Cases

### Use Case 1: Developer Workflow

```
1. Start with Browser Storage (IndexedDB)
   └─ Draft prompts offline, no server needed

2. Switch to Filesystem Storage
   └─ Prompts are now .prompt files in a folder

3. Version control with Git
   └─ git add *.prompt
   └─ git commit -m "Update prompts"

4. Share via GitHub, GitLab, etc.
```

### Use Case 2: Team Collaboration

```
1. Store prompts in shared Google Drive folder
   └─ Team can edit using the app

2. Enable File System Access API
   └─ App reads/writes directly to Drive folder

3. Changes sync automatically
   └─ All team members see updates
```

### Use Case 3: Offline Work + Cloud Sync

```
1. Use Browser Storage for offline work
   └─ Works without internet

2. When online, switch to Filesystem
   └─ Import browser data to cloud-synced folder

3. Sync folder with Dropbox/OneDrive/Drive
   └─ Data available on all devices
```

## Environment Variable Configuration

If deploying with Flask, you can set the default backend via environment variable:

```bash
# Default: user chooses via UI
export PROMPT_ASSEMBLE_BACKEND=local  # or: remote, filesystem

# User can still override via Settings menu
```

## Troubleshooting

### "Permission denied" when switching to Filesystem

**Cause:** Browser doesn't have permission to access the folder

**Solution:**

1. Click "Continue" again
2. When permission dialog appears, click "Allow" or "Grant access"
3. If already denied, reset permissions in browser settings:
    - Chrome: Settings → Privacy → Site settings → File system access
    - Firefox: Not yet supported (tracked as feature request)

### "Folder structure unrecognized" error

**Cause:** Selected an incompatible folder

**Solution:**

1. Create a new empty folder
2. Switch to filesystem backend
3. App will initialize the folder with proper structure

### Data not showing after switch

**Cause:** Migration failed silently

**Solution:**

1. Check browser console (F12 → Console tab) for errors
2. If migration failed, switch back to previous backend
3. Try again, ensuring all data is selected for import

### Can't switch back to Browser Storage

**Cause:** Browser storage (IndexedDB) was cleared

**Solution:**

1. IndexedDB data was lost (browser clear cache, etc.)
2. Switch to filesystem backend instead
3. Browser storage cannot be recovered once cleared

## Technical Details

### Backend Switching Architecture

```typescript
// User clicks "Switch to Filesystem"
↓
App.handleBackendChange('filesystem', importData=true)
  ├─ If filesystem: FileSystemBackend.selectAndVerifyFolder()
  │   └─ User selects folder, app saves handle to IndexedDB
  │
  ├─ If importData: migrateBackends(oldBackend, newBackend)
  │   ├─ Copy all prompts
  │   ├─ Copy all versions
  │   ├─ Copy all variable sets
  │   ├─ Copy all subscriptions
  │   └─ Log progress
  │
  ├─ Create new backend instance
  ├─ Persist preference to localStorage
  ├─ Reload all data from new backend
  └─ Show success notification
```

### Storage of Folder Handle

The File System Access API handle is stored in IndexedDB for persistence:

```typescript
// On selection:
await idb.put('fs-metadata', directoryHandle, 'root-dir')

// On app startup:
const handle = await idb.get('fs-metadata', 'root-dir')
await handle.queryPermission({ mode: 'readwrite' })
```

This allows the app to:

1. Remember which folder was selected
2. Request permission automatically on next load
3. Seamlessly restore the connection

## Browser Support

| Browser | IndexedDB | File System Access API |
|---------|-----------|------------------------|
| Chrome  | ✅ Full    | ✅ v86+                 |
| Firefox | ✅ Full    | ❌ Not yet              |
| Safari  | ✅ Full    | ⚠️ Limited (15.2+)     |
| Edge    | ✅ Full    | ✅ v86+                 |

**Note:** If File System Access API is unavailable, filesystem backend will show a warning message.

## Security & Privacy

### Browser Storage (IndexedDB)

- ✅ Data stored locally in browser
- ✅ Not sent to any server
- ✅ Domain-isolated (can't be accessed cross-domain)
- ⚠️ Lost if browser cache is cleared
- ⚠️ Device-specific (not synced across devices)

### Filesystem Storage

- ✅ Data in your selected folder (under your control)
- ✅ Not sent to any server (except if folder is cloud-synced)
- ✅ Human-readable text files
- ✅ Can be encrypted or backed up via OS tools
- ⚠️ App has read-write access to selected folder

## FAQ

**Q: Can I edit .prompt files in VS Code while the app is running?**
A: No. The app reads and writes files; external edits may be overwritten. Close the app before manual edits, or use the
app UI only.

**Q: Will switching backends lose my data?**
A: No. If you enable "Import browser data", all data is migrated. If you disable it, old data remains on your device and
can be recovered by switching back.

**Q: Can I use the same folder on multiple computers?**
A: Yes, if the folder is synced (Dropbox, Google Drive, etc.). The first app instance to write will save its changes;
subsequent instances should refresh to see changes.

**Q: What if I delete files from the filesystem folder?**
A: The app treats the folder as source-of-truth. Deleted files are gone. Keep backups if important.

**Q: Can I have multiple folder locations?**
A: Currently, the app stores one filesystem location. You can switch folders manually by going back to Browser storage
and selecting a different folder later.

---

**Last Updated:** March 2026
