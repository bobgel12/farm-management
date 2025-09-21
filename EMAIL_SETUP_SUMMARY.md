# 📧 Email Setup Summary

## 🎯 **Quick Start**

### **For Local Development:**
```bash
# 1. Run the setup script
./setup_email.sh

# 2. Edit .env file with your email credentials
# 3. Restart Docker
docker-compose down && docker-compose up -d

# 4. Test email
python test_email.py
```

### **For Railway Deployment:**
1. Go to Railway dashboard → Variables
2. Add email variables from `railway.env.example`
3. Deploy your application

---

## 📋 **Step-by-Step Instructions**

### **🏠 Local Development**

#### **Step 1: Set up Gmail App Password**
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Enable 2-Factor Authentication
3. Go to "Security" → "App Passwords"
4. Generate a new app password for "Mail" (16 characters)

#### **Step 2: Configure Environment**
```bash
# Run setup script
./setup_email.sh

# Edit .env file with your credentials
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com
DEBUG=False
```

#### **Step 3: Test Configuration**
```bash
# Test email configuration
python test_email.py

# Test via API
curl 'http://localhost:8000/api/tasks/send-test-email/' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data-raw '{"farm_id":1,"test_email":"your-email@gmail.com"}'
```

### **🚀 Railway Deployment**

#### **Step 1: Railway Environment Variables**
In Railway dashboard → Variables, add:
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com
DEBUG=False
```

#### **Step 2: Deploy and Test**
```bash
# Deploy to Railway
railway deploy

# Test email via Railway URL
curl 'https://your-app.railway.app/api/tasks/send-test-email/' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data-raw '{"farm_id":1,"test_email":"your-email@gmail.com"}'
```

---

## 🔧 **Configuration Files**

### **Local Development**
- `.env` - Environment variables
- `docker-compose.yml` - Docker configuration
- `setup_email.sh` - Setup script
- `test_email.py` - Test script

### **Railway Deployment**
- `railway.toml` - Railway configuration
- `railway.json` - Alternative Railway config
- `railway.env.example` - Environment variables template

---

## 🧪 **Testing**

### **Test Email Configuration**
```bash
python test_email.py
```

### **Test via API**
```bash
# Local
curl 'http://localhost:8000/api/tasks/send-test-email/' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data-raw '{"farm_id":1,"test_email":"your-email@gmail.com"}'

# Railway
curl 'https://your-app.railway.app/api/tasks/send-test-email/' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data-raw '{"farm_id":1,"test_email":"your-email@gmail.com"}'
```

### **Test Daily Tasks**
```bash
# Send daily tasks for all farms
curl 'http://localhost:8000/api/tasks/send-daily-tasks/' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data-raw '{}'

# Send daily tasks for specific farm
curl 'http://localhost:8000/api/tasks/send-daily-tasks/' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data-raw '{"farm_id":1}'
```

---

## 🚨 **Troubleshooting**

### **Common Issues**

1. **"Authentication failed"**
   - Check app password (16 characters)
   - Verify 2FA is enabled
   - Check email address

2. **"Connection refused"**
   - Check EMAIL_HOST and EMAIL_PORT
   - Verify network connectivity
   - Check firewall settings

3. **"SMTPAuthenticationError"**
   - Verify credentials
   - Check app password format
   - Ensure 2FA is enabled

4. **"Timeout"**
   - Check network connection
   - Verify SMTP settings
   - Check firewall/antivirus

### **Debug Steps**

1. **Check configuration:**
   ```bash
   python test_email.py
   ```

2. **Check Docker logs:**
   ```bash
   docker-compose logs backend | grep -i email
   ```

3. **Check Railway logs:**
   ```bash
   railway logs
   ```

---

## 📚 **Additional Resources**

- `EMAIL_SETUP_COMPLETE.md` - Detailed setup instructions
- `EMAIL_TROUBLESHOOTING.md` - Troubleshooting guide
- `RAILWAY_EMAIL_SETUP.md` - Railway-specific setup
- `test_email.py` - Email configuration test script
- `setup_email.sh` - Quick setup script

---

## ✅ **Success Checklist**

- [ ] Gmail app password created (16 characters)
- [ ] `.env` file configured with credentials
- [ ] Docker services restarted
- [ ] Email configuration test passed
- [ ] API test email sent successfully
- [ ] Railway environment variables set
- [ ] Railway deployment successful
- [ ] Railway email test passed

**Your email system is now fully configured for both local development and Railway deployment!** 🎉📧✨
