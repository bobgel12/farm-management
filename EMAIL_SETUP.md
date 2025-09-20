# Daily Task Email Setup Guide

## Overview
This guide explains how to set up daily task reminder emails that are sent at 9pm to all farm workers with today's and tomorrow's tasks.

## Features
- ✅ **Daily Email Reminders**: Automatically sent at 9pm every day
- ✅ **Multiple Workers**: Support for multiple workers per farm
- ✅ **Task Overview**: Today's and tomorrow's tasks for each house
- ✅ **Beautiful Templates**: HTML and plain text email templates
- ✅ **Email Tracking**: Track sent emails and delivery status
- ✅ **Test Emails**: Send test emails to verify configuration
- ✅ **Admin Interface**: Manage workers through Django admin

## Quick Setup

### 1. Configure Email Settings
Create a `.env` file in the project root with your email configuration:

```bash
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 2. Add Workers to Farms
1. Go to Django Admin: `http://localhost:8000/admin/`
2. Navigate to **Farms** → **Workers**
3. Add workers with their email addresses
4. Ensure `receive_daily_tasks` is checked

### 3. Set Up Daily Email Schedule

#### Option A: Using Cron (Recommended for Production)
```bash
# Run the setup script
./setup_email_cron.sh

# Or manually add to crontab
crontab -e
# Add this line:
0 21 * * * cd /path/to/chicken_house_management && docker-compose exec backend python manage.py send_daily_tasks
```

#### Option B: Using Docker Compose Scheduler
```bash
# Use the email-enabled docker-compose file
docker-compose -f docker-compose.email.yml up -d
```

## Email Configuration Details

### Gmail Setup
1. **Enable 2-Factor Authentication** on your Google account
2. **Generate App Password**:
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
   - Use this password as `EMAIL_HOST_PASSWORD`

### Other Email Providers
- **Outlook/Hotmail**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **Custom SMTP**: Use your provider's SMTP settings

## Testing Email Functionality

### 1. Test Email Configuration
```bash
# Test with a specific farm and email
docker-compose exec backend python manage.py send_daily_tasks \
  --test \
  --farm-id 1 \
  --test-email your-email@example.com
```

### 2. Send Test Email via API
```bash
curl -X POST http://localhost:8000/api/tasks/send-test-email/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "farm_id": 1,
    "test_email": "your-email@example.com"
  }'
```

### 3. Manually Trigger Daily Emails
```bash
# Send emails to all farms right now
docker-compose exec backend python manage.py send_daily_tasks
```

## Email Templates

### HTML Template Features
- 🎨 **Modern Design**: Clean, professional layout
- 📊 **Task Summary**: Overview of total tasks and houses
- 🏠 **House Sections**: Individual house task breakdowns
- 🔥 **Today's Tasks**: Highlighted in orange
- 📅 **Tomorrow's Tasks**: Highlighted in blue
- 📱 **Responsive**: Works on mobile and desktop

### Plain Text Template
- Simple, readable format for all email clients
- Same information as HTML version
- Compatible with all email systems

## API Endpoints

### Send Test Email
```http
POST /api/tasks/send-test-email/
Content-Type: application/json
Authorization: Token YOUR_TOKEN

{
  "farm_id": 1,
  "test_email": "test@example.com"
}
```

### Send Daily Tasks
```http
POST /api/tasks/send-daily-tasks/
Authorization: Token YOUR_TOKEN
```

### Email History
```http
GET /api/tasks/email-history/
GET /api/tasks/email-history/?farm_id=1
Authorization: Token YOUR_TOKEN
```

### Worker Management
```http
# Get workers for a farm
GET /api/farms/1/workers/

# Create worker
POST /api/workers/
{
  "farm_id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "555-0123",
  "role": "Manager",
  "receive_daily_tasks": true
}
```

## Worker Management

### Adding Workers
1. **Via Admin Interface**:
   - Go to `http://localhost:8000/admin/farms/worker/`
   - Click "Add Worker"
   - Fill in details and select farm

2. **Via API**:
   ```bash
   curl -X POST http://localhost:8000/api/workers/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Token YOUR_TOKEN" \
     -d '{
       "farm_id": 1,
       "name": "Jane Smith",
       "email": "jane@example.com",
       "phone": "555-0124",
       "role": "Supervisor",
       "receive_daily_tasks": true
     }'
   ```

### Worker Fields
- **Name**: Worker's full name
- **Email**: Email address for notifications
- **Phone**: Contact phone number (optional)
- **Role**: Job title/position (optional)
- **Is Active**: Whether worker is currently active
- **Receive Daily Tasks**: Whether to send daily email reminders

## Email Content

### Daily Email Includes
- **Farm Name** and date
- **Task Summary**: Total houses, tasks, today's tasks
- **Per House Breakdown**:
  - House number and current day
  - House status (setup, growth, etc.)
  - Today's tasks (urgent, highlighted)
  - Tomorrow's tasks (upcoming, highlighted)
  - Task descriptions and types

### Task Categories
- **Setup Tasks**: House preparation (Day -1)
- **Daily Care**: Regular maintenance tasks
- **Health Checks**: Monitoring and health tasks
- **Feeding**: Feed management tasks
- **Water Management**: Water system tasks
- **Equipment**: Equipment maintenance tasks

## Troubleshooting

### Common Issues

#### 1. Email Not Sending
```bash
# Check email configuration
docker-compose exec backend python manage.py shell -c "
from django.conf import settings
print('EMAIL_HOST:', settings.EMAIL_HOST)
print('EMAIL_PORT:', settings.EMAIL_PORT)
print('EMAIL_USE_TLS:', settings.EMAIL_USE_TLS)
"
```

#### 2. Authentication Errors
- Verify email credentials
- Check if 2FA is enabled (use app password)
- Ensure SMTP settings are correct

#### 3. No Workers Found
```bash
# Check if workers exist
docker-compose exec backend python manage.py shell -c "
from farms.models import Worker
print('Total workers:', Worker.objects.count())
print('Active workers:', Worker.objects.filter(is_active=True).count())
print('Workers with daily tasks:', Worker.objects.filter(receive_daily_tasks=True).count())
"
```

#### 4. No Tasks Found
```bash
# Check if tasks exist for houses
docker-compose exec backend python manage.py shell -c "
from houses.models import House
from tasks.models import Task
houses = House.objects.filter(is_active=True)
for house in houses:
    tasks = Task.objects.filter(house=house, is_completed=False)
    print(f'House {house.house_number}: {tasks.count()} pending tasks')
"
```

### Logs
Check email sending logs:
```bash
# View Django logs
docker-compose exec backend tail -f logs/django.log

# View container logs
docker-compose logs backend
```

## Production Deployment

### Environment Variables
Set these in your production environment:
```bash
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-production-email@domain.com
EMAIL_HOST_PASSWORD=your-secure-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### Cron Job Setup
```bash
# Add to production server crontab
0 21 * * * cd /path/to/production && docker-compose exec backend python manage.py send_daily_tasks >> /var/log/daily-tasks.log 2>&1
```

### Monitoring
- Set up log monitoring for email failures
- Monitor cron job execution
- Track email delivery rates
- Set up alerts for failed email sends

## Security Considerations

- **Email Credentials**: Store securely, never commit to version control
- **App Passwords**: Use app-specific passwords, not main account passwords
- **Rate Limiting**: Be aware of email provider rate limits
- **Bounce Handling**: Monitor for bounced emails and invalid addresses
- **Privacy**: Ensure worker email addresses are handled securely

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Django logs for error messages
3. Test email configuration with test emails
4. Verify worker and task data in the admin interface

---

**🎉 Your daily task email system is now ready! Workers will receive beautiful, informative emails every day at 9pm with their tasks for today and tomorrow.**
