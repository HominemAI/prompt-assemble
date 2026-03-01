# Prompt Manager UI

A comprehensive React-based management interface for the `prompt-assemble` library. Provides a full-featured editor with syntax highlighting, revision tracking, and advanced prompt exploration.

## Features

### Left Panel - Prompt Explorer
- **Search**: Full-text search with partial name matching
- **Tag Filtering**: Filter prompts by tags (AND intersection)
- **Quick View**: Display prompt name, update date, and tags
- **Independent Scrolling**: Dedicated scrollbar for the prompt list
- **Create New**: Quick button to create new prompts

### Right Panel - Multi-Tab Editor
- **Tabbed Interface**: Edit multiple prompts simultaneously
- **Tab Management**:
  - Close button with dirty state indicator
  - Lock tabs to prevent accidental closure
  - Visual indicator of unsaved changes (●)
- **Independent Scrolling**: Editor has its own scrollbar

### Document Editor
- **Syntax Highlighting**: Visual cues for prompt-assemble sigils:
  - `[[VAR_NAME]]` - Variable substitution
  - `[[PROMPT: name]]` - Component injection
  - `[[PROMPT_TAG: tag1, tag2]]` - Tag-based injection
  - `<!-- comment -->` - Bookmarks
- **Auto-Save**: Cache-based auto-save (2 second debounce)
- **Manual Save**: Save button for explicit saves
- **Undo/Redo**: Keyboard shortcuts (Cmd/Ctrl + Z/Y)
- **Bookmark Navigation**: Jump between document bookmarks (HTML comments)
- **Live Autocomplete**:
  - Type `[[PROMPT:` to trigger
  - Search by prompt name
  - Press `/` to filter
  - Use arrow keys to navigate
  - Press Enter to insert

### Document Properties Modal
- **Name**: Prompt identifier
- **Description**: Detailed description of prompt purpose
- **Tags**: Space or comma-separated tags with autocomplete
- **Owner**: Team or individual responsible
- **Metadata Display**: Shows current revision info
- **Revision Comments**: Track changes between versions

### Export Feature
- **Export All**: Download all prompts as JSON
- **Export by Tags**: Select tags (AND intersection) to export subset
- **Export by Name**: Partial name matching for targeted export
- **Format**: Standard JSON with metadata and content

### Additional Features
- **Delete with Confirmation**: Double-confirmation to prevent accidents
- **Revision Tracking**: Each save creates a version with reference to previous
- **Independent Scroll Areas**:
  - Left panel (explorer) has dedicated scrollbar
  - Right panel (editor) has dedicated scrollbar
- **Tab Locking**: Prevent accidental closure with lock icon
- **Status Bar**: Line count, character count, bookmark count

## Environment Variables

```bash
# Enable the UI server
export PROMPT_ASSEMBLE_UI=true
```

## Installation

### Backend Setup

```python
from prompt_assemble.ui import run_server
from prompt_assemble.sources import FileSystemSource

source = FileSystemSource("./prompts")
run_server(source=source, host="127.0.0.1", port=5000)
```

### Frontend Setup

```bash
cd src/prompt_assemble/ui/frontend
npm install
npm start
```

## API Endpoints

### Prompt Management
- `GET /api/prompts` - List all prompts
- `GET /api/prompts/<name>` - Get single prompt
- `POST /api/prompts/<name>` - Save/update prompt
- `DELETE /api/prompts/<name>` - Delete prompt
- `GET /api/prompts/search?q=query&tags=tag1&tags=tag2` - Search prompts

### Metadata
- `GET /api/tags` - List all available tags

### Export
- `POST /api/export` - Export prompts
  ```json
  {
    "tags": ["persona", "technical"],
    "names": ["greeting"]
  }
  ```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Cmd/Ctrl + Z | Undo |
| Cmd/Ctrl + Y | Redo |
| Arrow Keys (in autocomplete) | Navigate suggestions |
| Enter (in autocomplete) | Insert selected prompt |
| Escape (in autocomplete) | Close autocomplete |

## Syntax Guide

### Pambl Language

#### Variable Substitution
```
Hello [[USER_NAME]]!
```

#### Component Injection
```
[[PROMPT: system_instructions]]
```

#### Tag-Based Injection
```
Personas available:
[[PROMPT_TAG: persona]]
```

#### Limited Tag Injection
```
First persona:
[[PROMPT_TAG:1: persona]]
```

#### Bookmarks (Comments)
```
<!-- First section: Introduction -->
Introduction content here

<!-- Second section: Instructions -->
Instructions here
```

## Revision System

Each document tracks:
- Previous version ID (references the prompt it was based on)
- Revision comments explaining changes
- Save timestamp
- Change indicator (dirty flag)

## File Structure

```
src/prompt_assemble/ui/
├── __init__.py                 # Module entry point
├── server.py                   # Flask backend + API
├── README.md                   # This file
└── frontend/
    ├── package.json
    ├── src/
    │   ├── App.tsx            # Main component
    │   ├── App.css
    │   ├── index.tsx
    │   ├── index.css
    │   ├── components/
    │   │   ├── PromptExplorer.tsx
    │   │   ├── EditorPanel.tsx
    │   │   ├── DocumentProperties.tsx
    │   └── └── ExportModal.tsx
    └── └── styles/
        ├── PromptExplorer.css
        ├── EditorPanel.css
        ├── DocumentProperties.css
        └── ExportModal.css
```

## Architecture

### Component Hierarchy

```
App
├── PromptExplorer (left panel)
├── EditorPanel (right panel, tabbed)
│   ├── Tabs
│   ├── Editor
│   └── Autocomplete
├── DocumentProperties (modal)
└── ExportModal (modal)
```

### State Management

- **App-level State**:
  - documents: Multi-tab document storage
  - prompts: Loaded prompts
  - allTags: Available tags

- **Component-level State**:
  - Editor: Undo/redo history, bookmarks, autocomplete
  - Explorer: Search query, selected filters

### Caching Strategy

- **Editor Cache**: In-memory `Map<docId, docState>` for quick recovery
- **Auto-Save**: 2-second debounce before backend save
- **Browser Cache**: LocalStorage support for session recovery (optional)

## Dependencies

### Backend
- Flask (web framework)
- flask-cors (CORS support)
- prompt-assemble (core library)

### Frontend
- React 18
- React Icons
- Prismjs (syntax highlighting support)

## Development

### Backend Development
```bash
cd src/prompt_assemble/ui
export PROMPT_ASSEMBLE_UI=true
python -m flask run
```

### Frontend Development
```bash
cd src/prompt_assemble/ui/frontend
npm start
```

### Production Build
```bash
cd src/prompt_assemble/ui/frontend
npm run build
# Build output in build/ directory
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Limitations & Future Enhancements

### Current Limitations
- No collaborative editing (single user only)
- No syntax validation (accepts any input)
- No diff view between revisions
- No fullscreen editor mode

### Future Features
- Collaborative editing with WebSockets
- Syntax validation and error highlighting
- Diff viewer for revisions
- Custom theme support
- Dark mode
- Keyboard command palette (Cmd+K)
- Prompt templates/snippets
- Batch operations
- Import from file

## License

MIT (inherited from prompt-assemble)
