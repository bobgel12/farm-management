# Railway Email Configuration Guide

## Overview
This guide explains how to configure email settings for the Chicken House Management System on Railway platform.

## Railway-Specific Email Configuration

### 1. Environment Variables in Railway

Set these environment variables in your Railway project dashboard:

#### Required Email Settings
```bash
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Optional: Email debugging
EMAIL_DEBUG=False
```

#### Gmail App Password Setup
1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Click "2-Step Verification" → "App passwords"
   - Select "Mail" and generate password
   - Use this 16-character password as `EMAIL_HOST_PASSWORD`

### 2. Railway Cron Configuration

The `railway.toml` file already includes the daily email cron job:

```toml
[cron.daily-tasks]
schedule = "0 21 * * *"
command = "python manage.py send_daily_tasks"
```

This will automatically send daily task emails at 9 PM UTC every day.

### 3. Railway-Specific Settings Updates

The Django settings are already configured to read from environment variables:

```python
# Email Configuration (already in settings.py)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@chickenmanagement.com')
```

## Step-by-Step Railway Setup

### Step 1: Deploy to Railway
1. Connect your GitHub repository to Railway
2. Railway will automatically detect the `railway.toml` configuration
3. Add PostgreSQL service in Railway dashboard

### Step 2: Configure Environment Variables
In Railway dashboard, go to your project → Variables tab and add:

```bash
# Database (Railway will auto-generate these)
DATABASE_URL=postgresql://postgres:password@localhost:5432/chicken_management

# Django Settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,localhost

# Admin Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-password
ADMIN_EMAIL=admin@yourdomain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Frontend URL
REACT_APP_API_URL=https://your-app.railway.app/api
```

### Step 3: Test Email Configuration

#### Option A: Via Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Connect to your project
railway link

# Test email command
railway run python manage.py send_daily_tasks --test --farm-id 1 --test-email your-email@example.com
```

#### Option B: Via Railway Dashboard
1. Go to your Railway project dashboard
2. Click on "Deployments" → "View Logs"
3. Look for email-related logs

#### Option C: Via Django Admin
1. Access your app: `https://your-app.railway.app/admin/`
2. Login with admin credentials
3. Go to "Farms" → "Workers" and add test workers
4. Go to "Tasks" → "Email Tasks" to see sent emails

### Step 4: Verify Cron Job
1. Check Railway logs for cron job execution
2. Look for "Starting daily task email process..." messages
3. Verify emails are being sent at 9 PM UTC

## Email Provider Options

### Gmail (Recommended)
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Outlook/Hotmail
```bash
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

### SendGrid (Professional)
```bash
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

### Mailgun
```bash
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-mailgun-smtp-username
EMAIL_HOST_PASSWORD=your-mailgun-smtp-password
```

## Troubleshooting

### Common Issues

#### 1. "SMTPAuthenticationError"
- **Cause**: Wrong email credentials
- **Solution**: Verify `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
- **For Gmail**: Use App Password, not regular password

#### 2. "Connection refused"
- **Cause**: Wrong SMTP host/port
- **Solution**: Check `EMAIL_HOST` and `EMAIL_PORT` settings

#### 3. "Cron job not running"
- **Cause**: Railway cron not configured
- **Solution**: Verify `railway.toml` has correct cron configuration

#### 4. "No workers found"
- **Cause**: No workers added to farms
- **Solution**: Add workers via Django admin with `receive_daily_tasks=True`

### Debug Commands

```bash
# Test email configuration
railway run python manage.py shell -c "
from django.core.mail import send_mail
from django.conf import settings
print('Email settings:', {
    'host': settings.EMAIL_HOST,
    'port': settings.EMAIL_PORT,
    'user': settings.EMAIL_HOST_USER,
    'tls': settings.EMAIL_USE_TLS
})
"

# Send test email
railway run python manage.py send_daily_tasks --test --farm-id 1 --test-email your-email@example.com

# Check email logs
railway logs --tail
```

## Monitoring Email Delivery

### 1. Check Email Logs
```bash
railway logs --tail | grep -i email
```

### 2. Monitor Cron Jobs
```bash
railway logs --tail | grep -i cron
```

### 3. Check Database
- Go to Railway dashboard → PostgreSQL → Query
- Check `tasks_emailtask` table for sent emails
- Check `farms_worker` table for worker configurations

## Security Best Practices

### 1. Use App Passwords
- Never use your main email password
- Generate app-specific passwords
- Rotate passwords regularly

### 2. Environment Variables
- Never commit email credentials to code
- Use Railway's secure environment variable storage
- Use different credentials for different environments

### 3. Email Validation
- Validate email addresses before sending
- Implement rate limiting for email sending
- Monitor for spam complaints

## Production Checklist

- [ ] Environment variables configured in Railway
- [ ] Gmail App Password generated and set
- [ ] Workers added to farms with email addresses
- [ ] Test email sent successfully
- [ ] Cron job scheduled and running
- [ ] Email templates rendering correctly
- [ ] Error handling and logging configured
- [ ] Monitoring and alerting set up

## Support

If you encounter issues:

1. Check Railway logs: `railway logs --tail`
2. Test email configuration: `railway run python manage.py send_daily_tasks --test`
3. Verify environment variables in Railway dashboard
4. Check Django admin for worker configurations
5. Review email provider documentation

---

**Note**: Railway's cron jobs run in UTC time. Adjust the schedule in `railway.toml` if you need different timezone scheduling.
