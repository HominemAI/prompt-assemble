#!/bin/bash
set -e

echo "🔨 Building prompt-assemble..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📦 Step 1: Installing frontend dependencies...${NC}"
cd src/prompt_assemble/ui/frontend
npm install

echo -e "${BLUE}🏗️  Step 2: Building frontend with Vite...${NC}"
npm run build

echo -e "${BLUE}✅ Step 3: Frontend built successfully!${NC}"
echo ""
echo -e "${GREEN}✨ Build complete!${NC}"
echo ""
echo "To run the app, execute:"
echo "  cd $PROJECT_ROOT"
echo "  export PROMPT_ASSEMBLE_UI=true"
echo "  python -m prompt_assemble.ui.server"
echo ""
echo "Then visit: http://localhost:5000"
