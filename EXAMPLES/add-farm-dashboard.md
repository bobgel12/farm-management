# Example: Adding Farm Dashboard Feature

This example shows how to use the multi-agent system to add a new Farm Dashboard feature to your application.

## 🚀 Step-by-Step Process

### Step 1: Initialize the Feature
```bash
# Run the agent interaction script
./scripts/agent-interaction.sh

# Select option 1: Start new feature
# Enter feature name: farm-dashboard
# Enter feature description: Add a comprehensive dashboard for farm management with statistics, house overview, and task management
```

### Step 2: Coordinate with Agents

#### Frontend Specialist Task
```markdown
@frontend-specialist
I need to create a Farm Dashboard component with the following requirements:

**Requirements:**
- Display farm statistics (total houses, capacity, population)
- Show recent tasks for the farm
- Display house status overview
- Include charts for population trends
- Responsive design for mobile and desktop

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

#### Backend Specialist Task
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

## 🛠️ Implementation Examples

### Frontend Implementation (Frontend Specialist)
```typescript
// File: frontend/src/components/FarmDashboard.tsx
import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Alert
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
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
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchFarmData = async () => {
      try {
        setLoading(true);
        setError(null);

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
        setError('Failed to load farm data');
      } finally {
        setLoading(false);
      }
    };

    fetchFarmData();
  }, [farmId]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  const chartData = stats?.population_trend.map((value, index) => ({
    day: `Day ${index + 1}`,
    population: value
  })) || [];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        {farm?.name} Dashboard
      </Typography>
      
      <Grid container spacing={3}>
        {/* Statistics Cards */}
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">Total Houses</Typography>
              <Typography variant="h3">{stats?.total_houses || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">Total Capacity</Typography>
              <Typography variant="h3">{stats?.total_capacity || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">Current Population</Typography>
              <Typography variant="h3">{stats?.current_population || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" color="primary">Utilization</Typography>
              <Typography variant="h3">
                {stats ? Math.round((stats.current_population / stats.total_capacity) * 100) : 0}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Population Trend Chart */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Population Trend</Typography>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="population" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Tasks */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Recent Tasks</Typography>
              {tasks.slice(0, 5).map((task) => (
                <Box key={task.id} sx={{ mb: 1, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
                  <Typography variant="body2" fontWeight="bold">
                    {task.title}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Due: {new Date(task.due_date).toLocaleDateString()}
                  </Typography>
                  <Typography 
                    variant="caption" 
                    color={task.completed ? 'success.main' : 'warning.main'}
                    sx={{ ml: 1 }}
                  >
                    {task.completed ? 'Completed' : 'Pending'}
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Houses Overview */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Houses Overview</Typography>
              <Grid container spacing={2}>
                {houses.map((house) => (
                  <Grid item xs={12} sm={6} md={4} key={house.id}>
                    <Card variant="outlined">
                      <CardContent>
                        <Typography variant="h6">{house.name}</Typography>
                        <Typography variant="body2" color="text.secondary">
                          Capacity: {house.capacity}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Population: {house.current_population}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Utilization: {Math.round((house.current_population / house.capacity) * 100)}%
                        </Typography>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default FarmDashboard;
```

### Backend Implementation (Backend Specialist)
```python
# File: backend/farms/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
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
        return House.objects.filter(farm_id=farm_id).order_by('name')

@api_view(['GET'])
def farm_stats(request, farm_id):
    """Get comprehensive farm statistics"""
    try:
        farm = Farm.objects.get(id=farm_id)
        houses = House.objects.filter(farm_id=farm_id)
        tasks = Task.objects.filter(farm_id=farm_id).order_by('-created_at')[:10]
        
        # Calculate statistics
        total_houses = houses.count()
        total_capacity = houses.aggregate(Sum('capacity'))['capacity__sum'] or 0
        current_population = houses.aggregate(Sum('current_population'))['current_population__sum'] or 0
        
        # Calculate population trend (last 7 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        
        # Mock population trend data (in real app, you'd query historical data)
        population_trend = [750, 800, 720, 780, 750, 760, 740]
        
        stats = {
            'total_houses': total_houses,
            'total_capacity': total_capacity,
            'current_population': current_population,
            'population_trend': population_trend,
            'utilization_rate': round((current_population / total_capacity) * 100, 2) if total_capacity > 0 else 0,
            'average_house_capacity': round(houses.aggregate(Avg('capacity'))['capacity__avg'] or 0, 2),
            'average_house_population': round(houses.aggregate(Avg('current_population'))['current_population__avg'] or 0, 2)
        }
        
        return Response({
            'farm': FarmSerializer(farm).data,
            'houses': HouseSerializer(houses, many=True).data,
            'tasks': TaskSerializer(tasks, many=True).data,
            'stats': stats
        })
    except Farm.DoesNotExist:
        return Response({'error': 'Farm not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### Database Optimization (Database Specialist)
```python
# File: backend/farms/migrations/0003_add_farm_stats_indexes.py
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
        migrations.AddIndex(
            model_name='house',
            index=models.Index(fields=['farm', 'name'], name='farms_house_farm_name_idx'),
        ),
    ]
```

### Testing Implementation (Testing Specialist)
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

const mockFarmData = {
  farm: {
    id: 1,
    name: 'Test Farm',
    location: 'Test Location',
    created_at: '2024-01-01T00:00:00Z'
  },
  houses: [
    {
      id: 1,
      name: 'House 1',
      capacity: 500,
      current_population: 450,
      farm: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
  ],
  tasks: [
    {
      id: 1,
      title: 'Feed chickens',
      description: 'Morning feeding',
      due_date: '2024-01-15T10:00:00Z',
      completed: false,
      priority: 'high',
      farm: 1,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z'
    }
  ],
  stats: {
    total_houses: 1,
    total_capacity: 500,
    current_population: 450,
    population_trend: [450, 460, 440, 470, 450, 460, 450]
  }
};

describe('FarmDashboard', () => {
  beforeEach(() => {
    mockedApi.get.mockImplementation((url) => {
      if (url.includes('/stats/')) {
        return Promise.resolve({ data: mockFarmData });
      }
      return Promise.resolve({ data: mockFarmData[url.split('/').pop()] || [] });
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
      expect(screen.getByText('1')).toBeInTheDocument(); // Total houses
      expect(screen.getByText('500')).toBeInTheDocument(); // Total capacity
      expect(screen.getByText('450')).toBeInTheDocument(); // Current population
    });
  });

  it('displays loading state initially', () => {
    render(
      <BrowserRouter>
        <FarmDashboard farmId={1} />
      </BrowserRouter>
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  it('handles error state', async () => {
    mockedApi.get.mockRejectedValue(new Error('API Error'));

    render(
      <BrowserRouter>
        <FarmDashboard farmId={1} />
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load farm data')).toBeInTheDocument();
    });
  });
});
```

## 🔄 Agent Coordination During Development

### Daily Standup
```bash
# Check agent status
cat .cursor/agent-coordination/status.md

# Review progress
git log --oneline --since="yesterday"

# Check for conflicts
git status
```

### Agent Communication
```markdown
@frontend-specialist @backend-specialist
I've completed the FarmDashboard component and need the API endpoints.

**Current Status:**
- ✅ FarmDashboard component created
- ✅ UI layout implemented
- ✅ Error handling added
- ✅ Loading states implemented
- ⏳ Waiting for API endpoints

**Questions:**
1. What's the exact response format for /api/farms/{id}/stats/?
2. Do you have pagination for the tasks endpoint?
3. Should I handle errors differently for different endpoints?

**Timeline:** Need responses by 2 PM today
**Priority:** High
```

### Progress Monitoring
```bash
# Monitor agent activity
./.cursor/agent-coordination/monitor-agents.sh

# Check code quality
./scripts/lint-check.sh

# Run tests
cd frontend && npm test
cd backend && python manage.py test
```

## 🎯 Success Metrics

### Code Quality
- ✅ TypeScript strict mode enabled
- ✅ ESLint passing with no errors
- ✅ Prettier formatting applied
- ✅ Test coverage > 80%

### Performance
- ✅ Component loads in < 2 seconds
- ✅ API responses < 500ms
- ✅ Bundle size optimized
- ✅ Mobile responsive

### Security
- ✅ Input validation implemented
- ✅ Error handling secure
- ✅ API authentication required
- ✅ XSS protection enabled

This example shows how the multi-agent system enables parallel development while maintaining coordination and quality standards.
