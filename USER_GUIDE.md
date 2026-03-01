# PAMBL User Guide

## What is PAMBL?

PAMBL (Prompt Assembly) is a tool for creating, managing, and organizing reusable prompts with dynamic variable substitution, composition, and versioning.

## Key Features

- **🔄 Dynamic Variables** - Replace placeholders with values at render time
- **📦 Prompt Composition** - Reuse and combine prompts together
- **🏷️ Tag System** - Organize and search prompts by tags
- **📝 Versioning** - Track changes and revert to previous versions
- **💾 Auto-Save** - Automatic local caching with manual commits to database
- **🎨 Web UI** - Beautiful interface with dark mode support
- **📤 Export** - Export selected prompts as JSON

## Quick Syntax Guide

### Variable Substitution
Replace variables with values using `[[VARIABLE_NAME]]`:

```
You are a {{ROLE}} expert.
Respond in {{TONE}} tone.
```

When rendered with:
- `ROLE = "Python"`
- `TONE = "friendly"`

Becomes:
```
You are a Python expert.
Respond in friendly tone.
```

### Prompt Injection
Include other prompts using `[[PROMPT: name]]`:

```
<<[PROMPT: system_instructions]>>

User request: {{USER_INPUT}}
```

### Tag-Based Injection
Inject multiple prompts by tags using `[[PROMPT_TAG: tag1, tag2]]`:

```
<<[PROMPT_TAG: safety, validation]>>

Your task:
{{TASK_DESCRIPTION}}
```

Matching prompts tagged with BOTH "safety" AND "validation" will be injected in order of creation (newest first).

### Limiting Results
Limit tag-based results to N most recent using `[[PROMPT_TAG:N: tag1, tag2]]`:

```
Recent best practices:
<<[PROMPT_TAG:3: best-practice, python]>>

Your code:
{{CODE}}
```

## Using the Web UI

### Create a New Prompt
1. Click **"+ New"** button
2. Enter prompt name
3. Write your prompt content
4. Add metadata (description, owner, tags)
5. Click **"Save"** button (or Ctrl+S)
6. Enter optional revision comment

### Manage Variables
1. Open a prompt with variables
2. Click **"Variables"** button in header
3. Select variable sets to apply
4. Override specific variables if needed
5. Changes auto-save locally

### Render a Prompt
1. Click **"Render"** button
2. View output in **XML** or **JSON** format
3. Click **"Copy"** to copy to clipboard

### Version History
1. Click **"History"** button
2. View all previous versions with dates and comments
3. Select a version and click **"Revert to Selected"**
4. Revert automatically saves as new version

### Export Prompts
1. Click **"Export"** button
2. Choose export type:
   - **Current Prompt** - Just the open prompt
   - **All Prompts** - Everything in database
   - **By Tags** - Prompts matching all selected tags
   - **By Name** - Pattern match (e.g., "greeting" matches "greeting_short")
3. Click **"Export as JSON"**
4. Save file to your computer

## UI Shortcuts

| Action | Shortcut |
|--------|----------|
| Save Current | `Ctrl+S` |
| Close All Tabs | Click "×" next to tab list |
| Lock/Unlock Tab | Click lock icon on tab |
| Toggle Theme | Theme toggle button in header |

## Variable Sets

Variable sets bundle related variables together:

```yaml
set_name: "Python Best Practices"
variables:
  NAMING_CONVENTION: "snake_case"
  INDENT_SIZE: "4"
  LINE_LENGTH: "88"
```

Apply to prompts and override specific values as needed.

## Tips & Tricks

### Bookmarks
Add HTML comments to mark important sections:
```html
<!-- BOOKMARK: Step 1 - Analysis -->
This section analyzes the input...

<!-- BOOKMARK: Step 2 - Processing -->
This section processes the data...
```

Shows token count and bookmark list in editor.

### Comments
Use `#!` for line comments (removed during rendering):
```
Your instructions:
#! These comments won't appear in output
- Do this
- Do that
```

Use `<!--  -->` for block comments:
```
<!--
This entire block
will be removed during rendering
-->
Main content here
```

### Nesting Prompts
Compose complex prompts from simpler ones:

```
System prompt:
<<[PROMPT: system_base]>>

Safety guidelines:
<<[PROMPT_TAG: safety]>>

User task:
{{TASK}}
```

### Draft vs. Commit
- **Draft (dirty)** - Local changes not yet saved to database
- **Saved (clean)** - Changes committed to database
- Dirty documents show `*` in tab name
- Click Save to commit revisions to version history

## Keyboard Navigation

| Key | Action |
|-----|--------|
| `Ctrl+S` | Save current prompt |
| `Tab` | Autocomplete [[PROMPT: suggestions |
| `Escape` | Close modal dialogs |

## Common Workflows

### Creating a Reusable Prompt Library
1. Create base prompts (system, safety, validation)
2. Tag them appropriately
3. Create composite prompts that inject via tags
4. Use variable sets for customization

### A/B Testing Prompts
1. Create version 1 of prompt
2. Save with comment "v1 baseline"
3. Modify and save with comment "v2 test variant"
4. View history to compare versions
5. Revert if needed

### Team Collaboration
1. Export prompts regularly
2. Share JSON files with team
3. Import as reference
4. Version history tracks all changes
5. Revision comments document intent

## Need Help?

- **Syntax questions** - Check the Render output (XML/JSON tabs)
- **Lost work?** - Check Version History for previous versions
- **Variable issues?** - Check Variables panel for active sets
- **Stuck?** - Try exporting and examining the JSON structure

---

**Current Version:** 0.0.2
**Database:** PostgreSQL with versioning support
**UI Features:** Auto-save, dark mode, syntax highlighting, autocomplete
