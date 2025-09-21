# 📧 Complete Email Setup Guide

## 🏠 **Local Development Setup**

### **Step 1: Choose Email Provider**

#### **Option A: Gmail (Recommended)**
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Enable 2-Factor Authentication
3. Go to "Security" → "App Passwords"
4. Generate a new app password for "Mail" (16 characters)

#### **Option B: Outlook/Hotmail**
1. Go to [Microsoft Account Security](https://account.microsoft.com/security)
2. Enable 2-Factor Authentication
3. Go to "Security" → "App Passwords"
4. Generate a new app password

#### **Option C: Yahoo**
1. Go to [Yahoo Account Security](https://login.yahoo.com/account/security)
2. Enable 2-Factor Authentication
3. Go to "App Passwords"
4. Generate a new app password

### **Step 2: Create Local Environment File**

Create a `.env` file in the project root:

```bash
# .env file for local development
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com

# Optional: Override other settings
DEBUG=False  # Set to False to use SMTP instead of console
```

### **Step 3: Update Docker Compose for Local**

The Docker Compose file is already updated to use environment variables. Make sure it looks like this:

```yaml
environment:
  - DEBUG=True  # Set to False for real emails
  - EMAIL_HOST=smtp.gmail.com
  - EMAIL_PORT=587
  - EMAIL_USE_TLS=True
  - EMAIL_HOST_USER=${EMAIL_HOST_USER:-}
  - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD:-}
  - DEFAULT_FROM_EMAIL=${DEFAULT_FROM_EMAIL:-noreply@chickenmanagement.com}
```

### **Step 4: Test Local Email**

```bash
# 1. Restart Docker services
docker-compose down
docker-compose up -d

# 2. Test email sending
curl 'http://localhost:8000/api/tasks/send-test-email/' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -H 'Content-Type: application/json' \
  --data-raw '{"farm_id":1,"test_email":"your-email@gmail.com"}'
```

---

## 🚀 **Railway Deployment Setup**

### **Step 1: Railway Environment Variables**

In your Railway dashboard, go to your project → Variables and add:

```bash
# Required Email Variables
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com

# Optional: Override DEBUG for production
DEBUG=False
```

### **Step 2: Railway Configuration Files**

#### **railway.toml**
```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:$PORT"
healthcheckPath = "/api/"
healthcheckTimeout = 300
restartPolicyType = "on_failure"

[env]
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = "587"
EMAIL_USE_TLS = "True"
DEFAULT_FROM_EMAIL = "noreply@chickenmanagement.com"
```

#### **railway.json**
```json
{
  "build": {
    "builder": "dockerfile",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "startCommand": "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:$PORT",
    "healthcheckPath": "/api/",
    "healthcheckTimeout": 300,
    "restartPolicyType": "on_failure"
  },
  "env": {
    "EMAIL_HOST": "smtp.gmail.com",
    "EMAIL_PORT": "587",
    "EMAIL_USE_TLS": "True",
    "DEFAULT_FROM_EMAIL": "noreply@chickenmanagement.com"
  }
}
```

### **Step 3: Update Settings for Railway**

Let me update the settings to handle Railway environment properly:
