#!/bin/bash

# 📧 Email Setup Script for Chicken House Management
# This script helps you set up email for both local development and Railway deployment

echo "🐔 Chicken House Management - Email Setup"
echo "========================================"

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Email Configuration for Local Development
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password
DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com

# Optional: Set DEBUG=False to use real SMTP instead of console
DEBUG=False
EOF
    echo "✅ Created .env file with email configuration"
    echo "📝 Please edit .env file with your actual email credentials"
else
    echo "✅ .env file already exists"
fi

echo ""
echo "🔧 Next Steps:"
echo "1. Edit .env file with your email credentials"
echo "2. Run: docker-compose down && docker-compose up -d"
echo "3. Test email: curl 'http://localhost:8000/api/tasks/send-test-email/' -H 'Authorization: Token YOUR_TOKEN' -H 'Content-Type: application/json' --data-raw '{\"farm_id\":1,\"test_email\":\"your-email@gmail.com\"}'"
echo ""
echo "🚀 For Railway deployment:"
echo "1. Go to Railway dashboard → Variables"
echo "2. Add the same email variables from .env file"
echo "3. Deploy your application"
echo ""
echo "📚 For detailed instructions, see EMAIL_SETUP_COMPLETE.md"
