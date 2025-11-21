# Email Functionality Debug Report

## Test Results Summary

### Date: 2025-11-20

### Current Status: ❌ Email Not Configured

## Test Results

### ✅ Test 1: Email Configuration Check
- **EMAIL_BACKEND**: `django.core.mail.backends.console.EmailBackend` (Console backend - emails print to console)
- **EMAIL_HOST**: `smtp.gmail.com` ✅
- **EMAIL_PORT**: `587` ✅
- **EMAIL_USE_TLS**: `True` ✅
- **EMAIL_HOST_USER**: ❌ **NOT SET**
- **EMAIL_HOST_PASSWORD**: ❌ **NOT SET**
- **DEFAULT_FROM_EMAIL**: `noreply@chickenmanagement.com` ✅

### ❌ Issue Identified
**Email credentials are missing!** The system is using the console email backend because `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are not configured.

## How Email Works in This System

### Email Service Architecture

1. **Primary Email Service**: `TaskEmailService` (in `backend/tasks/email_service.py`)
   - Handles daily task reminder emails
   - Supports multiple email providers (SMTP, SendGrid)
   - Has test email functionality

2. **Alternative Email Service**: `EmailService` (in `backend/tasks/email_alternatives.py`)
   - Unified email service for multiple providers
   - Supports SMTP, SendGrid, and Mailgun

3. **Email Backend Selection**:
   - If `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are set → Uses SMTP backend
   - If not set → Uses console backend (emails print to logs)
   - If `EMAIL_HOST` contains `sendgrid.net` → Uses SendGrid API

### Email Configuration Flow

```
Environment Variables → Django Settings → Email Backend → Email Service
```

1. Environment variables are loaded via `python-decouple`
2. Settings in `backend/chicken_management/settings.py` configure Django email
3. Email backend is selected based on credentials
4. Email service classes handle the actual sending

## Configuration Options

### Option 1: Gmail SMTP (Recommended for Development)

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Generate password for "Mail"
   - Copy the 16-character password

3. **Set Environment Variables**:
   ```bash
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com
   ```

4. **For Docker**:
   - Add to `docker-compose.yml` environment section
   - Or create `.env` file and reference variables

### Option 2: SendGrid (Recommended for Production/Railway)

1. **Sign up at SendGrid**: https://sendgrid.com
2. **Get API Key**: Generate API key in SendGrid dashboard
3. **Set Environment Variables**:
   ```bash
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=SG.your-sendgrid-api-key
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

### Option 3: Mailgun

1. **Sign up at Mailgun**: https://mailgun.com
2. **Get API Key and Domain**
3. **Set Environment Variables**:
   ```bash
   EMAIL_HOST=smtp.mailgun.org
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=postmaster@yourdomain.mailgun.org
   EMAIL_HOST_PASSWORD=your-mailgun-api-key
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

## Testing Email Functionality

### Method 1: Using the Test Script

```bash
# Run the comprehensive test script
docker-compose exec backend python /app/test_email_debug.py
```

### Method 2: Using Django Management Command

```bash
# Send test email via management command
docker-compose exec backend python manage.py send_daily_tasks \
  --farm-id 1 \
  --test-email your-email@gmail.com
```

### Method 3: Using API Endpoint

```bash
# Get authentication token first
TOKEN=$(curl -X POST http://localhost:8002/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Send test email
curl -X POST http://localhost:8002/api/tasks/send-test-email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token $TOKEN" \
  -d '{"farm_id": 1, "test_email": "your-email@gmail.com"}'
```

### Method 4: Using Django Shell

```bash
docker-compose exec backend python manage.py shell
```

Then in the shell:
```python
from django.core.mail import send_mail
from django.conf import settings

# Check configuration
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")

# Send test email
send_mail(
    'Test Email',
    'This is a test email.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@gmail.com'],
    fail_silently=False,
)
```

## Debugging Steps

### Step 1: Verify Environment Variables

```bash
docker-compose exec backend env | grep EMAIL
```

### Step 2: Check Django Settings

```bash
docker-compose exec backend python manage.py shell -c "
from django.conf import settings
print(f'EMAIL_BACKEND: {settings.EMAIL_BACKEND}')
print(f'EMAIL_HOST: {settings.EMAIL_HOST}')
print(f'EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}')
print(f'EMAIL_HOST_PASSWORD: {\"*\" * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else \"NOT SET\"}')
"
```

### Step 3: Test SMTP Connection

```bash
docker-compose exec backend python manage.py shell -c "
from django.core.mail.backends.smtp import EmailBackend
from django.conf import settings

backend = EmailBackend(
    host=settings.EMAIL_HOST,
    port=settings.EMAIL_PORT,
    username=settings.EMAIL_HOST_USER,
    password=settings.EMAIL_HOST_PASSWORD,
    use_tls=settings.EMAIL_USE_TLS,
    fail_silently=False
)
backend.open()
print('✅ SMTP connection successful!')
backend.close()
"
```

### Step 4: Check Application Logs

```bash
docker-compose logs backend | grep -i email
```

## Common Issues and Solutions

### Issue 1: "Email credentials not configured"
**Solution**: Set `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` environment variables

### Issue 2: "SMTPAuthenticationError"
**Solution**: 
- For Gmail: Use App Password (not regular password)
- Verify 2FA is enabled
- Check password has no spaces

### Issue 3: "Connection timeout"
**Solution**:
- Check firewall settings
- Verify SMTP port is correct (587 for TLS)
- Check network connectivity

### Issue 4: "Email sending disabled due to network restrictions"
**Solution**: 
- Railway free tier blocks SMTP
- Use SendGrid API instead
- Or upgrade to Railway Pro

### Issue 5: Console backend being used
**Solution**: 
- Set `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD`
- Restart Docker container after setting variables

## Next Steps

1. **Configure Email Credentials**:
   - Choose email provider (Gmail, SendGrid, or Mailgun)
   - Set environment variables
   - Restart Docker containers

2. **Test Email Sending**:
   - Run test script: `python test_email_debug.py`
   - Or use API endpoint: `POST /api/tasks/send-test-email/`

3. **Verify Email Delivery**:
   - Check recipient inbox
   - Check spam folder
   - Review application logs

4. **Monitor Email Functionality**:
   - Check email history via API: `GET /api/tasks/email-history/`
   - Monitor logs for email errors
   - Test daily task emails

## Files Related to Email

- `backend/tasks/email_service.py` - Main email service
- `backend/tasks/email_alternatives.py` - Alternative email providers
- `backend/chicken_management/settings.py` - Email configuration
- `backend/tasks/views.py` - Email API endpoints
- `backend/tasks/urls.py` - Email URL routes
- `test_email_debug.py` - Comprehensive test script
- `RAILWAY_EMAIL_SETUP_GUIDE.md` - Railway setup guide
- `RAILWAY_EMAIL_ALTERNATIVES.md` - Alternative email services

## API Endpoints

- `POST /api/tasks/send-test-email/` - Send test email
  - Body: `{"farm_id": 1, "test_email": "email@example.com"}`
  
- `POST /api/tasks/send-daily-tasks/` - Send daily task emails
  - Body: `{"farm_id": 1}` (optional)
  
- `GET /api/tasks/email-history/` - Get email history

## Conclusion

The email functionality is **not currently working** because email credentials are not configured. The system is using the console backend, which means emails are being printed to logs instead of being sent.

**To fix this:**
1. Set `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` environment variables
2. Restart Docker containers
3. Run the test script to verify configuration
4. Test sending an email via API or management command

