#!/bin/bash

# Frontend Deployment Helper Script for Vercel
echo "🚀 Frontend Deployment Helper for Vercel"
echo "========================================"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "📦 Installing Vercel CLI..."
    npm install -g vercel
fi

# Check if user is logged in
if ! vercel whoami &> /dev/null; then
    echo "🔐 Please log in to Vercel..."
    vercel login
fi

# Navigate to frontend directory
cd frontend

echo "🔧 Frontend deployment configuration:"
echo "   - Root Directory: frontend/"
echo "   - Build Command: npm run build"
echo "   - Output Directory: build"
echo ""

# Check if .vercel directory exists (project is linked)
if [ ! -d ".vercel" ]; then
    echo "🔗 Linking to Vercel project..."
    vercel link
fi

# Deploy to Vercel
echo "🚀 Deploying frontend to Vercel..."
vercel --prod

echo ""
echo "✅ Frontend deployment initiated!"
echo ""
echo "📋 Next steps:"
echo "1. Set environment variable in Vercel dashboard:"
echo "   REACT_APP_API_URL=https://your-backend.railway.app/api"
echo ""
echo "2. Update backend CORS settings in Railway:"
echo "   CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app"
echo "   CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app"
echo ""
echo "3. Test your deployment:"
echo "   - Visit your Vercel URL"
echo "   - Try logging in with admin/admin123"
echo "   - Check browser console for any errors"
echo ""
echo "📚 For detailed instructions, see VERCEL_DEPLOYMENT.md"
