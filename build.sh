#!/bin/bash

# Build script for Railway deployment
echo "🚀 Building Chicken House Management System..."

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm ci
npm run build
cd ..

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd backend
pip install -r requirements.txt
cd ..

echo "✅ Build complete!"
