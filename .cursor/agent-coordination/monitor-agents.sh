#!/bin/bash

# Agent Monitoring Script
# This script monitors agent activity and coordination

echo "🤖 Agent Activity Monitor"
echo "========================="

# Check agent workspaces
echo "📁 Agent Workspaces:"
for agent in .cursor/agents/*/; do
    if [ -d "$agent" ]; then
        agent_name=$(basename "$agent")
        echo "  ✅ $agent_name: Active"
    fi
done

# Check for conflicts
echo ""
echo "⚠️  Potential Conflicts:"
git diff --name-only | while read file; do
    echo "  📝 Modified: $file"
done

# Check test status
echo ""
echo "🧪 Test Status:"
if [ -f "frontend/package.json" ]; then
    cd frontend && npm test -- --passWithNoTests --watchAll=false > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✅ Frontend tests: Passing"
    else
        echo "  ❌ Frontend tests: Failing"
    fi
    cd ..
fi

if [ -f "backend/manage.py" ]; then
    cd backend && python manage.py test --verbosity=0 > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✅ Backend tests: Passing"
    else
        echo "  ❌ Backend tests: Failing"
    fi
    cd ..
fi

# Check code quality
echo ""
echo "🔍 Code Quality:"
if command -v eslint > /dev/null 2>&1; then
    cd frontend && npm run lint:check > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✅ Frontend linting: Passing"
    else
        echo "  ❌ Frontend linting: Issues found"
    fi
    cd ..
fi

if command -v flake8 > /dev/null 2>&1; then
    cd backend && flake8 . > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "  ✅ Backend linting: Passing"
    else
        echo "  ❌ Backend linting: Issues found"
    fi
    cd ..
fi

echo ""
echo "📊 Agent Status:"
echo "  🟢 Active agents: $(ls -1 .cursor/agents/ | wc -l)"
echo "  📝 Modified files: $(git diff --name-only | wc -l)"
echo "  🧪 Test status: $(if [ -f "frontend/package.json" ] && [ -f "backend/manage.py" ]; then echo "Mixed"; else echo "Unknown"; fi)"
