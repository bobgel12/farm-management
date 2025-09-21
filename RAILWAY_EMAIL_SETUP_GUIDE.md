# Railway Email Setup Guide

This guide will help you configure email functionality on Railway for the Chicken House Management application.

## 📧 Required Environment Variables

You need to set these environment variables in your Railway dashboard:

### 1. Go to Railway Dashboard
1. Navigate to your project on [Railway](https://railway.app)
2. Click on your service (backend)
3. Go to the "Variables" tab

### 2. Set Email Environment Variables

Add these environment variables:

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `EMAIL_HOST` | `smtp.gmail.com` | Gmail SMTP server |
| `EMAIL_PORT` | `587` | Gmail SMTP port |
| `EMAIL_USE_TLS` | `True` | Use TLS encryption |
| `EMAIL_HOST_USER` | `your-email@gmail.com` | Your Gmail address |
| `EMAIL_HOST_PASSWORD` | `your-app-password` | Gmail App Password (16 characters) |
| `DEFAULT_FROM_EMAIL` | `noreply@chickenmanagement.com` | Default sender email |

### 3. Gmail App Password Setup

1. **Enable 2-Factor Authentication** on your Google account
2. Go to [Google Account Settings](https://myaccount.google.com/)
3. Navigate to **Security** → **2-Step Verification** → **App passwords**
4. Generate a new app password for "Mail"
5. Copy the 16-character password (format: `xxxx xxxx xxxx xxxx`)
6. Set `EMAIL_HOST_PASSWORD` to this value (without spaces)

## 🔧 Configuration Details

### Email Settings in Code
The application uses `python-decouple` to load environment variables:

```python
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@chickenmanagement.com')
```

### Production vs Development
- **Development**: Uses `.env` file (local Docker)
- **Production**: Uses Railway environment variables

## 🧪 Testing Email on Railway

### 1. Test via API
Once deployed, you can test email functionality:

```bash
# Test email endpoint
curl -X POST https://your-railway-app.railway.app/api/tasks/send-test-email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"farm_id":1,"test_email":"your-test-email@gmail.com"}'
```

### 2. Check Logs
Monitor Railway logs to see email configuration:

```bash
# View logs in Railway dashboard or CLI
railway logs
```

Look for these log messages:
```
Email configuration - Host: smtp.gmail.com
Email configuration - Port: 587
Email configuration - User: your-email@gmail.com
Email configuration - Password: *******************
```

## 🚨 Troubleshooting

### Common Issues

1. **"Username and Password not accepted"**
   - Verify 2FA is enabled on Gmail
   - Check app password is correct (16 characters)
   - Ensure no spaces in the app password

2. **"SMTPAuthenticationError"**
   - Double-check `EMAIL_HOST_USER` matches your Gmail address
   - Verify `EMAIL_HOST_PASSWORD` is the app password, not your regular password

3. **Environment variables not loading**
   - Restart your Railway service after setting variables
   - Check variable names are exactly as specified (case-sensitive)

### Debug Steps

1. **Check Environment Variables**:
   ```python
   # Add this to your Django shell on Railway
   from django.conf import settings
   print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
   print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
   ```

2. **Test SMTP Connection**:
   ```python
   # Test in Django shell
   from django.core.mail import send_mail
   send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
   ```

## 📋 Verification Checklist

- [ ] 2FA enabled on Gmail account
- [ ] App password generated (16 characters)
- [ ] All environment variables set in Railway
- [ ] Railway service restarted after setting variables
- [ ] Test email sent successfully
- [ ] Daily task emails working (if cron is enabled)

## 🔄 Automatic Daily Emails

The application includes a cron job that sends daily task emails at 9 PM UTC:

```toml
[cron.daily-tasks]
schedule = "0 21 * * *"
command = "python manage.py send_daily_tasks"
```

This will automatically send daily task reminders to all active workers who have `receive_daily_tasks=True`.

## 📞 Support

If you encounter issues:
1. Check Railway logs for error messages
2. Verify all environment variables are set correctly
3. Test with a simple email first
4. Ensure Gmail app password is valid and not expired

---

**Note**: The email system is designed to work seamlessly between development (local Docker) and production (Railway) environments. The same configuration approach is used in both cases.
