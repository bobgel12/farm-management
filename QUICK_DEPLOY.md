# Quick Deploy Guide

## 🚀 Deploy in 5 Minutes

### Option 1: Railway (Recommended)
```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login to Railway
railway login

# 3. Deploy
./deploy_railway.sh
```

### Option 2: Render
```bash
# 1. Install Render CLI
curl -fsSL https://cli.render.com/install | sh

# 2. Login to Render
render auth login

# 3. Deploy
./deploy_render.sh
```

## 📋 Pre-Deployment Checklist

- [ ] Push code to GitHub
- [ ] Set up email credentials (Gmail app password)
- [ ] Choose deployment platform
- [ ] Run deployment script

## ⚙️ Post-Deployment Setup

### 1. Configure Environment Variables
In your hosting platform dashboard, add:
```bash
# Required
SECRET_KEY=your-super-secret-key
DATABASE_URL=postgresql://user:pass@host:port/db
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Optional
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 2. Run Database Migrations
```bash
# Railway
railway run python manage.py migrate

# Render
render run python manage.py migrate
```

### 3. Create Admin User
```bash
# Railway
railway run python manage.py createsuperuser

# Render
render run python manage.py createsuperuser
```

### 4. Test Your Deployment
```bash
# Health check
curl https://your-app.railway.app/api/

# Test email
curl -X POST https://your-app.railway.app/api/tasks/send-test-email/ \
  -H "Content-Type: application/json" \
  -d '{"farm_id": 1, "test_email": "your-email@example.com"}'
```

## 🎯 What You Get

- ✅ **Full-Stack App**: Frontend + Backend + Database
- ✅ **Daily Emails**: Automatic 9pm task reminders
- ✅ **Admin Panel**: Manage farms, houses, workers
- ✅ **API**: RESTful API for all operations
- ✅ **Health Checks**: Monitoring endpoints
- ✅ **SSL**: HTTPS enabled
- ✅ **Cron Jobs**: Automated daily tasks

## 🔧 Troubleshooting

### Common Issues
1. **Build Fails**: Check Python/Node versions
2. **Database Error**: Verify DATABASE_URL format
3. **Email Fails**: Check SMTP credentials
4. **Static Files**: Ensure collectstatic runs

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

## 📊 Monitoring

### Health Endpoints
- `GET /api/health/` - Basic health check
- `GET /api/health/detailed/` - Detailed metrics
- `GET /api/health/ready/` - Readiness probe
- `GET /api/health/alive/` - Liveness probe

### Logs
- Application logs: Platform dashboard
- Email logs: Check Django logs
- Error tracking: Platform error monitoring

## 💰 Cost Breakdown

| Platform | Free Tier | Monthly Cost |
|----------|-----------|--------------|
| Railway | $5 credit | $0-5 |
| Render | 750 hours | $0-7 |
| Vercel + Supabase | Unlimited | $0 |

## 🎉 Success!

Your Chicken House Management System is now live! 

**Next Steps:**
1. Add your farm data
2. Set up workers
3. Configure daily emails
4. Start managing your chicken houses!

**Need Help?** Check `DEPLOYMENT.md` for detailed instructions.
