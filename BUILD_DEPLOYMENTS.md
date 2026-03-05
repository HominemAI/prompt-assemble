# Build & Deployment Guide

Different deployments require different configurations. This guide shows you how to build for each scenario.

---

## Build Options

### 1. **Local Deployment (Client-Side Only)**
```bash
npm run build:local
```

**What it includes:**
- ✅ **LocalBackend (IndexedDB)** - Browser storage
- ✅ **FileSystemBackend (File System Access API)** - Disk files
- ❌ RemoteBackend (HTTP API) - Not available
- Users **can switch** between Local ↔ Filesystem
- **No server required**

**Best for:**
- ✅ Cloudflare Pages
- ✅ Netlify / Vercel
- ✅ GitHub Pages
- ✅ Any static hosting
- ✅ User wants offline capability
- ✅ Complete control over data

**Deployment:**
```bash
npm run build:local
# Deploy dist/ to CF Pages, Netlify, GitHub Pages, etc.
```

**User Experience:**
- Defaults to LocalBackend (IndexedDB)
- Can switch to FileSystemBackend via Settings
- Works completely offline
- No server calls

---

### 2. **Full-Featured Deployment (With Flask API)**
```bash
npm run build:full
```

**What it includes:**
- ✅ **LocalBackend (IndexedDB)** - Browser storage
- ✅ **FileSystemBackend (File System Access API)** - Disk files
- ✅ **RemoteBackend (HTTP/Flask API)** - Central server
- Users **can switch** between all 3 backends
- **Flask server required**

**Best for:**
- ✅ Self-hosted deployments
- ✅ Private servers
- ✅ Team collaboration
- ✅ Central repository
- ✅ Multi-device sync
- ✅ When you control the server

**Deployment:**
```bash
# 1. Build the UI
npm run build:full

# 2. Start Flask server
export PROMPT_ASSEMBLE_UI=true
python -m prompt_assemble.api.server

# 3. Visit http://localhost:8000
```

**User Experience:**
- Defaults to RemoteBackend (central API)
- Can switch to LocalBackend (offline) or FileSystemBackend (disk)
- All data sync'd to central server
- Users can go offline temporarily with Local mode

---

## Comparison Table

| Feature | **Local** (CF Pages) | **Full** (Flask) |
|---------|----------------------|-----------------|
| **LocalBackend** | ✅ Yes | ✅ Yes |
| **FileSystemBackend** | ✅ Yes | ✅ Yes |
| **RemoteBackend** | ❌ No | ✅ Yes |
| **Backend Switching** | ✅ Local ↔ Filesystem | ✅ All 3 |
| **Server Required** | ❌ No | ✅ Flask |
| **Offline Capable** | ✅ Full | ✅ Partial (Local mode) |
| **Data Control** | User device | User device + Server |
| **Multi-Device Sync** | ❌ Manual (cloud sync folder) | ✅ Automatic |
| **Hosting** | Any static host | Self-hosted |
| **Cost** | Free (CF Pages) | Server cost |
| **Setup Complexity** | 🟢 Simple | 🟡 Moderate |

---

## Deployment Scenarios

### Scenario A: Deploy to Cloudflare Pages

```bash
# 1. Build
npm run build:local

# 2. Deploy via git (CF Pages auto-builds)
# OR deploy manually:
wrangler pages deploy dist/

# 3. Users visit your-app.pages.dev
#    → Defaults to LocalBackend (IndexedDB)
#    → Can switch to FileSystemBackend via Settings
#    → Works completely offline
```

### Scenario B: Deploy to Netlify

```bash
# 1. Build
npm run build:local

# 2. Deploy via git or CLI
netlify deploy --prod --dir=dist

# 3. Same as CF Pages behavior - fully client-side
```

### Scenario C: Deploy to GitHub Pages

```bash
# 1. Build
npm run build:local

# 2. Commit & push
git add dist/
git commit -m "Build"
git push origin main

# 3. GitHub Pages serves static app
```

### Scenario D: Docker with Flask (Full Stack)

```bash
# 1. Build
npm run build:full

# 2. Flask server picks it up from src/prompt_assemble/api/static/
docker build -t prompt-assemble .
docker run -p 8000:8000 prompt-assemble

# 3. Serves UI + API
# Users get all 3 backends
```

### Scenario E: Separate UI + API Servers

```bash
# UI Server (Netlify, Vercel, etc.)
npm run build:full
# Deploy to Netlify
# Note: Defaults to RemoteBackend

# API Server (Heroku, Railway, AWS, etc.)
export PROMPT_ASSEMBLE_UI=false
export FLASK_PORT=5000
python -m prompt_assemble.api.server

# Users visit UI on Netlify
# → App calls /api/... on your API server
# → All 3 backends available (user selects Remote)
```

---

## Environment Variables at Build Time

Vite exposes environment variables prefixed with `REACT_APP_`:

```typescript
// In your code:
const locked = (window as any).REACT_APP_LOCKED_BACKEND_MODE
const defaultMode = (window as any).REACT_APP_DEFAULT_BACKEND_MODE
```

### Available Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `REACT_APP_LOCKED_BACKEND_MODE` | Lock to single backend | `local`, `filesystem` |
| `REACT_APP_DEFAULT_BACKEND_MODE` | Default if not locked | `local`, `filesystem`, `remote` |

### Setting Variables

**On macOS/Linux:**
```bash
REACT_APP_LOCKED_BACKEND_MODE=local npm run build
```

**On Windows (PowerShell):**
```powershell
$env:REACT_APP_LOCKED_BACKEND_MODE="local"
npm run build
```

**On Windows (Command Prompt):**
```cmd
set REACT_APP_LOCKED_BACKEND_MODE=local
npm run build
```

**In package.json scripts:**
```json
{
  "scripts": {
    "build:custom": "REACT_APP_LOCKED_BACKEND_MODE=custom tsc && vite build"
  }
}
```

---

## Troubleshooting

### "Backend is locked" message in Settings

**Expected behavior:** The app is deployed with a locked backend mode.

**To unlock:**
1. Build with `npm run build:full` instead
2. Or select a different build command

### RemoteBackend not working

**Cause:** No Flask API server running

**Solution:**
1. If you deployed to CF Pages, use `build:local` instead
2. If you need RemoteBackend, run Flask server:
   ```bash
   export PROMPT_ASSEMBLE_UI=true
   python -m prompt_assemble.api.server
   ```

### Can't select FileSystemBackend

**Cause:** Browser doesn't support File System Access API

**Solution:**
- Use Chrome/Edge (v86+), Safari (15.2+)
- Or use LocalBackend instead

### Build size too large

**Note:** 6.2 MB build is expected (includes jszip for export functionality)

**To optimize:**
- Use dynamic imports for heavy libraries
- Tree-shake unused dependencies
- Consider code-splitting

---

## Quick Reference

```bash
# Development
npm run dev                    # Local dev server

# Client-side only (no server needed)
npm run build:local           # CF Pages, Netlify, GitHub Pages

# Full-featured (with Flask API)
npm run build:full            # All backends, requires Flask
npm run build                 # Same as build:full (default)

# Preview built app locally
npm run preview
```

---

## Best Practices

1. **For CF Pages/Netlify:** Use `build:local`
   - Users get LocalBackend + FileSystemBackend
   - No server maintenance needed
   - Cheap/free hosting

2. **For Team/Self-Hosted:** Use `build:full`
   - Users get all 3 backends
   - Central repository via RemoteBackend
   - More features

3. **Version Your Builds:**
   ```bash
   npm run build:local
   mv dist/ dist-v1.0.0
   ```

---

**Last Updated:** March 2026
