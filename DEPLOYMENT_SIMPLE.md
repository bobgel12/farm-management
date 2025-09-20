# 🚀 Simple Production Deployment Guide

## Overview

This application uses a **simplified deployment strategy**:
- **Backend**: Railway (Django + PostgreSQL)
- **Frontend**: Vercel (React)

## Prerequisites

- GitHub account
- Railway account (free at [railway.app](https://railway.app))
- Vercel account (free at [vercel.com](https://vercel.com))

## 🎯 Step 1: Deploy Backend to Railway

### 1.1 Install Railway CLI
```bash
npm install -g @railway/cli
```

### 1.2 Login to Railway
```bash
railway login
```

### 1.3 Deploy Backend
```bash
# From project root
./deploy_railway.sh
```

### 1.4 Configure Environment Variables
In Railway dashboard, add these variables:

```bash
# Required
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://postgres:password@host:port/database
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Optional
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 1.5 Add PostgreSQL Database
1. In Railway dashboard, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically set `DATABASE_URL`

### 1.6 Run Database Setup
```bash
# Run migrations
railway run python manage.py migrate

# Create admin user
railway run python manage.py createsuperuser
```

## 🎯 Step 2: Deploy Frontend to Vercel

### 2.1 Go to Vercel
1. Visit [vercel.com](https://vercel.com)
2. Sign in with GitHub

### 2.2 Import Project
1. Click "New Project"
2. Select your GitHub repository
3. Set **Root Directory** to `frontend/`
4. Click "Deploy"

### 2.3 Configure Environment Variables
In Vercel dashboard, add:
```bash
REACT_APP_API_URL=https://your-backend.railway.app/api
```

### 2.4 Update Backend CORS
In Railway dashboard, add your Vercel URL to CORS settings:
```bash
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-app.vercel.app
```

## 🎯 Step 3: Test Your Deployment

### 3.1 Test Backend
```bash
# Health check
curl https://your-backend.railway.app/api/health/

# Test API
curl https://your-backend.railway.app/api/farms/
```

### 3.2 Test Frontend
1. Visit your Vercel URL
2. Try logging in with admin credentials
3. Test creating a farm and house

## 🎯 Step 4: Configure Email (Optional)

### 4.1 Gmail Setup
1. Enable 2-factor authentication
2. Generate app password
3. Use app password in `EMAIL_HOST_PASSWORD`

### 4.2 Test Email
```bash
# Test email functionality
railway run python manage.py shell -c "
from tasks.email_service import EmailService
EmailService.send_test_email('your-email@example.com')
"
```

## 🔧 Troubleshooting

### Common Issues

**Backend Issues:**
```bash
# Check logs
railway logs

# Check environment
railway run env

# Restart service
railway restart
```

**Frontend Issues:**
- Check Vercel deployment logs
- Verify `REACT_APP_API_URL` is set correctly
- Check browser console for errors

**CORS Issues:**
- Ensure Vercel URL is in `CORS_ALLOWED_ORIGINS`
- Check `CSRF_TRUSTED_ORIGINS` includes Vercel URL

### Database Issues
```bash
# Reset database
railway run python manage.py flush

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser
```

## 📊 Monitoring

### Health Checks
- **Backend**: `https://your-backend.railway.app/api/health/`
- **Frontend**: Vercel automatically monitors

### Logs
- **Backend**: `railway logs`
- **Frontend**: Vercel dashboard

## 💰 Cost

- **Railway**: Free tier ($5 credit/month)
- **Vercel**: Free tier (unlimited personal projects)
- **Total**: $0/month for personal use

## 🎉 Success!

Your Chicken House Management System is now live!

**URLs:**
- Frontend: `https://your-app.vercel.app`
- Backend API: `https://your-backend.railway.app/api`
- Admin Panel: `https://your-backend.railway.app/admin`

**Next Steps:**
1. Add your farm data
2. Set up workers
3. Configure daily emails
4. Start managing your chicken houses!
