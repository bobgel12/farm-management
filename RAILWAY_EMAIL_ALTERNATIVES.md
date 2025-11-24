# Railway Email Alternatives

Since Railway blocks outbound SMTP connections on the free tier, here are alternative solutions:

## 🚀 **Option 1: Railway Pro (Recommended)**
- **Cost**: $5/month
- **Benefit**: Enables outbound SMTP connections
- **Setup**: Just upgrade your Railway plan
- **Result**: Gmail SMTP will work immediately

## 📧 **Option 2: Alternative Email Services**

### **SendGrid (Free Tier)**
```bash
# Set these environment variables in Railway
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your_sendgrid_api_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### **Mailgun (Free Tier)**
```bash
# Set these environment variables in Railway
EMAIL_HOST=smtp.mailgun.org
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=postmaster@yourdomain.mailgun.org
EMAIL_HOST_PASSWORD=your_mailgun_password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### **Amazon SES (Pay-as-you-go)**
```bash
# Set these environment variables in Railway
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_ses_access_key
EMAIL_HOST_PASSWORD=your_ses_secret_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

## 🔧 **Option 3: Resend (BEST for Low Volume - 3,000 emails/month FREE)**

**Perfect for <50 emails/month!** Already implemented in the codebase.

```bash
# Set these environment variables in Railway
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_your_api_key_here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

**Setup**:
1. Sign up at https://resend.com (free, no credit card)
2. Get API key from dashboard
3. Set environment variables above
4. Redeploy

**That's it!** No code changes needed - the code automatically uses Resend when `EMAIL_PROVIDER=resend` is set.

See `LOW_VOLUME_EMAIL_ALTERNATIVES.md` for complete guide.

### **EmailJS (Client-side)**
- Send emails directly from frontend
- No backend email service needed
- Free tier available

## 🎯 **Recommended Solution**

**For low volume (<50 emails/month)**: Use **Resend** (3,000 emails/month free) ⭐ **BEST FOR LOW VOLUME**
**For immediate fix**: Upgrade to Railway Pro ($5/month)
**For free solution**: Use SendGrid free tier (100 emails/day)

## 📋 **Quick Setup with SendGrid**

1. **Sign up at SendGrid**: https://sendgrid.com
2. **Create API Key**: Settings → API Keys → Create API Key
3. **Set Railway variables**:
   ```bash
   railway variables --set "EMAIL_HOST=smtp.sendgrid.net"
   railway variables --set "EMAIL_PORT=587"
   railway variables --set "EMAIL_USE_TLS=True"
   railway variables --set "EMAIL_HOST_USER=apikey"
   railway variables --set "EMAIL_HOST_PASSWORD=your_sendgrid_api_key"
   ```
4. **Redeploy**: `railway redeploy`

## 🔍 **Why This Happens**

- **Railway Free Tier**: Blocks outbound SMTP ports (25, 587, 465)
- **Security**: Prevents spam and abuse
- **Common**: Most cloud platforms have similar restrictions
- **Solution**: Use approved email services or upgrade plan
