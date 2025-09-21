# Agent Coordination System

## Parallel Development Strategies

### 1. Feature-Based Parallel Development
When developing a new feature, agents can work in parallel on different aspects:

```
Feature: "Add Farm Management Dashboard"

Frontend Specialist:
- Create dashboard components
- Implement data visualization
- Handle user interactions

Backend Specialist:
- Design API endpoints
- Implement business logic
- Handle data processing

Database Specialist:
- Optimize queries
- Design indexes
- Handle data relationships

UI/UX Specialist:
- Design user interface
- Ensure accessibility
- Optimize user experience

Testing Specialist:
- Write unit tests
- Create integration tests
- Set up test data

Security Specialist:
- Review authentication
- Validate permissions
- Check data security
```

### 2. File-Based Parallel Development
Agents can work on different files simultaneously:

```
Frontend Specialist:
- src/components/Dashboard.tsx
- src/contexts/FarmContext.tsx
- src/services/farmApi.ts

Backend Specialist:
- farms/views.py
- farms/serializers.py
- farms/urls.py

Database Specialist:
- farms/migrations/0002_add_dashboard_fields.py
- farms/models.py (optimizations)

Testing Specialist:
- src/components/__tests__/Dashboard.test.tsx
- farms/tests.py (new tests)
```

### 3. Layer-Based Parallel Development
Work on different architectural layers:

```
Presentation Layer (Frontend + UI/UX):
- React components
- User interface design
- User experience optimization

Business Logic Layer (Backend + Security):
- API endpoints
- Business rules
- Security validation

Data Layer (Database + Performance):
- Database optimization
- Query performance
- Data integrity

Infrastructure Layer (DevOps + Security):
- Deployment configuration
- Environment setup
- Security hardening
```

## Agent Communication Protocols

### 1. Change Notifications
When an agent makes changes that affect other agents:

```markdown
@frontend-specialist @ui-ux-specialist
I've updated the Farm model to include a 'status' field.
This will affect the dashboard display and may require UI updates.

Changes made:
- Added 'status' field to Farm model
- Updated FarmSerializer
- Added status choices: 'active', 'inactive', 'maintenance'

Please review and update:
- Dashboard component to show status
- Farm list to include status filter
- UI to handle status display
```

### 2. Dependency Coordination
When agents need to coordinate on dependencies:

```markdown
@backend-specialist @frontend-specialist
I need the following API endpoints for the dashboard:

Required endpoints:
- GET /api/farms/{id}/stats/ - Farm statistics
- GET /api/farms/{id}/houses/ - Houses in farm
- GET /api/tasks/farm/{id}/ - Tasks for farm

Expected response format:
{
  "farm": {...},
  "houses": [...],
  "tasks": [...],
  "stats": {
    "total_houses": 5,
    "total_capacity": 1000,
    "current_population": 750
  }
}

Please implement these endpoints so I can integrate them.
```

### 3. Conflict Resolution
When agents have conflicting approaches:

```markdown
@all-agents
Conflict: Authentication approach for API calls

Frontend Specialist suggests: JWT tokens in localStorage
Backend Specialist suggests: HTTP-only cookies
Security Specialist suggests: Short-lived tokens with refresh

Let's discuss the trade-offs:

JWT in localStorage:
+ Simple implementation
+ Works with SPA
- Vulnerable to XSS
- No automatic expiration

HTTP-only cookies:
+ More secure
+ Automatic expiration
- Requires CSRF protection
- More complex implementation

Short-lived tokens:
+ Most secure
+ Automatic rotation
- Complex refresh logic
- More API calls

Recommendation: Use short-lived tokens with refresh mechanism
```

## Workflow Templates

### 1. New Feature Development
```markdown
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
```

### 2. Bug Fix Workflow
```markdown
## Bug: [Bug Description]

### Investigation Phase
- [ ] Testing Specialist: Reproduce bug
- [ ] Relevant Specialist: Identify root cause
- [ ] Security Specialist: Check security implications

### Fix Phase
- [ ] Relevant Specialist: Implement fix
- [ ] Testing Specialist: Write regression tests
- [ ] Security Specialist: Security review

### Validation Phase
- [ ] Testing Specialist: Run all tests
- [ ] Performance Specialist: Check performance impact
- [ ] All agents: Code review
```

### 3. Refactoring Workflow
```markdown
## Refactoring: [Component/Module Name]

### Analysis Phase
- [ ] Performance Specialist: Identify optimization opportunities
- [ ] Relevant Specialist: Plan refactoring approach
- [ ] Testing Specialist: Ensure test coverage

### Implementation Phase
- [ ] Relevant Specialist: Implement refactoring
- [ ] Testing Specialist: Update tests
- [ ] All agents: Coordinate on changes

### Validation Phase
- [ ] Testing Specialist: Run all tests
- [ ] Performance Specialist: Verify improvements
- [ ] All agents: Code review
```

## Best Practices for Parallel Development

### 1. Communication
- Use clear, descriptive commit messages
- Tag relevant agents in comments
- Document decisions and rationale
- Share progress regularly
- Ask questions early

### 2. Coordination
- Work on different files when possible
- Coordinate on shared interfaces
- Use feature branches for parallel work
- Merge frequently to avoid conflicts
- Review each other's work

### 3. Quality
- Maintain high code quality
- Write comprehensive tests
- Follow established patterns
- Document complex logic
- Regular code reviews

### 4. Conflict Prevention
- Define clear interfaces
- Use consistent naming conventions
- Follow established patterns
- Communicate changes early
- Regular synchronization

## Tools for Coordination

### 1. Git Workflow
```bash
# Create feature branch
git checkout -b feature/farm-dashboard

# Work in parallel
git checkout -b feature/farm-dashboard-frontend
git checkout -b feature/farm-dashboard-backend
git checkout -b feature/farm-dashboard-tests

# Merge when ready
git checkout feature/farm-dashboard
git merge feature/farm-dashboard-frontend
git merge feature/farm-dashboard-backend
git merge feature/farm-dashboard-tests
```

### 2. Code Review Process
```markdown
## Code Review Checklist

### Frontend Changes
- [ ] TypeScript types are correct
- [ ] Components are properly structured
- [ ] Error handling is implemented
- [ ] UI is responsive and accessible
- [ ] Tests are included

### Backend Changes
- [ ] API endpoints are properly designed
- [ ] Database queries are optimized
- [ ] Security is properly implemented
- [ ] Error handling is comprehensive
- [ ] Tests are included

### Infrastructure Changes
- [ ] Configuration is secure
- [ ] Deployment is properly configured
- [ ] Monitoring is in place
- [ ] Documentation is updated
- [ ] Rollback plan is available
```

### 3. Testing Strategy
```markdown
## Testing Approach

### Unit Tests
- Frontend: Component testing with React Testing Library
- Backend: Model and view testing with Django TestCase
- Database: Query testing and data integrity

### Integration Tests
- API endpoint testing
- Database integration testing
- Frontend-backend integration

### End-to-End Tests
- User workflow testing
- Cross-browser testing
- Performance testing

### Security Tests
- Authentication testing
- Authorization testing
- Input validation testing
- Vulnerability scanning
```

This coordination system ensures that multiple agents can work effectively in parallel while maintaining code quality and avoiding conflicts.
