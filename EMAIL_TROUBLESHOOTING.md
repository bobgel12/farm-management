# 📧 Email Troubleshooting Guide

## 🔍 **Current Issue**
You're not receiving emails because the system is configured for development mode with console email backend.

## ✅ **Email is Working (Console Mode)**
The good news is that emails **are being generated** and sent to the console. You can see the email content in the Docker logs:

```bash
docker-compose logs backend | tail -20
```

## 🛠️ **Solutions**

### **Option 1: View Emails in Console (Current Setup)**
```bash
# View recent email logs
docker-compose logs backend | grep -A 20 -B 5 "Subject:"

# Follow logs in real-time
docker-compose logs -f backend
```

### **Option 2: Configure Real Email (Recommended)**

#### **Step 1: Set up Gmail App Password**
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Enable 2-Factor Authentication
3. Go to "App Passwords" → "Mail"
4. Generate a new app password (16 characters)

#### **Step 2: Create Environment File**
Create a `.env` file in the project root:

```bash
# .env file
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com
```

#### **Step 3: Restart Docker Services**
```bash
docker-compose down
docker-compose up -d
```

#### **Step 4: Test Email**
```bash
curl 'http://localhost:8000/api/tasks/send-test-email/' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data-raw '{"farm_id":1,"test_email":"your-email@gmail.com"}'
```

### **Option 3: Use Different Email Provider**

#### **Outlook/Hotmail**
```bash
# .env file
EMAIL_HOST=smtp-mail.outlook.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@outlook.com
EMAIL_HOST_PASSWORD=your-password
```

#### **Yahoo**
```bash
# .env file
EMAIL_HOST=smtp.mail.yahoo.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@yahoo.com
EMAIL_HOST_PASSWORD=your-app-password
```

### **Option 4: Force SMTP Mode (Development)**

#### **Temporary Fix - Override DEBUG Mode**
```bash
# Set DEBUG=False temporarily
docker-compose exec backend python manage.py shell -c "
from django.conf import settings
settings.DEBUG = False
settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
"
```

## 🔧 **Troubleshooting Steps**

### **1. Check Email Configuration**
```bash
docker-compose exec backend python manage.py shell -c "
from django.conf import settings
print('DEBUG:', settings.DEBUG)
print('EMAIL_BACKEND:', settings.EMAIL_BACKEND)
print('EMAIL_HOST:', settings.EMAIL_HOST)
print('EMAIL_HOST_USER:', settings.EMAIL_HOST_USER)
print('EMAIL_HOST_PASSWORD:', '***' if settings.EMAIL_HOST_PASSWORD else 'Not set')
"
```

### **2. Test Email Connection**
```bash
docker-compose exec backend python manage.py shell -c "
from django.core.mail import send_mail
from django.conf import settings
try:
    send_mail(
        'Test Subject',
        'Test message',
        settings.DEFAULT_FROM_EMAIL,
        ['your-email@gmail.com'],
        fail_silently=False,
    )
    print('Email sent successfully!')
except Exception as e:
    print('Email failed:', str(e))
"
```

### **3. Check Docker Logs**
```bash
# View all logs
docker-compose logs backend

# View only email-related logs
docker-compose logs backend | grep -i email

# Follow logs in real-time
docker-compose logs -f backend
```

## 📋 **Quick Setup Commands**

### **For Gmail (Recommended)**
```bash
# 1. Create .env file
cat > .env << EOF
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com
EOF

# 2. Restart services
docker-compose down && docker-compose up -d

# 3. Test email
curl 'http://localhost:8000/api/tasks/send-test-email/' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data-raw '{"farm_id":1,"test_email":"your-email@gmail.com"}'
```

## 🎯 **Expected Results**

### **Console Mode (Current)**
- ✅ Emails generated and logged to console
- ❌ No actual email delivery
- 📝 Perfect for development/testing

### **SMTP Mode (After Setup)**
- ✅ Emails sent to actual email addresses
- ✅ Real email delivery
- 📧 Perfect for production/demo

## 🚨 **Common Issues**

1. **"Authentication failed"** → Check app password
2. **"Connection refused"** → Check EMAIL_HOST and EMAIL_PORT
3. **"SMTPAuthenticationError"** → Verify credentials
4. **"Timeout"** → Check network/firewall settings

## 📞 **Need Help?**

If you're still having issues, please share:
1. The output of the configuration check
2. Any error messages from the logs
3. Which email provider you're using

The email system is working correctly - it just needs proper SMTP configuration to send real emails! 📧✨
