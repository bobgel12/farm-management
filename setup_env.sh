#!/bin/bash

# Setup Environment Configuration
# This script helps you set up the .env file for email configuration

echo "🐔 Setting up Environment Configuration..."

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists!"
    echo "📋 Current .env file contents:"
    echo "----------------------------------------"
    head -20 .env
    echo "----------------------------------------"
    echo ""
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Setup cancelled. .env file not modified."
        exit 0
    fi
fi

# Copy example to .env
if [ -f "env.example" ]; then
    cp env.example .env
    echo "✅ Created .env file from env.example"
    echo ""
    echo "📧 Next steps:"
    echo "1. Edit .env file with your email configuration"
    echo "2. Choose your email provider (Gmail, Outlook, Yahoo, or Custom SMTP)"
    echo "3. Update the email settings in .env"
    echo "4. Test your configuration with:"
    echo "   docker-compose exec backend python manage.py send_daily_tasks --test --farm-id 1 --test-email your-email@example.com"
    echo ""
    echo "📚 For detailed setup instructions, see EMAIL_SETUP.md"
    echo ""
    echo "🔧 Quick Gmail setup:"
    echo "1. Enable 2FA on your Google account"
    echo "2. Generate an app password: https://myaccount.google.com/apppasswords"
    echo "3. Update these lines in .env:"
    echo "   EMAIL_HOST_USER=your-email@gmail.com"
    echo "   EMAIL_HOST_PASSWORD=your-16-character-app-password"
    echo ""
    echo "📝 Edit .env file now? (y/N): "
    read -p "" -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v nano &> /dev/null; then
            nano .env
        elif command -v vim &> /dev/null; then
            vim .env
        elif command -v vi &> /dev/null; then
            vi .env
        else
            echo "📝 Please edit .env file manually with your preferred editor"
        fi
    fi
else
    echo "❌ env.example file not found!"
    echo "💡 Make sure you're in the project root directory"
    exit 1
fi

echo ""
echo "🎉 Environment setup complete!"
echo "📧 Don't forget to test your email configuration!"
