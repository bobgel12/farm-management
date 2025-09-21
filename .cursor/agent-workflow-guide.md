# How to Interact with Multi-Agent System

## 🚀 Quick Start - Adding a New Feature

### Step 1: Initialize the Feature
```bash
# Create a new feature branch
git checkout -b feature/farm-dashboard

# Update agent status
echo "## Current Sprint: Farm Dashboard Feature

### Active Agents
- [ ] Frontend Specialist: Design dashboard components
- [ ] Backend Specialist: Create farm statistics API
- [ ] Database Specialist: Optimize farm queries
- [ ] UI/UX Specialist: Design dashboard layout
- [ ] Testing Specialist: Write dashboard tests
- [ ] Security Specialist: Review farm data access
- [ ] Performance Specialist: Optimize dashboard loading
- [ ] DevOps Specialist: Update deployment if needed

### Blocked Tasks
- None

### Completed Tasks
- None

### Upcoming Tasks
- [ ] Frontend Specialist: Create FarmDashboard component
- [ ] Backend Specialist: Implement /api/farms/{id}/stats/ endpoint
- [ ] Database Specialist: Add farm statistics queries
" > .cursor/agent-coordination/status.md
```

### Step 2: Coordinate with Agents

#### Frontend Specialist
```markdown
@frontend-specialist
I need to create a Farm Dashboard component with the following requirements:

**Requirements:**
- Display farm statistics (total houses, capacity, population)
- Show recent tasks for the farm
- Display house status overview
- Include charts for population trends

**API Endpoints Needed:**
- GET /api/farms/{id}/stats/ - Farm statistics
- GET /api/farms/{id}/houses/ - Houses in farm
- GET /api/tasks/farm/{id}/ - Tasks for farm

**Expected Response Format:**
```json
{
  "farm": {...},
  "houses": [...],
  "tasks": [...],
  "stats": {
    "total_houses": 5,
    "total_capacity": 1000,
    "current_population": 750,
    "population_trend": [...]
  }
}
```

**Timeline:** Need by end of day
**Priority:** High
```

#### Backend Specialist
```markdown
@backend-specialist
I need the following API endpoints for the Farm Dashboard:

**Required Endpoints:**
- GET /api/farms/{id}/stats/ - Farm statistics
- GET /api/farms/{id}/houses/ - Houses in farm  
- GET /api/tasks/farm/{id}/ - Tasks for farm

**Expected Response Format:**
```json
{
  "farm": {...},
  "houses": [...],
  "tasks": [...],
  "stats": {
    "total_houses": 5,
    "total_capacity": 1000,
    "current_population": 750,
    "population_trend": [...]
  }
}
```

**Database Fields Needed:**
- Farm: name, location, created_at
- House: name, capacity, current_population, farm_id
- Task: title, due_date, completed, farm_id

**Timeline:** Need by end of day
**Priority:** High
```

### Step 3: Monitor Progress
```bash
# Check agent activity
./.cursor/agent-coordination/monitor-agents.sh

# Review agent status
cat .cursor/agent-coordination/status.md

# Check for conflicts
git status
git diff --name-only
```

## 🛠️ Practical Agent Interaction Examples

### Example 1: Adding a New Farm Feature

#### 1. Frontend Specialist Work
```typescript
// Create FarmDashboard component
// File: frontend/src/components/FarmDashboard.tsx

import React, { useState, useEffect } from 'react';
import { Box, Grid, Card, CardContent, Typography } from '@mui/material';
import { Farm, House, Task } from '../types';
import { api } from '../services/api';

interface FarmStats {
  total_houses: number;
  total_capacity: number;
  current_population: number;
  population_trend: number[];
}

interface FarmDashboardProps {
  farmId: number;
}

const FarmDashboard: React.FC<FarmDashboardProps> = ({ farmId }) => {
  const [farm, setFarm] = useState<Farm | null>(null);
  const [houses, setHouses] = useState<House[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<FarmStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchFarmData = async () => {
      try {
        const [farmResponse, housesResponse, tasksResponse, statsResponse] = await Promise.all([
          api.get(`/farms/${farmId}/`),
          api.get(`/farms/${farmId}/houses/`),
          api.get(`/tasks/farm/${farmId}/`),
          api.get(`/farms/${farmId}/stats/`)
        ]);

        setFarm(farmResponse.data);
        setHouses(housesResponse.data);
        setTasks(tasksResponse.data);
        setStats(statsResponse.data.stats);
      } catch (error) {
        console.error('Error fetching farm data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFarmData();
  }, [farmId]);

  if (loading) return <div>Loading...</div>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {farm?.name} Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Farm Statistics</Typography>
              <Typography>Total Houses: {stats?.total_houses}</Typography>
              <Typography>Total Capacity: {stats?.total_capacity}</Typography>
              <Typography>Current Population: {stats?.current_population}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6">Recent Tasks</Typography>
              {tasks.slice(0, 5).map((task) => (
                <Typography key={task.id}>
                  {task.title} - {task.due_date}
                </Typography>
              ))}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default FarmDashboard;
```

#### 2. Backend Specialist Work
```python
# File: backend/farms/views.py

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count
from .models import Farm, House
from .serializers import FarmSerializer, HouseSerializer
from tasks.models import Task
from tasks.serializers import TaskSerializer

class FarmDetailView(generics.RetrieveAPIView):
    queryset = Farm.objects.all()
    serializer_class = FarmSerializer

class FarmHousesView(generics.ListAPIView):
    serializer_class = HouseSerializer
    
    def get_queryset(self):
        farm_id = self.kwargs['farm_id']
        return House.objects.filter(farm_id=farm_id)

@api_view(['GET'])
def farm_stats(request, farm_id):
    """Get farm statistics"""
    try:
        farm = Farm.objects.get(id=farm_id)
        houses = House.objects.filter(farm_id=farm_id)
        
        stats = {
            'total_houses': houses.count(),
            'total_capacity': houses.aggregate(Sum('capacity'))['capacity__sum'] or 0,
            'current_population': houses.aggregate(Sum('current_population'))['current_population__sum'] or 0,
            'population_trend': [750, 800, 720, 780, 750]  # Mock data for now
        }
        
        return Response({
            'farm': FarmSerializer(farm).data,
            'houses': HouseSerializer(houses, many=True).data,
            'tasks': TaskSerializer(Task.objects.filter(farm_id=farm_id)[:10], many=True).data,
            'stats': stats
        })
    except Farm.DoesNotExist:
        return Response({'error': 'Farm not found'}, status=status.HTTP_404_NOT_FOUND)
```

#### 3. Database Specialist Work
```python
# File: backend/farms/migrations/0003_add_farm_stats.py

from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('farms', '0002_alter_farm_options_alter_farm_contact_email_and_more'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='house',
            index=models.Index(fields=['farm', 'capacity'], name='farms_house_farm_capacity_idx'),
        ),
        migrations.AddIndex(
            model_name='house',
            index=models.Index(fields=['farm', 'current_population'], name='farms_house_farm_population_idx'),
        ),
    ]
```

#### 4. Testing Specialist Work
```typescript
// File: frontend/src/components/__tests__/FarmDashboard.test.tsx

import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import FarmDashboard from '../FarmDashboard';
import { api } from '../../services/api';

// Mock the API
jest.mock('../../services/api');
const mockedApi = api as jest.Mocked<typeof api>;

describe('FarmDashboard', () => {
  beforeEach(() => {
    mockedApi.get.mockResolvedValue({
      data: {
        id: 1,
        name: 'Test Farm',
        location: 'Test Location'
      }
    });
  });

  it('renders farm dashboard with statistics', async () => {
    render(
      <BrowserRouter>
        <FarmDashboard farmId={1} />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Test Farm Dashboard')).toBeInTheDocument();
    });
  });
});
```

### Example 2: Agent Communication During Development

#### Frontend Specialist to Backend Specialist
```markdown
@backend-specialist
I'm implementing the FarmDashboard component and need the API endpoints.

**Current Status:**
- Created FarmDashboard component
- Implemented basic UI structure
- Ready to integrate with API

**Questions:**
1. What's the exact response format for /api/farms/{id}/stats/?
2. Do you have pagination for the tasks endpoint?
3. Should I handle errors differently for different endpoints?

**Timeline:** Need responses by 2 PM today
**Priority:** High
```

#### Backend Specialist Response
```markdown
@frontend-specialist
Here are the API endpoint details:

**GET /api/farms/{id}/stats/**
```json
{
  "farm": {
    "id": 1,
    "name": "Test Farm",
    "location": "Test Location",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "houses": [
    {
      "id": 1,
      "name": "House 1",
      "capacity": 500,
      "current_population": 450
    }
  ],
  "tasks": [
    {
      "id": 1,
      "title": "Feed chickens",
      "due_date": "2024-01-15T10:00:00Z",
      "completed": false
    }
  ],
  "stats": {
    "total_houses": 5,
    "total_capacity": 1000,
    "current_population": 750,
    "population_trend": [750, 800, 720, 780, 750]
  }
}
```

**Pagination:** Yes, tasks endpoint supports ?page=1&page_size=10
**Error Handling:** All endpoints return standard HTTP status codes

**Timeline:** Endpoints ready by 1 PM today
**Priority:** High
```

## 🔄 Daily Workflow

### Morning Standup
```bash
# Check agent status
cat .cursor/agent-coordination/status.md

# Review overnight changes
git log --oneline --since="yesterday"

# Check for conflicts
git status
```

### During Development
```bash
# Monitor agent activity
./.cursor/agent-coordination/monitor-agents.sh

# Check code quality
./scripts/lint-check.sh

# Run tests
cd frontend && npm test
cd backend && python manage.py test
```

### End of Day
```bash
# Update agent status
echo "## End of Day Status
- [x] Frontend Specialist: FarmDashboard component completed
- [x] Backend Specialist: API endpoints implemented
- [x] Database Specialist: Indexes added
- [x] Testing Specialist: Tests written
- [ ] UI/UX Specialist: Design review pending
- [ ] Security Specialist: Security review pending
" > .cursor/agent-coordination/status.md

# Commit changes
git add .
git commit -m "feat: add farm dashboard with statistics API"
git push origin feature/farm-dashboard
```

## 🎯 Best Practices for Agent Interaction

### 1. Clear Communication
- Use specific, actionable messages
- Include context and requirements
- Set clear timelines and priorities
- Ask questions when uncertain

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

This workflow ensures efficient parallel development while maintaining code quality and coordination between agents.
