# Manual Railway Deployment Guide

## Step-by-Step Railway Deployment

### Step 1: Prepare Your Code
```bash
# Make sure all changes are committed
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

### Step 2: Set Up Railway Project

#### Option A: Via Railway Dashboard
1. Go to [railway.app](https://railway.app)
2. Sign up/Login with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway will auto-detect the setup

#### Option B: Via CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init

# Link to existing project (if you have one)
railway link
```

### Step 3: Add PostgreSQL Database
1. In Railway dashboard, click "New"
2. Select "Database" → "PostgreSQL"
3. Wait for database to be ready
4. Copy the `DATABASE_URL` from the database service

### Step 4: Configure Environment Variables
In Railway dashboard, go to your service → Variables tab and add:

```bash
# Required
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://postgres:password@host:port/database
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,localhost

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=admin@example.com

# Email (Gmail example)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com

# Django Settings
DJANGO_SETTINGS_MODULE=chicken_management.settings_prod
```

### Step 5: Configure Build Settings
In Railway dashboard, go to your service → Settings:

#### Build Command:
```bash
cd frontend && npm ci && npm run build && cd .. && cd backend && pip install -r requirements.txt
```

#### Start Command:
```bash
cd backend && python manage.py migrate && python manage.py runserver 0.0.0.0:$PORT
```

#### Health Check Path:
```
/api/health/
```

### Step 6: Deploy
1. Railway will automatically deploy when you push to main
2. Or click "Deploy" in the dashboard
3. Wait for deployment to complete

### Step 7: Post-Deployment Setup

#### Run Database Migrations:
```bash
railway run python manage.py migrate
```

#### Create Superuser:
```bash
railway run python manage.py createsuperuser
```

#### Test Your Deployment:
```bash
# Health check
curl https://your-app.railway.app/api/health/

# Test API
curl https://your-app.railway.app/api/farms/
```

### Step 8: Set Up Daily Email Cron
1. In Railway dashboard, go to your service
2. Click "Cron" tab
3. Add new cron job:
   - **Name**: daily-tasks
   - **Schedule**: `0 21 * * *` (9pm daily)
   - **Command**: `cd backend && python manage.py send_daily_tasks`

## Troubleshooting

### If Build Fails
1. **Check build logs** in Railway dashboard
2. **Try simpler build command**:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. **Check Node.js version** (Railway uses Node 18 by default)

### If App Won't Start
1. **Check environment variables** are set correctly
2. **Verify DATABASE_URL** format
3. **Check start command** is correct
4. **Look at logs** for error messages

### If Database Issues
1. **Verify PostgreSQL service** is running
2. **Check DATABASE_URL** is correct
3. **Run migrations** manually
4. **Test database connection**

### If Email Not Working
1. **Verify SMTP credentials**
2. **Check Gmail app password** is correct
3. **Test email** with a simple command
4. **Check email environment variables**

## Alternative: Render Deployment

If Railway continues to have issues, try Render instead:

### Quick Render Setup
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Create "Web Service"
4. Connect your repository
5. Configure:
   - **Build Command**: `cd frontend && npm ci && npm run build && cd .. && cd backend && pip install -r requirements.txt`
   - **Start Command**: `cd backend && python manage.py migrate && python manage.py runserver 0.0.0.0:$PORT`
6. Add PostgreSQL database
7. Set environment variables
8. Deploy

## Success Checklist

- [ ] App builds successfully
- [ ] App starts without errors
- [ ] Database migrations run
- [ ] Health check passes (`/api/health/`)
- [ ] Admin panel accessible (`/admin/`)
- [ ] API endpoints working (`/api/farms/`)
- [ ] Email configuration working
- [ ] Daily email cron job set up
- [ ] Custom domain configured (optional)

## Getting Help

1. **Railway Dashboard**: Check logs and status
2. **Railway Docs**: https://docs.railway.app
3. **Railway Discord**: https://discord.gg/railway
4. **Project Issues**: Check GitHub repository

---

**🎉 Once all steps are completed, your Chicken House Management System will be live on Railway!**
