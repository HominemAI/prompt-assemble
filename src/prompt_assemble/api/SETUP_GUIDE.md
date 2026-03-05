# Prompt Manager UI - Setup Guide

Complete guide for setting up and running the Prompt Manager web interface.

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm
- Flask for backend
- React 18 for frontend

### 1. Backend Setup

#### Install Dependencies
```bash
pip install flask flask-cors prompt-assemble
```

#### Create a Prompts Directory (Optional)
```bash
mkdir prompts
echo "Hello [[NAME]]!" > prompts/greeting.prompt
```

#### Run the Server
```bash
export PROMPT_ASSEMBLE_UI=true
python -c "
from prompt_assemble.sources import FileSystemSource
from prompt_assemble.api import run_server

source = FileSystemSource('./prompts')
run_server(source=source, port=5000, debug=True)
"
```

### 2. Frontend Setup

#### Install Dependencies
```bash
cd src/prompt_assemble/api/frontend
npm install
```

#### Start Development Server
```bash
npm start
```

The app will automatically open at `http://localhost:3000`

### 3. Access the UI

Open your browser and navigate to:
- Development: `http://localhost:3000`
- Production: `http://localhost:5000`

## Full Installation from Source

### Step 1: Clone and Setup Python Environment

```bash
cd /path/to/prompt-assemble
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -e ".[dev]"
pip install flask flask-cors
```

### Step 2: Setup Frontend

```bash
cd src/prompt_assemble/api/frontend

# Install dependencies
npm install

# Optional: Install development tools
npm install --save-dev typescript @types/react @types/node
```

### Step 3: Create Prompt Directory Structure

```bash
mkdir -p prompts/personas prompts/system

# Create example prompts
cat > prompts/greeting.prompt << 'EOF'
<!-- A friendly greeting -->
You are a helpful assistant.
Greet the user warmly: "Hello [[NAME]]!"
EOF

cat > prompts/personas/expert.prompt << 'EOF'
<!-- Expert persona for technical domains -->
You are an expert in [[DOMAIN]].
Provide authoritative guidance on the topic.
EOF

cat > prompts/system/_registry.json << 'EOF'
{
  "expert": {
    "description": "Expert persona for domain-specific tasks",
    "tags": ["persona", "professional"],
    "owner": "team-platform"
  }
}
EOF
```

### Step 4: Run Both Backend and Frontend

#### Terminal 1: Backend Server
```bash
export PROMPT_ASSEMBLE_UI=true
cd /path/to/prompt-assemble
python src/prompt_assemble/api/example_usage.py
```

#### Terminal 2: Frontend Development
```bash
cd /path/to/prompt-assemble/src/prompt_assemble/api/frontend
npm start
```

## Production Deployment

### Build Frontend

```bash
cd src/prompt_assemble/api/frontend
npm run build
```

The build output will be in `build/` directory.

### Serve with Flask

```python
from flask import Flask, send_from_directory
from prompt_assemble.sources import FileSystemSource
from prompt_assemble.api import create_app
import os

# Create app with source
source = FileSystemSource('./prompts')
app = create_app(source=source)

# Serve built React app
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_static(path):
    if path and os.path.exists(os.path.join('build', path)):
        return send_from_directory('build', path)
    return send_from_directory('build', 'index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Run Production Server

```bash
export PROMPT_ASSEMBLE_UI=true
python app.py
```

## Configuration

### Environment Variables

```bash
# Enable UI (required)
export PROMPT_ASSEMBLE_UI=true

# Server configuration
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export FLASK_DEBUG=false

# Database (if using DatabaseSource)
export DATABASE_URL=sqlite:///prompts.db
```

### Flask Config

```python
app_config = {
    'DEBUG': True,
    'TESTING': False,
    'JSON_SORT_KEYS': False,
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
}

app = create_app(source=source, config=app_config)
```

## Using Different Prompt Sources

### FileSystemSource

```python
from prompt_assemble.sources import FileSystemSource
from prompt_assemble.api import run_server

source = FileSystemSource('./prompts')
run_server(source=source)
```

**Directory Structure:**
```
prompts/
├── greeting.prompt
├── task.prompt
├── _registry.json
└── personas/
    ├── expert.prompt
    ├── teacher.prompt
    └── _registry.json
```

### DatabaseSource

```python
import sqlite3
from prompt_assemble.sources import DatabaseSource
from prompt_assemble.api import run_server

conn = sqlite3.connect('prompts.db')
source = DatabaseSource(conn)

# Add some prompts
source.save_prompt(
    'greeting',
    'Hello [[NAME]]!',
    description='Friendly greeting',
    tags=['greeting', 'basic']
)

run_server(source=source)
```

## API Integration

### Example: Custom Python Client

```python
import requests

BASE_URL = 'http://localhost:5000/api'

# List all prompts
response = requests.get(f'{BASE_URL}/prompts')
prompts = response.json()['prompts']

# Search prompts
response = requests.get(
    f'{BASE_URL}/prompts/search',
    params={'q': 'greeting', 'tags': ['basic']}
)
results = response.json()['results']

# Get prompt details
response = requests.get(f'{BASE_URL}/prompts/greeting')
prompt = response.json()

# Save prompt
response = requests.post(
    f'{BASE_URL}/prompts/new_prompt',
    json={
        'content': 'New content',
        'metadata': {
            'description': 'My prompt',
            'tags': ['custom'],
            'owner': 'alice'
        }
    }
)

# Export prompts
response = requests.post(
    f'{BASE_URL}/export',
    json={'tags': ['basic'], 'names': []}
)
exported = response.json()['export']
```

## Troubleshooting

### Backend Issues

#### Flask not found
```bash
pip install flask flask-cors
```

#### CORS errors
```bash
pip install flask-cors
# Make sure it's imported in server.py
```

#### Port already in use
```bash
# Change port
python -c "from prompt_assemble.api import run_server; run_server(port=8000)"

# Or kill existing process
lsof -ti:5000 | xargs kill -9  # macOS/Linux
```

### Frontend Issues

#### Node modules not installed
```bash
cd src/prompt_assemble/api/frontend
rm -rf node_modules package-lock.json
npm install
```

#### React not starting
```bash
# Check Node version
node --version  # Should be 16+

# Clear cache
npm cache clean --force
npm start
```

#### Blank page
1. Check browser console for errors (F12)
2. Verify backend is running: `curl http://localhost:5000/api/prompts`
3. Check that API responses are valid JSON

### Connection Issues

#### Can't connect to backend from frontend
```javascript
// In Development: Check frontend package.json
// Add proxy: "http://localhost:5000"

// In Production: Update API_URL in components
const API_URL = 'http://your-domain.com/api'
```

## Listeners and Events

### Track Changes

```python
from prompt_assemble.sources import FileSystemSource
from prompt_assemble.api import run_server

source = FileSystemSource('./prompts')

def on_change(event_type: str):
    print(f'Event: {event_type}')

source.add_listener(on_change)
run_server(source=source)
```

### Registry Events

- `"refreshed"` - Prompts reloaded from source
- `"prompt_saved"` - New/updated prompt saved (DatabaseSource only)

## Performance Optimization

### Caching

The UI uses in-memory caching for:
- Auto-save drafts
- Undo/redo history
- Loaded prompts

Configure cache size:
```python
# In components
const CACHE_MAX_SIZE = 100;  // MB
```

### Large Prompt Sets

For 1000+ prompts:
1. Use database source (faster than filesystem)
2. Enable pagination in explorer
3. Lazy-load prompt content
4. Use efficient search (Elasticsearch, etc.)

## Advanced Configuration

### Custom Components

Extend the UI with custom components:

```typescript
// src/components/CustomComponent.tsx
import React from 'react';

export const CustomComponent: React.FC<{
  data: any;
  onAction: (action: string) => void;
}> = ({ data, onAction }) => {
  return (
    <div className="custom-component">
      {/* Your custom UI */}
    </div>
  );
};
```

### Theming

Customize colors in CSS files:

```css
:root {
  --primary-color: #007acc;
  --danger-color: #dc3545;
  --success-color: #28a745;
}
```

### Extending API

Add custom endpoints:

```python
@app.route('/api/custom/<action>', methods=['POST'])
def custom_action(action):
    data = request.json
    # Your custom logic
    return jsonify({'result': 'success'})
```

## Support & Debugging

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('prompt_assemble.api')
logger.setLevel(logging.DEBUG)
```

### Check Browser DevTools

1. **Console**: Look for JS errors
2. **Network**: Verify API requests are successful
3. **Application**: Check LocalStorage and cookies
4. **Performance**: Monitor for bottlenecks

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Blank editor | Refresh page, check backend |
| Slow search | Use database source, increase page size |
| Save not working | Verify backend API is running |
| Tags not showing | Reload prompts (refresh button) |
| Autocomplete not appearing | Type `[[PROMPT:` to trigger |

## Next Steps

1. **Customize Prompts**: Add your own prompt files
2. **Set Up Database**: Switch to DatabaseSource for better performance
3. **Add Listeners**: Track events and create webhooks
4. **Deploy**: Follow production deployment guide
5. **Extend**: Create custom components and API endpoints

## See Also

- [Prompt Manager UI Documentation](./README.md)
- [Example Usage](./example_usage.py)
- [API Reference](#api-integration)
