# Quick Email Setup Guide

## Current Status
❌ **Email is NOT configured** - Credentials are missing

## Quick Fix (5 minutes)

### Option 1: Gmail (Easiest for Development)

1. **Get Gmail App Password**:
   - Go to: https://myaccount.google.com/apppasswords
   - Enable 2FA if not already enabled
   - Generate password for "Mail"
   - Copy the 16-character password

2. **Set Environment Variables**:

   **For Docker (docker-compose.yml)**:
   ```yaml
   environment:
     - EMAIL_HOST_USER=your-email@gmail.com
     - EMAIL_HOST_PASSWORD=your-16-char-app-password
   ```

   **Or create `.env` file**:
   ```bash
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   ```

3. **Restart Docker**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Test**:
   ```bash
   docker-compose exec backend python /app/test_email_debug.py
   ```

### Option 2: SendGrid (Best for Production)

1. **Sign up**: https://sendgrid.com (Free tier: 100 emails/day)

2. **Get API Key**:
   - Dashboard → Settings → API Keys
   - Create API Key
   - Copy the key (starts with `SG.`)

3. **Set Environment Variables**:
   ```bash
   EMAIL_HOST=smtp.sendgrid.net
   EMAIL_HOST_USER=apikey
   EMAIL_HOST_PASSWORD=SG.your-api-key-here
   DEFAULT_FROM_EMAIL=noreply@yourdomain.com
   ```

4. **Restart and Test** (same as above)

## Test Email Sending

### Method 1: Test Script
```bash
docker-compose exec backend python /app/test_email_debug.py
```

### Method 2: API Endpoint
```bash
# Get auth token
TOKEN=$(curl -X POST http://localhost:8002/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.token')

# Send test email
curl -X POST http://localhost:8002/api/tasks/send-test-email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token $TOKEN" \
  -d '{"farm_id": 1, "test_email": "your-email@gmail.com"}'
```

### Method 3: Django Shell
```bash
docker-compose exec backend python manage.py shell
```

```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test.',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@gmail.com'],
    fail_silently=False,
)
```

## Verify It's Working

✅ **Success indicators**:
- Test script shows "✅ SMTP connection successful!"
- Test script shows "✅ Test email sent successfully!"
- You receive email in your inbox

❌ **Failure indicators**:
- "Using console email backend" warning
- "SMTP connection failed" error
- "Email credentials not configured" error

## Troubleshooting

### "SMTPAuthenticationError"
- Use App Password (not regular Gmail password)
- Verify 2FA is enabled
- Remove spaces from password

### "Connection timeout"
- Check firewall/network
- Verify port 587 is open
- Try port 465 with SSL

### "Console backend being used"
- Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Restart Docker after setting variables

## Full Documentation

See `EMAIL_DEBUG_REPORT.md` for comprehensive debugging guide.

