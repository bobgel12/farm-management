# Quick Start: Multi-Agent Development

## 🚀 Get Started in 3 Steps

### 1. Setup Agents
```bash
./scripts/setup-agents.sh
```

### 2. Start Agent Interaction
```bash
./scripts/agent-interaction.sh
```

### 3. Add Your First Feature
```bash
# Select option 1: Start new feature
# Enter feature name: your-feature-name
# Enter description: Brief description of what you want to build
```

## 🤖 Available Agents

| Agent | Focus Area | Key Files |
|-------|------------|-----------|
| **Frontend Specialist** | React, TypeScript, Material-UI | `frontend/src/**/*.tsx` |
| **Backend Specialist** | Django, API, Python | `backend/**/*.py` |
| **DevOps Specialist** | Docker, Deployment | `Dockerfile*`, `docker-compose*.yml` |
| **Testing Specialist** | Tests, Quality | `**/*.test.*`, `**/test_*.py` |
| **Security Specialist** | Security, Auth | `authentication/**/*.py` |
| **Database Specialist** | Database, Models | `**/models.py`, `**/migrations/` |
| **UI/UX Specialist** | Design, UX | `frontend/src/components/` |
| **Performance Specialist** | Performance, Optimization | All files |

## 📋 Common Workflows

### Add New Feature
1. Run `./scripts/agent-interaction.sh`
2. Select "1. Start new feature"
3. Enter feature details
4. Send messages to relevant agents
5. Monitor progress

### Check Status
1. Run `./scripts/agent-interaction.sh`
2. Select "2. Check agent status"
3. Review current tasks and progress

### Send Message to Agent
1. Run `./scripts/agent-interaction.sh`
2. Select "4. Send message to agent"
3. Choose agent and enter message
4. Message saved for agent to respond

### Monitor Activity
1. Run `./scripts/agent-interaction.sh`
2. Select "3. Monitor agent activity"
3. Review code quality and test status

## 💬 Agent Communication Examples

### Request API Endpoint
```markdown
@backend-specialist
I need a new API endpoint for farm statistics.

**Endpoint:** GET /api/farms/{id}/stats/
**Response:** Farm stats with houses and tasks
**Timeline:** Need by tomorrow
**Priority:** High
```

### Request UI Component
```markdown
@frontend-specialist
I need a new dashboard component.

**Component:** FarmDashboard
**Features:** Statistics cards, charts, task list
**API:** Will use /api/farms/{id}/stats/
**Timeline:** Need by tomorrow
**Priority:** High
```

### Request Testing
```markdown
@testing-specialist
I need tests for the new FarmDashboard component.

**Component:** FarmDashboard
**Test Types:** Unit tests, integration tests
**Coverage:** >80%
**Timeline:** Need by tomorrow
**Priority:** High
```

## 🔧 Quick Commands

### Check Everything
```bash
# Monitor all agents
./.cursor/agent-coordination/monitor-agents.sh

# Check code quality
./scripts/lint-check.sh

# Run all tests
cd frontend && npm test
cd backend && python manage.py test
```

### Update Status
```bash
# Update agent status
./scripts/agent-interaction.sh
# Select "5. Update agent status"

# Check for conflicts
./scripts/agent-interaction.sh
# Select "6. Check for conflicts"
```

### View Dashboard
```bash
# View agent dashboard
./scripts/agent-interaction.sh
# Select "8. View agent dashboard"
```

## 📊 Agent Status Tracking

### Current Status
```bash
cat .cursor/agent-coordination/status.md
```

### Performance Metrics
```bash
cat .cursor/agent-coordination/performance.md
```

### Agent Dashboard
```bash
cat .cursor/agent-coordination/dashboard.md
```

## 🎯 Best Practices

### 1. Clear Communication
- Be specific about requirements
- Include timelines and priorities
- Ask questions when uncertain
- Provide context for changes

### 2. Coordinate Dependencies
- Identify shared interfaces early
- Communicate changes that affect others
- Use feature branches for parallel work
- Merge frequently to avoid conflicts

### 3. Monitor Progress
- Check agent status regularly
- Use monitoring tools
- Review code quality
- Run tests frequently

### 4. Resolve Conflicts
- Discuss issues directly
- Consider trade-offs
- Document decisions
- Learn from differences

## 🚨 Troubleshooting

### Common Issues
1. **Agent not responding**: Check message files in `.cursor/agent-coordination/`
2. **Conflicts detected**: Use option 6 to check and resolve
3. **Tests failing**: Run quality checks with option 7
4. **Code quality issues**: Use `./scripts/fix-code.sh`

### Getting Help
1. Check agent logs: `.cursor/agent-logs/`
2. Review coordination rules: `.cursor/agent-coordination/collaboration-rules.md`
3. Use communication templates: `.cursor/agent-templates/`
4. Monitor agent activity: `./.cursor/agent-coordination/monitor-agents.sh`

## 🎉 Success!

You now have a fully functional multi-agent development system! 

- ✅ 8 specialized agents ready to work
- ✅ Parallel development capabilities
- ✅ Clear communication protocols
- ✅ Quality assurance tools
- ✅ Progress monitoring
- ✅ Conflict resolution

Start building amazing features with your AI development team! 🚀
