#!/bin/bash

# Multi-Agent Development Setup Script
# This script sets up the multi-agent development environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_agent() {
    echo -e "${PURPLE}[AGENT]${NC} $1"
}

echo "🤖 Setting up Multi-Agent Development Environment..."

# Create agent directories
print_status "Creating agent workspace directories..."
mkdir -p .cursor/agents
mkdir -p .cursor/agent-logs
mkdir -p .cursor/agent-coordination
mkdir -p .cursor/agent-templates

# Create agent-specific workspaces
print_agent "Setting up Frontend Specialist workspace..."
mkdir -p .cursor/agents/frontend-specialist
cat > .cursor/agents/frontend-specialist/workspace.json << EOF
{
  "name": "Frontend Specialist",
  "focus": "React, TypeScript, Material-UI, Frontend Architecture",
  "files": [
    "frontend/src/**/*.tsx",
    "frontend/src/**/*.ts",
    "frontend/src/**/*.css",
    "frontend/package.json",
    "frontend/tsconfig.json"
  ],
  "tools": ["eslint", "prettier", "typescript", "react-testing-library"],
  "context": [
    "frontend/src/types/index.ts",
    "frontend/src/utils/index.ts",
    "frontend/src/services/api.ts"
  ]
}
EOF

print_agent "Setting up Backend Specialist workspace..."
mkdir -p .cursor/agents/backend-specialist
cat > .cursor/agents/backend-specialist/workspace.json << EOF
{
  "name": "Backend Specialist",
  "focus": "Django, Django REST Framework, Python, API Design",
  "files": [
    "backend/**/*.py",
    "backend/requirements.txt",
    "backend/pyproject.toml"
  ],
  "tools": ["black", "isort", "flake8", "mypy", "pytest"],
  "context": [
    "backend/farms/models.py",
    "backend/houses/models.py",
    "backend/tasks/models.py",
    "backend/authentication/views.py"
  ]
}
EOF

print_agent "Setting up DevOps Specialist workspace..."
mkdir -p .cursor/agents/devops-specialist
cat > .cursor/agents/devops-specialist/workspace.json << EOF
{
  "name": "DevOps Specialist",
  "focus": "Docker, Deployment, CI/CD, Infrastructure",
  "files": [
    "Dockerfile*",
    "docker-compose*.yml",
    "railway.json",
    "vercel.json",
    "nginx.conf",
    "scripts/*.sh"
  ],
  "tools": ["docker", "docker-compose", "nginx", "git", "bash"],
  "context": [
    "docker-compose.yml",
    "docker-compose.prod.yml",
    "scripts/dev-setup.sh",
    "scripts/start-dev.sh"
  ]
}
EOF

print_agent "Setting up Testing Specialist workspace..."
mkdir -p .cursor/agents/testing-specialist
cat > .cursor/agents/testing-specialist/workspace.json << EOF
{
  "name": "Testing Specialist",
  "focus": "Test Automation, Quality Assurance, Test Coverage",
  "files": [
    "**/*.test.ts",
    "**/*.test.tsx",
    "**/*.spec.ts",
    "**/*.spec.tsx",
    "**/test_*.py",
    "**/tests.py"
  ],
  "tools": ["jest", "react-testing-library", "pytest", "coverage"],
  "context": [
    "frontend/src/components/__tests__/",
    "backend/farms/tests.py",
    "backend/houses/tests.py"
  ]
}
EOF

print_agent "Setting up Security Specialist workspace..."
mkdir -p .cursor/agents/security-specialist
cat > .cursor/agents/security-specialist/workspace.json << EOF
{
  "name": "Security Specialist",
  "focus": "Application Security, Authentication, Data Protection",
  "files": [
    "backend/authentication/**/*.py",
    "backend/chicken_management/settings*.py",
    "frontend/src/contexts/AuthContext.tsx",
    "frontend/src/services/api.ts"
  ],
  "tools": ["bandit", "safety", "semgrep", "eslint-plugin-security"],
  "context": [
    "backend/authentication/views.py",
    "backend/chicken_management/settings.py",
    "frontend/src/contexts/AuthContext.tsx"
  ]
}
EOF

print_agent "Setting up Database Specialist workspace..."
mkdir -p .cursor/agents/database-specialist
cat > .cursor/agents/database-specialist/workspace.json << EOF
{
  "name": "Database Specialist",
  "focus": "Database Design, Optimization, Data Management",
  "files": [
    "backend/**/migrations/*.py",
    "backend/**/models.py",
    "database_dump.sql",
    "scripts/dump_database.sh",
    "scripts/restore_database.sh"
  ],
  "tools": ["django-migrations", "psql", "pg_dump", "pg_restore"],
  "context": [
    "backend/farms/models.py",
    "backend/houses/models.py",
    "backend/tasks/models.py"
  ]
}
EOF

print_agent "Setting up UI/UX Specialist workspace..."
mkdir -p .cursor/agents/ui-ux-specialist
cat > .cursor/agents/ui-ux-specialist/workspace.json << EOF
{
  "name": "UI/UX Specialist",
  "focus": "User Interface Design, User Experience, Accessibility",
  "files": [
    "frontend/src/components/**/*.tsx",
    "frontend/src/index.css",
    "frontend/public/**/*"
  ],
  "tools": ["axe-core", "lighthouse", "storybook", "chromatic"],
  "context": [
    "frontend/src/components/Layout.tsx",
    "frontend/src/components/Dashboard.tsx",
    "frontend/src/index.css"
  ]
}
EOF

print_agent "Setting up Performance Specialist workspace..."
mkdir -p .cursor/agents/performance-specialist
cat > .cursor/agents/performance-specialist/workspace.json << EOF
{
  "name": "Performance Specialist",
  "focus": "Application Performance, Optimization, Monitoring",
  "files": [
    "frontend/src/**/*.tsx",
    "frontend/src/**/*.ts",
    "backend/**/*.py",
    "nginx.conf"
  ],
  "tools": ["webpack-bundle-analyzer", "lighthouse", "django-debug-toolbar", "django-silk"],
  "context": [
    "frontend/package.json",
    "backend/chicken_management/settings.py",
    "nginx/nginx.conf"
  ]
}
EOF

# Create agent coordination files
print_status "Setting up agent coordination system..."

# Create agent communication template
cat > .cursor/agent-templates/communication-template.md << 'EOF'
# Agent Communication Template

## Change Notification
@[relevant-agents]
I've made changes to [file/feature] that may affect your work.

**Changes made:**
- [List specific changes]

**Impact on other agents:**
- [Describe how this affects other agents]

**Action required:**
- [List what other agents need to do]

## Dependency Request
@[target-agent]
I need [specific requirement] for [feature/component].

**Requirements:**
- [List specific requirements]

**Expected format:**
- [Describe expected format/structure]

**Timeline:**
- [When you need this by]

## Conflict Resolution
@all-agents
Conflict: [Description of conflict]

**Options:**
1. [Option 1 with pros/cons]
2. [Option 2 with pros/cons]
3. [Option 3 with pros/cons]

**Recommendation:**
[Your recommendation with reasoning]

**Decision needed by:**
[When decision is needed]
EOF

# Create agent workflow templates
cat > .cursor/agent-templates/feature-development.md << 'EOF'
# Feature Development Workflow

## Feature: [Feature Name]

### Planning Phase
- [ ] Backend Specialist: Design API endpoints
- [ ] Database Specialist: Design data model
- [ ] Frontend Specialist: Design component structure
- [ ] UI/UX Specialist: Create mockups/wireframes
- [ ] Security Specialist: Review security requirements

### Implementation Phase
- [ ] Backend Specialist: Implement API endpoints
- [ ] Database Specialist: Create migrations
- [ ] Frontend Specialist: Implement components
- [ ] UI/UX Specialist: Implement UI design
- [ ] Testing Specialist: Write tests

### Review Phase
- [ ] Security Specialist: Security review
- [ ] Performance Specialist: Performance review
- [ ] All agents: Code review
- [ ] Testing Specialist: Test execution

### Deployment Phase
- [ ] DevOps Specialist: Update deployment config
- [ ] All agents: Final testing
- [ ] DevOps Specialist: Deploy to production
EOF

# Create agent status tracking
cat > .cursor/agent-coordination/status.md << 'EOF'
# Agent Status Tracking

## Current Sprint: [Sprint Name]

### Active Agents
- [ ] Frontend Specialist: [Current task]
- [ ] Backend Specialist: [Current task]
- [ ] DevOps Specialist: [Current task]
- [ ] Testing Specialist: [Current task]
- [ ] Security Specialist: [Current task]
- [ ] Database Specialist: [Current task]
- [ ] UI/UX Specialist: [Current task]
- [ ] Performance Specialist: [Current task]

### Blocked Tasks
- [Agent]: [Blocked task] - [Reason] - [Blocked by]

### Completed Tasks
- [Agent]: [Completed task] - [Date]

### Upcoming Tasks
- [Agent]: [Upcoming task] - [Priority]
EOF

# Create agent performance tracking
cat > .cursor/agent-coordination/performance.md << 'EOF'
# Agent Performance Tracking

## Metrics

### Code Quality
- [ ] Frontend Specialist: [Quality score]
- [ ] Backend Specialist: [Quality score]
- [ ] DevOps Specialist: [Quality score]
- [ ] Testing Specialist: [Quality score]
- [ ] Security Specialist: [Quality score]
- [ ] Database Specialist: [Quality score]
- [ ] UI/UX Specialist: [Quality score]
- [ ] Performance Specialist: [Quality score]

### Test Coverage
- [ ] Frontend: [Coverage %]
- [ ] Backend: [Coverage %]
- [ ] Integration: [Coverage %]

### Performance
- [ ] Frontend: [Performance score]
- [ ] Backend: [Performance score]
- [ ] Database: [Performance score]

### Security
- [ ] Authentication: [Security score]
- [ ] Authorization: [Security score]
- [ ] Data Protection: [Security score]
EOF

# Create agent collaboration rules
cat > .cursor/agent-coordination/collaboration-rules.md << 'EOF'
# Agent Collaboration Rules

## Communication
1. Use clear, descriptive messages
2. Tag relevant agents when needed
3. Provide context for changes
4. Ask questions early
5. Share progress regularly

## Coordination
1. Work on different files when possible
2. Coordinate on shared interfaces
3. Use feature branches for parallel work
4. Merge frequently to avoid conflicts
5. Review each other's work

## Quality
1. Maintain high code quality
2. Write comprehensive tests
3. Follow established patterns
4. Document complex logic
5. Regular code reviews

## Conflict Resolution
1. Discuss the issue directly
2. Consider trade-offs
3. Seek consensus
4. Document decisions
5. Learn from differences
EOF

# Create agent monitoring script
cat > .cursor/agent-coordination/monitor-agents.sh << 'EOF'
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
EOF

chmod +x .cursor/agent-coordination/monitor-agents.sh

# Create agent coordination dashboard
cat > .cursor/agent-coordination/dashboard.md << 'EOF'
# Agent Coordination Dashboard

## Quick Actions
- [ ] Run agent monitor: `./.cursor/agent-coordination/monitor-agents.sh`
- [ ] Check agent status: `cat .cursor/agent-coordination/status.md`
- [ ] Review performance: `cat .cursor/agent-coordination/performance.md`
- [ ] Update collaboration rules: `cat .cursor/agent-coordination/collaboration-rules.md`

## Agent Workspaces
- Frontend Specialist: `.cursor/agents/frontend-specialist/`
- Backend Specialist: `.cursor/agents/backend-specialist/`
- DevOps Specialist: `.cursor/agents/devops-specialist/`
- Testing Specialist: `.cursor/agents/testing-specialist/`
- Security Specialist: `.cursor/agents/security-specialist/`
- Database Specialist: `.cursor/agents/database-specialist/`
- UI/UX Specialist: `.cursor/agents/ui-ux-specialist/`
- Performance Specialist: `.cursor/agents/performance-specialist/`

## Templates
- Communication: `.cursor/agent-templates/communication-template.md`
- Feature Development: `.cursor/agent-templates/feature-development.md`

## Monitoring
- Agent Monitor: `.cursor/agent-coordination/monitor-agents.sh`
- Status Tracking: `.cursor/agent-coordination/status.md`
- Performance Tracking: `.cursor/agent-coordination/performance.md`
EOF

print_success "Multi-agent development environment setup completed!"
echo ""
print_status "Agent workspaces created:"
echo "  📁 .cursor/agents/ - Individual agent workspaces"
echo "  📁 .cursor/agent-coordination/ - Coordination tools"
echo "  📁 .cursor/agent-templates/ - Communication templates"
echo ""
print_status "Available agents:"
echo "  🤖 Frontend Specialist - React, TypeScript, Material-UI"
echo "  🤖 Backend Specialist - Django, Django REST Framework, Python"
echo "  🤖 DevOps Specialist - Docker, Deployment, CI/CD"
echo "  🤖 Testing Specialist - Test Automation, Quality Assurance"
echo "  🤖 Security Specialist - Application Security, Authentication"
echo "  🤖 Database Specialist - Database Design, Optimization"
echo "  🤖 UI/UX Specialist - User Interface, User Experience"
echo "  🤖 Performance Specialist - Application Performance, Optimization"
echo ""
print_status "Quick start:"
echo "  📊 Monitor agents: ./.cursor/agent-coordination/monitor-agents.sh"
echo "  📝 Check status: cat .cursor/agent-coordination/status.md"
echo "  📋 View dashboard: cat .cursor/agent-coordination/dashboard.md"
echo ""
print_success "Ready for multi-agent development! 🚀"
