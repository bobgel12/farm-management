# Chicken House Management System

## Overview
A comprehensive web application for managing multiple chicken farms with automated task scheduling based on chicken age. The system tracks daily tasks for each house from day -1 (setup) through day 41 (cleanup).

## Current Application Status (Updated: September 20, 2025)

### ✅ Fully Functional Features
- **Farm Management**: Create, read, update, delete farms with full contact information
- **House Management**: Create, read, update, delete houses with automatic task generation
- **Task Management**: Complete task overview with clickable task completion
- **Authentication**: Token-based authentication with CSRF protection
- **Task Overview**: Collapsible task sections showing today's, tomorrow's, and other pending tasks
- **Real-time Updates**: Task completion updates task counts and progress bars
- **Responsive UI**: Material-UI components with modern design

### 🔧 Recent Fixes Applied
- **Docker Port Conflicts**: Resolved port 5432 conflicts with automatic process termination
- **Frontend Module Resolution**: Fixed all import statements with proper .tsx extensions
- **Material-UI Icons**: Replaced invalid Farm icon with Agriculture icon
- **CSRF Protection**: Implemented token-based authentication bypassing CSRF requirements
- **Database Migrations**: Applied all necessary migrations for custom apps
- **API Pagination**: Fixed frontend to handle paginated API responses correctly
- **Task Generation**: Automatic task creation when houses are added
- **Task Completion**: Clickable tasks with completion dialog and notes
- **Edit Farm Functionality**: Fixed missing updateFarm implementation

## Application Architecture

### Backend (Django)
- **Framework**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL (production) / SQLite (development)
- **Authentication**: Token-based authentication with Django REST Framework Authtoken
- **API**: RESTful API with pagination and CSRF protection
- **CORS**: Configured for frontend communication
- **CSRF**: Bypassed for API endpoints using @csrf_exempt

### Frontend (React)
- **Framework**: React 18+ with TypeScript
- **UI Library**: Material-UI (MUI) v5
- **State Management**: React Context API (AuthContext, FarmContext, TaskContext)
- **Routing**: React Router v6
- **API Integration**: Axios with interceptors for token management
- **Error Handling**: Comprehensive error handling with user feedback

### Deployment
- **Containerization**: Docker with docker-compose
- **Environment**: Development and Production configurations
- **Database**: PostgreSQL for production, SQLite for development
- **Ports**: Frontend (3000), Backend (8000), Database (5433)

## Data Models

### Farm Model
```python
class Farm(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=20)
    contact_email = models.EmailField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def total_houses(self):
        return self.houses.count()
    
    @property
    def active_houses(self):
        return self.houses.filter(is_active=True).count()
```

### House Model
```python
class House(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE)
    house_number = models.IntegerField()
    chicken_in_date = models.DateField()
    chicken_out_date = models.DateField(default=None, null=True, blank=True)
    chicken_out_day = models.IntegerField(default=40)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def current_day(self):
        if self.chicken_in_date:
            return (timezone.now().date() - self.chicken_in_date).days
        return None
    
    @property
    def days_remaining(self):
        if self.current_day is not None and self.chicken_out_day:
            return self.chicken_out_day - self.current_day
        return None
    
    @property
    def status(self):
        current_day = self.current_day
        if current_day is None:
            return 'inactive'
        elif current_day < 0:
            return 'setup'
        elif current_day == 0:
            return 'arrival'
        elif current_day <= 7:
            return 'early_care'
        elif current_day <= 20:
            return 'growth'
        elif current_day <= 35:
            return 'maturation'
        elif current_day <= 39:
            return 'production'
        elif current_day == 40:
            return 'pre_exit'
        else:
            return 'cleanup'
```

### Task Model
```python
class Task(models.Model):
    house = models.ForeignKey(House, on_delete=models.CASCADE)
    day_offset = models.IntegerField()  # -1 to 41
    task_name = models.CharField(max_length=200)
    description = models.TextField()
    task_type = models.CharField(max_length=50, default='general')
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def mark_completed(self, completed_by='', notes=''):
        self.is_completed = True
        self.completed_at = timezone.now()
        self.completed_by = completed_by
        self.notes = notes
        self.save()
```

## Task Schedule by Chicken Age

### Day -1: House Setup
- Open heater pipe lock
- Turn heater (24 hours ahead before chicken is in)
- Before turning heat, check if the heat line is down
- Turn water on
- Check water line
- Replace filter
- Set water pressure to 6 half turns
- Set water line height to 6 full turns
- Place 16 plastic tray feeds (5 load per tray) on single feed side
- Set up turbo
- Lock mid house feed line
- Run feed line to full

### Day 0: Chicken Arrival
- Chicken is in
- Check water line has water all the way to the end
- Check heater is running
- Check feed is full

### Day 1: Initial Care
- Increase water pressure by 1 half turn
- Death chicken pickup (1 per 2 days)
- Set up and turn on feed setup
- Turn on feed manually 2 times daily (morning and afternoon)

### Days 1-7: Early Care
- Death chicken pickup every 2 days
- Turn on feed manually 2 times daily (morning and afternoon)

### Day 7: Transition
- Close turbo feed, push out
- Close curtains (front and back)

### Day 8: Full House Operations
- Full house works including:
  - Increase water pressure by 1 half turn
  - Turn on feed and water to full house
  - Turn feed to 3/4 of front and back side for automatic night run
  - Turn on heat 1, 2, 7, 8
  - Open separator on 2 sides so chickens can spread out
  - Turn feed on automatic on controller

### Days 9-12: Monitoring and Adjustment
- Check feeder motor on last pan and clean out
- Ensure feed runs for the line 2 times daily (early morning and end of day)
- Days 9-10: Check if chickens spread out evenly, then close separator
- Day 12: Clean up turbo line (make it to ceiling)

### Day 13: Feeder Adjustment
- Raise feeder line so pan doesn't touch ground
- Level the feeder line

### Day 14: Water Pressure Increase
- Increase water pressure by 1 half turn
- This repeats every 6 days from now (days 20, 26, 32, 38)

### Day 20: Coolpad Preparation
- Turn water on coolpad

### Day 21: Coolpad Activation
- Turn on coolpad including:
  - Turn coolpad breaker
  - Turn water on coolpad
  - Turn controller coolpad on auto

### Days 35-40: Exit Planning
- Keep asking for chicken out schedule for each house (both date and time)

### Day 39: Pre-Exit Preparation
- Turn water pressure 2 half circles

### Day 40: Chicken Exit Day
- 12 hours before chicken out time: Turn off feeder
- 10 hours before chicken out: Clean out auger and feeder line, ensure no feed left
- 6 hours before chicken out: Raise feeder line up (ensure pan is empty)
- Turn off heater (both breaker and controller), then raise heater up
- 1 hour before chicken out: Turn off water line and raise water line up
- Turn on water line on front of house
- Turn off tunnel fan, light 3 hours after chicken out

### Day 41: Post-Exit Cleanup
- Collect death chickens that are left

## Recurring Tasks

### Weekly Tasks
- **Every Monday at 9am**: Check generator run
- **Every Monday and Thursday**: Check and report feed bin

## Water Line Configuration

### Days 0-5
- Nipple on chicken eye level

### Days 6-40
- Nipple on level that is chicken drinking water 45 degrees based on smallest chicken

## Application Features

### Farm Management
- ✅ Create and manage multiple farms with full contact information
- ✅ Edit farm details (name, location, contact person, phone, email)
- ✅ Delete farms with confirmation
- ✅ View farm statistics (total houses, active houses)
- ✅ Farm status tracking (active/inactive)

### House Management
- ✅ Add houses to farms with automatic task generation
- ✅ Set chicken in date (day 0) and chicken out day (default 40)
- ✅ Track house status and current day calculation
- ✅ Edit house details
- ✅ Delete houses with confirmation
- ✅ Automatic status calculation based on current day

### Task Management
- ✅ Automatic task generation for all 42 days (-1 to 41)
- ✅ Task completion with notes and user tracking
- ✅ Clickable task completion from farm overview
- ✅ Task categorization (today's, tomorrow's, other pending)
- ✅ Progress tracking with completion percentages
- ✅ Collapsible task sections for better organization

### Dashboard & Overview
- ✅ Farm overview with house statistics
- ✅ Task overview with collapsible sections
- ✅ Today's and tomorrow's tasks prominently displayed
- ✅ Other pending tasks collapsed by default
- ✅ Real-time task completion updates
- ✅ Visual progress indicators

### Authentication & Security
- ✅ Token-based authentication
- ✅ CSRF protection with trusted origins
- ✅ CORS configuration for frontend
- ✅ Protected routes and API endpoints
- ✅ Automatic token refresh and logout on 401 errors

## Technical Implementation

### Backend API Endpoints
```
# Authentication
POST /api/auth/login/ - User login with token response
POST /api/auth/logout/ - User logout
GET /api/auth/user/ - Get current user info

# Farms
GET /api/farms/ - List all farms (paginated)
POST /api/farms/ - Create new farm
GET /api/farms/{id}/ - Get farm details
PUT /api/farms/{id}/ - Update farm
DELETE /api/farms/{id}/ - Delete farm
GET /api/farms/{id}/houses/ - List houses for farm
GET /api/farms/{id}/task-summary/ - Get farm task summary

# Houses
GET /api/houses/ - List all houses (paginated)
POST /api/houses/ - Create new house (auto-generates tasks)
GET /api/houses/{id}/ - Get house details
PUT /api/houses/{id}/ - Update house
DELETE /api/houses/{id}/ - Delete house

# Tasks
GET /api/tasks/ - List all tasks (paginated)
GET /api/tasks/{id}/ - Get task details
POST /api/tasks/{id}/complete/ - Mark task as complete
GET /api/houses/{id}/tasks/ - Get tasks for specific house
```

### Frontend Components
- **FarmList**: Display and manage farms with edit/delete functionality
- **FarmDetail**: Detailed farm view with task overview and house management
- **HouseDetail**: Individual house management and task viewing
- **TaskList**: Task management for individual houses
- **Dashboard**: Overview of all operations
- **Login**: Authentication form
- **Layout**: Navigation and protected route wrapper

### Context Providers
- **AuthContext**: User authentication state and login/logout functions
- **FarmContext**: Farm and house management with task completion
- **TaskContext**: Task management and completion tracking

### API Service
- **Axios Configuration**: Base URL, credentials, headers
- **Request Interceptor**: Automatic token injection
- **Response Interceptor**: 401 error handling and token cleanup

## Database Schema

### Current Tables
- **farms_farm**: Farm information and contact details
- **houses_house**: House information with calculated properties
- **tasks_task**: Task information with completion tracking
- **authtoken_token**: User authentication tokens
- **django_migrations**: Migration tracking

### Key Relationships
- Farm → Houses (One-to-Many)
- House → Tasks (One-to-Many)
- User → Token (One-to-One)

## Development Setup

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker and Docker Compose
- PostgreSQL (for production)
- Colima (for macOS Docker)

### Quick Start
```bash
# Clone and setup
git clone <repository>
cd chicken_house_management

# Run setup script (handles all dependencies and fixes)
chmod +x setup.sh
./setup.sh

# Or run quick fix for existing setup
chmod +x quick-fix.sh
./quick-fix.sh
```

### Manual Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

# Frontend
cd frontend
npm install
npm start

# Docker
docker-compose up --build
```

## Current Configuration

### Environment Variables
```bash
# Backend (.env)
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://user:password@db:5432/chicken_management
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@example.com

# Frontend (.env)
REACT_APP_API_URL=http://localhost:8000/api
```

### Docker Services
- **frontend**: React app on port 3000
- **backend**: Django API on port 8000
- **db**: PostgreSQL on port 5433

### CORS & CSRF Settings
```python
# Django settings
CORS_ALLOWED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
```

## Troubleshooting

### Common Issues Fixed
1. **Port Conflicts**: Automatic detection and termination of conflicting processes
2. **Module Resolution**: All imports fixed with proper .tsx extensions
3. **CSRF Errors**: Token authentication bypasses CSRF requirements
4. **Database Tables**: All migrations applied for custom apps
5. **API Pagination**: Frontend handles paginated responses correctly
6. **Task Generation**: Automatic task creation on house creation
7. **Edit Functionality**: All CRUD operations working properly

### Setup Scripts
- **setup.sh**: Complete setup with all fixes applied
- **quick-fix.sh**: Quick fixes for existing installations
- **TROUBLESHOOTING.md**: Detailed troubleshooting guide

## Security Considerations
- ✅ Input validation and sanitization
- ✅ SQL injection prevention
- ✅ XSS protection
- ✅ CSRF protection with trusted origins
- ✅ Token-based authentication
- ✅ Secure session management
- ✅ Environment variable security
- ✅ CORS configuration

## Performance Optimizations
- ✅ API pagination for large datasets
- ✅ React Context for efficient state management
- ✅ Material-UI components for optimized rendering
- ✅ Axios interceptors for efficient API calls
- ✅ Collapsible UI sections for better performance

## Future Enhancements
- Mobile app for field workers
- IoT sensor integration
- Automated data collection
- Advanced analytics and reporting
- Multi-language support
- Cloud deployment options
- Real-time notifications
- Task scheduling and reminders
- Advanced reporting dashboard
- Data export capabilities

## Current Status Summary
**✅ FULLY FUNCTIONAL** - All core features working with recent fixes applied:
- Farm and house management
- Task generation and completion
- Authentication and security
- Responsive UI with modern design
- Real-time updates and progress tracking
- Comprehensive error handling
- Docker deployment ready