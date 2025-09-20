# Production Deployment Guide

## Free Hosting Options

### 1. Railway (Recommended) - Free Tier Available
- **Free Tier**: $5 credit monthly, 500 hours runtime
- **Features**: PostgreSQL, Redis, automatic deployments
- **Best For**: Full-stack applications with database

### 2. Render - Free Tier Available
- **Free Tier**: 750 hours/month, sleeps after 15min inactivity
- **Features**: PostgreSQL, automatic deployments
- **Best For**: Simple deployments with database

### 3. Heroku - Limited Free Tier
- **Free Tier**: 550-1000 dyno hours/month
- **Features**: PostgreSQL addon, easy deployment
- **Best For**: Quick deployments (note: Heroku removed free tier in 2022)

### 4. Vercel + Supabase (Recommended for Frontend)
- **Free Tier**: Unlimited static hosting + free PostgreSQL
- **Features**: Serverless functions, edge deployment
- **Best For**: Frontend + API with external database

## Railway Deployment (Recommended)

### Prerequisites
- GitHub account
- Railway account (free at railway.app)
- Domain name (optional, free subdomain provided)

### Step 1: Prepare Repository
```bash
# Ensure all files are committed
git add .
git commit -m "Prepare for production deployment"
git push origin main
```

### Step 2: Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect the Docker setup

### Step 3: Configure Environment Variables
In Railway dashboard, go to Variables tab and add:

```bash
# Database (Railway will provide this)
DATABASE_URL=postgresql://postgres:password@host:port/database

# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,localhost

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=admin@yourdomain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Step 4: Add PostgreSQL Database
1. In Railway dashboard, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically set `DATABASE_URL`
3. Wait for database to be ready

### Step 5: Deploy
Railway will automatically deploy when you push to main branch.

## Render Deployment

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub

### Step 2: Create Web Service
1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Build Command**: `cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && python manage.py migrate && python manage.py runserver 0.0.0.0:$PORT`
   - **Environment**: Python 3

### Step 3: Add PostgreSQL Database
1. Click "New" → "PostgreSQL"
2. Copy the database URL
3. Add to environment variables

### Step 4: Configure Environment Variables
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com
# ... other variables
```

## Vercel + Supabase Deployment

### Step 1: Deploy Frontend to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Import your GitHub repository
3. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

### Step 2: Set Up Supabase Database
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Get connection string
4. Run migrations in Supabase SQL editor

### Step 3: Deploy Backend API
1. Create `api` folder in root
2. Add Vercel serverless functions
3. Deploy backend as API routes

## Production Configuration Files

### Railway Configuration
```yaml
# railway.json
{
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "cd backend && python manage.py migrate && python manage.py runserver 0.0.0.0:$PORT",
    "healthcheckPath": "/api/",
    "healthcheckTimeout": 100
  }
}
```

### Dockerfile for Production
```dockerfile
# Dockerfile
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ .

# Copy frontend build
COPY --from=frontend-build /app/frontend/build ./static/

# Create logs directory
RUN mkdir -p logs

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "manage.py", "migrate", "&&", "python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### Production Settings
```python
# backend/chicken_management/settings_prod.py
import os
from .settings import *

DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Database
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL)
    }

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@chickenmanagement.com')
```

## Deployment Scripts

### Railway Deployment Script
```bash
#!/bin/bash
# deploy_railway.sh

echo "🚀 Deploying to Railway..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway
railway login

# Link to project
railway link

# Deploy
railway up

echo "✅ Deployment complete!"
echo "🌐 Your app is available at: https://your-app.railway.app"
```

### Render Deployment Script
```bash
#!/bin/bash
# deploy_render.sh

echo "🚀 Deploying to Render..."

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo "Installing Render CLI..."
    curl -fsSL https://cli.render.com/install | sh
fi

# Deploy
render deploy

echo "✅ Deployment complete!"
echo "🌐 Your app is available at: https://your-app.onrender.com"
```

## Post-Deployment Setup

### 1. Run Database Migrations
```bash
# Railway
railway run python manage.py migrate

# Render
render run python manage.py migrate
```

### 2. Create Superuser
```bash
# Railway
railway run python manage.py createsuperuser

# Render
render run python manage.py createsuperuser
```

### 3. Set Up Daily Email Cron
```bash
# Railway - Use Railway Cron
# Add to railway.json:
{
  "cron": {
    "daily-tasks": {
      "schedule": "0 21 * * *",
      "command": "python manage.py send_daily_tasks"
    }
  }
}

# Render - Use external cron service like cron-job.org
# Set up cron job to hit: https://your-app.onrender.com/api/tasks/send-daily-tasks/
```

### 4. Configure Custom Domain (Optional)
1. **Railway**: Go to Settings → Domains
2. **Render**: Go to Settings → Custom Domains
3. **Vercel**: Go to Settings → Domains

## Monitoring and Maintenance

### Health Checks
```python
# backend/health/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
```

### Logging Configuration
```python
# backend/chicken_management/settings_prod.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

## Cost Comparison

| Service | Free Tier | Database | Email | Cron | Custom Domain |
|---------|-----------|----------|-------|------|---------------|
| Railway | $5 credit/month | ✅ | ✅ | ✅ | ✅ |
| Render | 750 hours/month | ✅ | ✅ | ❌ | ✅ |
| Vercel + Supabase | Unlimited | ✅ | ✅ | ✅ | ✅ |
| Heroku | $5-7/month | ✅ | ✅ | ✅ | ✅ |

## Troubleshooting

### Common Issues
1. **Database Connection**: Check DATABASE_URL format
2. **Static Files**: Ensure collectstatic runs
3. **Email**: Verify SMTP credentials
4. **CORS**: Update ALLOWED_HOSTS
5. **Memory**: Monitor resource usage

### Debug Commands
```bash
# Check logs
railway logs
render logs

# Run shell
railway run python manage.py shell
render run python manage.py shell

# Check environment
railway run env
render run env
```

## Security Checklist

- [ ] Change default admin password
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Configure CORS properly
- [ ] Use environment variables for secrets
- [ ] Enable database backups
- [ ] Monitor access logs
- [ ] Regular security updates

## Backup Strategy

### Database Backups
```bash
# Railway
railway run pg_dump $DATABASE_URL > backup.sql

# Render
render run pg_dump $DATABASE_URL > backup.sql
```

### Automated Backups
Set up daily backups using:
- Railway: Built-in backup service
- Render: External backup service
- Supabase: Automatic backups included

---

**🎉 Your Chicken House Management System is now ready for production deployment! Choose your preferred hosting service and follow the deployment guide.**
