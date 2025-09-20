# 🚀 Separate Frontend & Backend Deployment Guide

This guide shows how to deploy the Chicken House Management System with separate frontend and backend services.

## 📋 Overview

- **Backend**: Django API deployed to Railway with PostgreSQL
- **Frontend**: React SPA deployed to Railway (or Vercel/Netlify)
- **Benefits**: Clean separation, independent scaling, proper static file serving

## 🔧 Prerequisites

- Railway account
- Git repository
- Node.js and Python installed locally

## 🚀 Deployment Steps

### Step 1: Deploy Backend (Django API)

1. **Deploy to Railway:**
   ```bash
   # From project root
   ./deploy-backend.sh
   ```

2. **Set Environment Variables in Railway:**
   - `SECRET_KEY`: Generate with `python -c "import secrets; print(secrets.token_urlsafe(50))"`
   - `DATABASE_URL`: Auto-provided by Railway PostgreSQL
   - `CORS_ALLOWED_ORIGINS`: Your frontend URL (e.g., `https://your-frontend.railway.app`)

3. **Verify Backend:**
   ```bash
   curl https://your-backend.railway.app/api/health/
   ```

### Step 2: Deploy Frontend (React SPA)

#### Option A: Railway Deployment

1. **Deploy to Railway:**
   ```bash
   # From project root
   ./deploy-frontend.sh
   ```

2. **Set Environment Variables in Railway:**
   - `REACT_APP_API_URL`: Your backend URL (e.g., `https://your-backend.railway.app/api`)

#### Option B: Vercel Deployment

1. **Connect to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Import your Git repository
   - Set root directory to `frontend/`

2. **Set Environment Variables:**
   - `REACT_APP_API_URL`: Your backend URL

3. **Deploy:**
   - Vercel will automatically deploy on every push

#### Option C: Netlify Deployment

1. **Connect to Netlify:**
   - Go to [netlify.com](https://netlify.com)
   - Connect your Git repository
   - Set build command: `cd frontend && npm run build`
   - Set publish directory: `frontend/build`

2. **Set Environment Variables:**
   - `REACT_APP_API_URL`: Your backend URL

## 🔗 Configuration

### Backend CORS Settings

The backend is configured to allow requests from:
- `http://localhost:3000` (local development)
- `https://*.railway.app` (Railway deployments)
- `https://*.vercel.app` (Vercel deployments)
- `https://*.netlify.app` (Netlify deployments)

### Frontend API Configuration

The frontend automatically detects the environment:
- **Development**: `http://localhost:8000/api`
- **Production**: Uses `REACT_APP_API_URL` environment variable

## 🧪 Testing

### Test Backend API
```bash
curl https://your-backend.railway.app/api/health/
```

### Test Frontend
1. Visit your frontend URL
2. Check browser console for API calls
3. Verify CORS is working

## 🔧 Development

### Local Development
```bash
# Terminal 1: Backend
cd backend
python manage.py runserver

# Terminal 2: Frontend
cd frontend
npm start
```

### Environment Variables
Create `.env.local` in frontend directory:
```
REACT_APP_API_URL=http://localhost:8000/api
```

## 📊 Monitoring

### Backend Monitoring
- Railway dashboard shows logs and metrics
- Health check endpoint: `/api/health/`

### Frontend Monitoring
- Railway/Vercel/Netlify dashboards
- Browser developer tools for API calls

## 🚨 Troubleshooting

### CORS Issues
- Check `CORS_ALLOWED_ORIGINS` in backend
- Verify frontend URL is in allowed origins

### API Connection Issues
- Check `REACT_APP_API_URL` environment variable
- Verify backend is running and accessible

### Static File Issues
- Frontend is served as SPA, no Django static file issues
- Check build process and deployment logs

## 🔄 Updates

### Backend Updates
```bash
git add .
git commit -m "Backend update"
git push
# Railway auto-deploys
```

### Frontend Updates
```bash
git add .
git commit -m "Frontend update"
git push
# Railway/Vercel/Netlify auto-deploys
```

## 💡 Benefits of This Approach

1. **Clean Separation**: Frontend and backend are independent
2. **Proper Static Serving**: No Django static file complications
3. **Independent Scaling**: Scale frontend and backend separately
4. **Better Caching**: CDN can cache static files properly
5. **Easier Debugging**: Clear separation of concerns
6. **Multiple Frontend Options**: Can deploy to different platforms

## 🎯 Next Steps

1. Deploy backend to Railway
2. Deploy frontend to your chosen platform
3. Configure environment variables
4. Test the full application
5. Set up monitoring and alerts
