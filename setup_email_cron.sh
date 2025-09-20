#!/bin/bash

# Setup Daily Task Email Cron Job
# This script sets up a cron job to send daily task reminders at 9pm

echo "🐔 Setting up Daily Task Email Cron Job..."

# Check if running inside Docker container
if [ -f /.dockerenv ]; then
    echo "⚠️  Running inside Docker container. Cron setup for Docker requires additional configuration."
    echo "📋 Manual setup required:"
    echo "   1. Add this line to your host's crontab:"
    echo "      0 21 * * * docker-compose -f /path/to/chicken_house_management/docker-compose.yml exec backend python manage.py send_daily_tasks"
    echo "   2. Or use a task scheduler like systemd timers or cron on the host"
    echo ""
    echo "🔧 Alternative: Use Docker Compose with a scheduler service"
    echo "   Add this to your docker-compose.yml:"
    echo "   scheduler:"
    echo "     image: alpine:latest"
    echo "     volumes:"
    echo "       - ./:/app"
    echo "     command: sh -c 'apk add --no-cache dcron && echo \"0 21 * * * cd /app && docker-compose exec backend python manage.py send_daily_tasks\" | crontab - && crond -f'"
    exit 0
fi

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

echo "📁 Project directory: $PROJECT_DIR"

# Create the cron job command
CRON_COMMAND="cd $PROJECT_DIR && docker-compose exec backend python manage.py send_daily_tasks"

# Add the cron job (9pm daily)
echo "⏰ Adding cron job for 9pm daily task emails..."
(crontab -l 2>/dev/null; echo "0 21 * * * $CRON_COMMAND") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
    echo "📅 Daily task emails will be sent at 9:00 PM every day"
    echo ""
    echo "📋 Current crontab:"
    crontab -l | grep "send_daily_tasks" || echo "   (No matching cron jobs found)"
    echo ""
    echo "🔧 To test the email system:"
    echo "   cd $PROJECT_DIR"
    echo "   docker-compose exec backend python manage.py send_daily_tasks --test --farm-id 1 --test-email your-email@example.com"
    echo ""
    echo "📧 To configure email settings, set these environment variables:"
    echo "   EMAIL_HOST=smtp.gmail.com"
    echo "   EMAIL_PORT=587"
    echo "   EMAIL_USE_TLS=True"
    echo "   EMAIL_HOST_USER=your-email@gmail.com"
    echo "   EMAIL_HOST_PASSWORD=your-app-password"
    echo "   DEFAULT_FROM_EMAIL=noreply@yourdomain.com"
    echo ""
    echo "🛠️  To remove the cron job:"
    echo "   crontab -e"
    echo "   (Then delete the line with 'send_daily_tasks')"
else
    echo "❌ Failed to add cron job"
    echo "💡 Try running this script with appropriate permissions"
    exit 1
fi

echo ""
echo "🎉 Daily task email setup complete!"
echo "📚 For more information, see the email configuration in settings.py"
