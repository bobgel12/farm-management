# SendGrid 401 Unauthorized Error - Troubleshooting Guide

## Error Message
```
ERROR SendGrid email failed: HTTP Error 401: Unauthorized
```

## What This Means
A 401 Unauthorized error from SendGrid indicates that your API key authentication failed. This typically happens when:

1. **API key is missing** - The `EMAIL_HOST_PASSWORD` environment variable is not set
2. **API key is incorrect** - The API key doesn't match what's in your SendGrid account
3. **API key is revoked** - The API key was deleted or disabled in SendGrid
4. **API key lacks permissions** - The API key doesn't have "Mail Send" permission enabled
5. **API key format is wrong** - The key doesn't start with `SG.`

## Quick Fix Steps

### Step 1: Verify Environment Variable
Check that `EMAIL_HOST_PASSWORD` is set in your environment:

**For Railway:**
```bash
railway variables
```

**For Local Development:**
```bash
echo $EMAIL_HOST_PASSWORD
```

### Step 2: Create/Verify SendGrid API Key

1. **Go to SendGrid Dashboard**: https://app.sendgrid.com
2. **Navigate to**: Settings → API Keys
3. **Create a new API Key** (or verify existing one):
   - Click "Create API Key"
   - Give it a name (e.g., "Chicken Management App")
   - **IMPORTANT**: Select "Full Access" or at minimum ensure "Mail Send" permission is enabled
   - Click "Create & View"
   - **Copy the API key immediately** (you won't be able to see it again!)

### Step 3: Update Environment Variable

**For Railway:**
```bash
railway variables --set "EMAIL_HOST_PASSWORD=SG.your-actual-api-key-here"
```

**For Local Development (.env file):**
```env
EMAIL_HOST_PASSWORD=SG.your-actual-api-key-here
```

**Important Notes:**
- The API key must start with `SG.`
- Don't include quotes around the API key value
- The key should be about 70 characters long

### Step 4: Verify Other Email Settings

Ensure these environment variables are set correctly:

```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=SG.your-actual-api-key-here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

**Note**: For SendGrid API (not SMTP), the `EMAIL_HOST_USER` should be `apikey`, but the actual API key goes in `EMAIL_HOST_PASSWORD`.

### Step 5: Verify Sender Authentication

SendGrid requires sender authentication. Make sure:

1. **Single Sender Verification** (for testing):
   - Go to Settings → Sender Authentication → Single Sender Verification
   - Verify your sender email address
   - Use this verified email in `DEFAULT_FROM_EMAIL`

2. **Domain Authentication** (for production):
   - Go to Settings → Sender Authentication → Domain Authentication
   - Follow the DNS setup instructions
   - This allows you to send from any email on your domain

### Step 6: Restart Your Application

After updating environment variables:

**For Railway:**
```bash
railway redeploy
```

**For Local Development:**
```bash
# Restart your Django server
python manage.py runserver
```

## Verification

After fixing the issue, test the email functionality:

1. **Check logs** - You should see:
   ```
   INFO SendGrid API key found: SG.xx...xxxx (length: 70)
   INFO SendGrid email sent successfully to ['recipient@example.com']
   ```

2. **Test email endpoint** - Use your application's test email feature if available

## Common Issues

### Issue: "Invalid SendGrid API key format"
**Solution**: API key must start with `SG.` and be the full key from SendGrid dashboard.

### Issue: "API key doesn't have 'Mail Send' permission"
**Solution**: 
1. Go to SendGrid → Settings → API Keys
2. Edit your API key
3. Ensure "Mail Send" permission is checked
4. Or create a new key with "Full Access"

### Issue: "Sender email not verified"
**Solution**: 
1. Go to SendGrid → Settings → Sender Authentication
2. Verify your sender email address
3. Update `DEFAULT_FROM_EMAIL` to match verified email

### Issue: API key works locally but not on Railway
**Solution**:
1. Verify the environment variable is set in Railway dashboard
2. Check that the variable name is exactly `EMAIL_HOST_PASSWORD`
3. Ensure there are no extra spaces or quotes
4. Redeploy the application after setting variables

## Testing SendGrid API Key

You can test your API key directly using curl:

```bash
curl -X POST "https://api.sendgrid.com/v3/mail/send" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "personalizations": [{
      "to": [{"email": "test@example.com"}]
    }],
    "from": {"email": "noreply@yourdomain.com"},
    "subject": "Test Email",
    "content": [{
      "type": "text/plain",
      "value": "This is a test email"
    }]
  }'
```

If you get a 401 error, the API key is invalid. If you get a 202 Accepted, the key is working!

## Additional Resources

- [SendGrid API Documentation](https://docs.sendgrid.com/api-reference)
- [SendGrid API Keys Guide](https://docs.sendgrid.com/ui/account-and-settings/api-keys)
- [SendGrid Sender Authentication](https://docs.sendgrid.com/ui/sending-email/sender-verification)

## Need More Help?

If the issue persists after following these steps:

1. Check the application logs for detailed error messages
2. Verify the API key in SendGrid dashboard is active
3. Try creating a new API key with full permissions
4. Ensure your SendGrid account is not suspended or restricted

