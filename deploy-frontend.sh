#!/bin/bash

# Deploy Frontend to Railway
echo "🚀 Deploying Frontend to Railway..."

# Check if we're in the right directory
if [ ! -f "frontend/package.json" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build the project
echo "🔨 Building React app..."
npm run build

# Deploy to Railway
echo "🚀 Deploying to Railway..."
railway up --service frontend

echo "✅ Frontend deployment initiated!"
echo "🔗 Check your Railway dashboard for deployment status"
echo "📝 Don't forget to set environment variables:"
echo "   - REACT_APP_API_URL (your backend API URL)"
