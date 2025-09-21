# Railway Deployment Guide

## Overview
This guide explains how to deploy the Chicken House Management System to Railway with proper email configuration for daily task reminders.

## Prerequisites

### 1. Install Railway CLI
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login
```

### 2. Prepare Email Credentials
- **Gmail Account** (recommended)
- **App Password** (not your regular password)
- **Domain** for email addresses

## Quick Deployment

### Option 1: Automated Script (Recommended)
```bash
# Run the deployment script
./deploy_railway.sh
```

### Option 2: Manual Deployment

#### Step 1: Initialize Railway Project
```bash
# Create new project
railway init

# Or link to existing project
railway link
```

#### Step 2: Add PostgreSQL Service
```bash
railway add postgresql
```

#### Step 3: Set Environment Variables
```bash
# Django settings
railway variables set SECRET_KEY="$(openssl rand -base64 32)"
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS="*.railway.app,localhost,127.0.0.1"

# Admin credentials
railway variables set ADMIN_USERNAME=admin
railway variables set ADMIN_PASSWORD="$(openssl rand -base64 16)"
railway variables set ADMIN_EMAIL=admin@chickenmanagement.com

# Email configuration
railway variables set EMAIL_HOST=smtp.gmail.com
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=your-email@gmail.com
railway variables set EMAIL_HOST_PASSWORD=your-16-char-app-password
railway variables set DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

#### Step 4: Deploy Application
```bash
railway up
```

## Email Configuration Details

### Gmail Setup
1. **Enable 2-Factor Authentication**
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable "2-Step Verification"

2. **Generate App Password**
   - Go to "App passwords" in Google Account Security
   - Select "Mail" and generate password
   - Use this 16-character password as `EMAIL_HOST_PASSWORD`

3. **Set Environment Variables**
   ```bash
   railway variables set EMAIL_HOST_USER=your-email@gmail.com
   railway variables set EMAIL_HOST_PASSWORD=your-16-char-app-password
   railway variables set DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

### Alternative Email Providers

#### SendGrid
```bash
railway variables set EMAIL_HOST=smtp.sendgrid.net
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=apikey
railway variables set EMAIL_HOST_PASSWORD=your-sendgrid-api-key
```

#### Mailgun
```bash
railway variables set EMAIL_HOST=smtp.mailgun.org
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=your-mailgun-smtp-username
railway variables set EMAIL_HOST_PASSWORD=your-mailgun-smtp-password
```

## Testing Email Functionality

### 1. Test Email Configuration
```bash
# Test email connection
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
```

### 2. Check Application Logs
```bash
# View deployment logs
railway logs --tail

# Filter for email-related logs
railway logs --tail | grep -i email
```

### 3. Verify Cron Job
```bash
# Check if cron job is running
railway logs --tail | grep -i cron
```

## Daily Email Schedule

The application is configured to send daily task emails at **9 PM UTC** every day.

### Cron Configuration
- **Schedule**: `0 21 * * *` (9 PM UTC daily)
- **Command**: `python manage.py send_daily_tasks`
- **Timezone**: UTC (Railway default)

### Email Content
- **Today's Tasks**: All incomplete tasks for current chicken day
- **Tomorrow's Tasks**: All tasks for next chicken day
- **House Information**: Current day, status, chicken in date
- **Recipients**: All active workers with `receive_daily_tasks=True`

## Monitoring and Maintenance

### 1. Check Email Delivery
```bash
# View email logs
railway logs --tail | grep -i "email\|mail"

# Check database for sent emails
railway run python manage.py shell -c "
from tasks.models import EmailTask
print('Sent emails:', EmailTask.objects.count())
for email in EmailTask.objects.all()[:5]:
    print(f'{email.sent_date}: {email.farm.name} - {email.tasks_count} tasks')
"
```

### 2. Monitor Application Health
```bash
# Check application status
railway status

# View recent deployments
railway deployments
```

### 3. Update Application
```bash
# Deploy latest changes
railway up

# Check deployment status
railway logs --tail
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
from django.core.mail import get_connection
from django.conf import settings
try:
    connection = get_connection()
    connection.open()
    print('✅ Email connection successful')
    connection.close()
except Exception as e:
    print(f'❌ Email connection failed: {e}')
"

# Check environment variables
railway run python manage.py shell -c "
import os
print('Email env vars:')
for key in ['EMAIL_HOST', 'EMAIL_PORT', 'EMAIL_HOST_USER', 'EMAIL_HOST_PASSWORD']:
    value = os.getenv(key, 'Not set')
    if key == 'EMAIL_HOST_PASSWORD':
        value = '***' if value != 'Not set' else value
    print(f'{key}: {value}')
"

# Test sending email
railway run python manage.py shell -c "
from django.core.mail import send_mail
try:
    send_mail(
        'Test Email',
        'This is a test email from Railway deployment.',
        'noreply@chickenmanagement.com',
        ['your-email@example.com'],
        fail_silently=False,
    )
    print('✅ Test email sent successfully')
except Exception as e:
    print(f'❌ Test email failed: {e}')
"
```

## Security Best Practices

### 1. Environment Variables
- Never commit email credentials to code
- Use Railway's secure environment variable storage
- Rotate passwords regularly

### 2. Email Security
- Use App Passwords instead of main passwords
- Monitor for spam complaints
- Implement rate limiting

### 3. Application Security
- Use strong SECRET_KEY
- Set DEBUG=False in production
- Configure ALLOWED_HOSTS properly

## Production Checklist

- [ ] Railway CLI installed and logged in
- [ ] PostgreSQL service added
- [ ] Environment variables configured
- [ ] Email credentials set (Gmail App Password)
- [ ] Application deployed successfully
- [ ] Test email sent successfully
- [ ] Cron job scheduled and running
- [ ] Workers added to farms
- [ ] Daily emails being sent
- [ ] Monitoring and logging configured

## Support

If you encounter issues:

1. **Check Railway Logs**: `railway logs --tail`
2. **Test Email Config**: `railway run python manage.py send_daily_tasks --test`
3. **Verify Environment Variables**: Check Railway dashboard
4. **Review Documentation**: See `RAILWAY_EMAIL_SETUP.md`
5. **Check Database**: Verify workers and farms are configured

---

**Note**: Railway's cron jobs run in UTC time. The daily emails will be sent at 9 PM UTC every day. Adjust your local time expectations accordingly.
