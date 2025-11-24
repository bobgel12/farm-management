# Low-Volume Email Alternatives for Railway (<50 emails/month)

Since SendGrid is too expensive for low-volume usage, here are the best alternatives that work perfectly with Railway and are either **free** or **extremely cheap** for <50 emails/month.

## 🏆 **Recommended: Resend (Best Free Option)**

**Free Tier**: 3,000 emails/month, 100 emails/day  
**Cost**: $0/month for your use case  
**Why it's perfect**: Modern API, great documentation, no credit card required, works seamlessly with Railway

### Setup Steps

1. **Sign up at Resend**: https://resend.com (free account)
2. **Get API Key**: Dashboard → API Keys → Create API Key
3. **Verify Domain** (or use their test domain for testing):
   - Go to Domains → Add Domain
   - Follow DNS setup instructions
   - Or use `onboarding@resend.dev` for testing (limited)
4. **Set Railway Environment Variables**:
   ```bash
   railway variables --set "EMAIL_PROVIDER=resend"
   railway variables --set "RESEND_API_KEY=re_your_api_key_here"
   railway variables --set "DEFAULT_FROM_EMAIL=noreply@yourdomain.com"
   ```
5. **Redeploy**: `railway redeploy`

### Configuration

```env
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_your_api_key_here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

**Note**: The code automatically detects Resend when `EMAIL_PROVIDER=resend` is set, or you can use `EMAIL_HOST=resend.com`.

---

## 💰 **Option 2: Amazon SES (Extremely Cheap)**

**Free Tier**: 3,000 emails/month for first 12 months  
**Cost After Free Tier**: $0.10 per 1,000 emails (so **<50 emails = $0.005/month**)  
**Why it's great**: Extremely reliable, used by major companies, very cheap

### Setup Steps

1. **Sign up for AWS**: https://aws.amazon.com (free tier available)
2. **Go to Amazon SES**: AWS Console → Simple Email Service
3. **Verify Email Address** (or domain):
   - Go to Verified identities → Create identity
   - Verify your email or domain
4. **Create IAM User**:
   - Go to IAM → Users → Create user
   - Attach policy: `AmazonSESFullAccess` (or create custom policy)
   - Save Access Key ID and Secret Access Key
5. **Set Railway Environment Variables**:
   ```bash
   railway variables --set "EMAIL_HOST=email-smtp.us-east-1.amazonaws.com"
   railway variables --set "EMAIL_PORT=587"
   railway variables --set "EMAIL_USE_TLS=True"
   railway variables --set "EMAIL_HOST_USER=your_aws_access_key_id"
   railway variables --set "EMAIL_HOST_PASSWORD=your_aws_secret_access_key"
   railway variables --set "DEFAULT_FROM_EMAIL=noreply@yourdomain.com"
   ```
6. **Move out of Sandbox** (if needed):
   - By default, SES is in sandbox mode (can only send to verified emails)
   - Request production access: SES → Account dashboard → Request production access

### Configuration

```env
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_aws_access_key_id
EMAIL_HOST_PASSWORD=your_aws_secret_access_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

**Cost Calculation**: 50 emails/month = $0.005/month (practically free!)

---

## 🆓 **Option 3: Brevo (formerly Sendinblue)**

**Free Tier**: 300 emails/day (9,000/month)  
**Cost**: $0/month for your use case  
**Why it's good**: Generous free tier, SMTP and API support

### Setup Steps

1. **Sign up at Brevo**: https://www.brevo.com
2. **Verify Email**: Go to Senders → Add a sender → Verify your email
3. **Get SMTP Credentials**: Settings → SMTP & API → SMTP
4. **Set Railway Environment Variables**:
   ```bash
   railway variables --set "EMAIL_HOST=smtp-relay.brevo.com"
   railway variables --set "EMAIL_PORT=587"
   railway variables --set "EMAIL_USE_TLS=True"
   railway variables --set "EMAIL_HOST_USER=your_brevo_email"
   railway variables --set "EMAIL_HOST_PASSWORD=your_brevo_smtp_key"
   railway variables --set "DEFAULT_FROM_EMAIL=noreply@yourdomain.com"
   ```

### Configuration

```env
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_brevo_email
EMAIL_HOST_PASSWORD=your_brevo_smtp_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

---

## 📧 **Option 4: SparkPost**

**Free Tier**: 500 emails/month, 100 emails/day  
**Cost**: $0/month for your use case  
**Why it's good**: Simple setup, good for testing

### Setup Steps

1. **Sign up at SparkPost**: https://www.sparkpost.com
2. **Create API Key**: Account → API Keys → Create API Key
3. **Verify Sending Domain**: Sending Domains → Add Domain
4. **Set Railway Environment Variables**:
   ```bash
   railway variables --set "EMAIL_PROVIDER=sparkpost"
   railway variables --set "SPARKPOST_API_KEY=your_api_key"
   railway variables --set "DEFAULT_FROM_EMAIL=noreply@yourdomain.com"
   ```

**Note**: SparkPost requires custom implementation (not currently in codebase, but can be added).

---

## 📊 **Comparison Table**

| Service | Free Tier | Cost for 50 emails/month | Setup Difficulty | Railway Compatible |
|---------|-----------|-------------------------|------------------|-------------------|
| **Resend** | 3,000/month | **$0** | ⭐ Easy | ✅ Yes (API) |
| **Amazon SES** | 3,000/month (12mo) | **$0.005** | ⭐⭐ Medium | ✅ Yes (SMTP) |
| **Brevo** | 9,000/month | **$0** | ⭐ Easy | ✅ Yes (SMTP) |
| **SparkPost** | 500/month | **$0** | ⭐⭐ Medium | ✅ Yes (API) |
| **Mailgun** | 5,000/month (3mo) | $35/month after | ⭐⭐ Medium | ✅ Yes (API) |
| **SendGrid** | 100/day | $19.95/month | ⭐ Easy | ✅ Yes (API) |

---

## 🎯 **My Recommendation for <50 emails/month**

### **Best Choice: Resend** ⭐⭐⭐⭐⭐

**Why Resend is perfect for you:**
- ✅ **3,000 emails/month free** (60x your needs!)
- ✅ **No credit card required**
- ✅ **Modern, clean API** (already implemented in codebase)
- ✅ **Works perfectly with Railway** (no SMTP needed)
- ✅ **Great documentation and support**
- ✅ **Fast and reliable**

### **Setup Time**: ~5 minutes

1. Sign up at https://resend.com
2. Get API key
3. Set environment variables:
   ```bash
   railway variables --set "EMAIL_PROVIDER=resend"
   railway variables --set "RESEND_API_KEY=re_your_key"
   railway variables --set "DEFAULT_FROM_EMAIL=noreply@yourdomain.com"
   ```
4. Redeploy

**That's it!** Your emails will work immediately.

---

## 🔧 **Implementation Status**

✅ **Resend** - Fully implemented in `email_service.py`  
✅ **SendGrid** - Already implemented  
✅ **Mailgun** - Already implemented  
⚠️ **Amazon SES** - Uses SMTP (works if Railway Pro, or use API wrapper)  
⚠️ **Brevo** - Uses SMTP (works if Railway Pro, or use API wrapper)

---

## 🚀 **Quick Migration from SendGrid to Resend**

1. **Sign up for Resend**: https://resend.com
2. **Get your API key** from Resend dashboard
3. **Update Railway variables**:
   ```bash
   railway variables --set "EMAIL_PROVIDER=resend"
   railway variables --set "RESEND_API_KEY=re_your_key_here"
   # Remove or keep EMAIL_HOST (not needed for Resend)
   ```
4. **Redeploy**: `railway redeploy`
5. **Test**: Send a test email from your app

**No code changes needed!** The code automatically detects `EMAIL_PROVIDER=resend` and uses Resend API.

---

## 📝 **Environment Variable Reference**

### For Resend (Recommended)
```env
EMAIL_PROVIDER=resend
RESEND_API_KEY=re_your_api_key_here
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### For Amazon SES
```env
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_aws_access_key_id
EMAIL_HOST_PASSWORD=your_aws_secret_access_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### For Brevo
```env
EMAIL_HOST=smtp-relay.brevo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_brevo_email
EMAIL_HOST_PASSWORD=your_brevo_smtp_key
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

---

## ❓ **FAQ**

### Q: Do I need Railway Pro for these services?
**A**: No! All these services use HTTP APIs (not SMTP), so they work on Railway's free tier.

### Q: Which service is easiest to set up?
**A**: Resend is the easiest - just sign up, get API key, set environment variable, done!

### Q: Will I hit any limits with 50 emails/month?
**A**: No! All recommended services have free tiers well above 50 emails/month.

### Q: Can I switch between services easily?
**A**: Yes! Just change the `EMAIL_PROVIDER` environment variable and redeploy.

### Q: Do I need to verify my domain?
**A**: For production, yes. For testing, Resend provides a test domain. Other services may require verification.

---

## 🆘 **Need Help?**

If you run into issues:
1. Check application logs for detailed error messages
2. Verify environment variables are set correctly in Railway
3. Ensure your sender email is verified in the service dashboard
4. Test with a simple email first before sending production emails

---

## 📚 **Additional Resources**

- [Resend Documentation](https://resend.com/docs)
- [Amazon SES Documentation](https://docs.aws.amazon.com/ses/)
- [Brevo Documentation](https://developers.brevo.com/)
- [Railway Environment Variables Guide](https://docs.railway.app/develop/variables)

