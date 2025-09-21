# 🚀 Vercel Frontend Deployment Guide

## Prerequisites

- GitHub repository with your code
- Railway backend deployed and running
- Vercel account (free at [vercel.com](https://vercel.com))

## Step 1: Deploy to Vercel

### 1.1 Connect Repository
1. Go to [vercel.com](https://vercel.com)
2. Sign in with GitHub
3. Click "New Project"
4. Select your GitHub repository

### 1.2 Configure Project
1. **Framework Preset**: Create React App
2. **Root Directory**: `frontend`
3. **Build Command**: `npm run build`
4. **Output Directory**: `build`
5. **Install Command**: `npm install`

### 1.3 Set Environment Variables
In the Vercel dashboard, go to Settings → Environment Variables and add:

```bash
REACT_APP_API_URL=https://your-backend.railway.app/api
```

**Important**: Replace `your-backend.railway.app` with your actual Railway backend URL.

### 1.4 Deploy
Click "Deploy" and wait for the build to complete.

## Step 2: Configure Backend CORS

### 2.1 Update Railway Environment Variables
In your Railway backend dashboard, add these environment variables:

```bash
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app
```

Replace `your-frontend.vercel.app` with your actual Vercel URL.

### 2.2 Restart Backend
After adding the CORS variables, restart your Railway backend service.

## Step 3: Test the Deployment

### 3.1 Test Frontend
1. Visit your Vercel URL
2. Open browser developer tools (F12)
3. Check the console for API configuration logs
4. Try logging in with admin/admin123

### 3.2 Debug API Connection
If login fails, check:
1. **Console logs**: Look for API configuration and error messages
2. **Network tab**: Check if API calls are being made to the correct URL
3. **CORS errors**: Look for CORS-related errors in the console

## Step 4: Enable Automatic Deployments

### 4.1 GitHub Integration
Vercel automatically deploys when you push to your main branch. To verify:

1. Go to Vercel dashboard
2. Click on your project
3. Go to "Settings" → "Git"
4. Ensure "Production Branch" is set to `main` (or your default branch)

### 4.2 Test Automatic Deployment
1. Make a small change to your frontend code
2. Commit and push to GitHub
3. Check Vercel dashboard - you should see a new deployment starting automatically

## Troubleshooting

### Common Issues

#### 1. API URL Not Set
**Error**: `REACT_APP_API_URL not set in production`
**Solution**: Set the environment variable in Vercel dashboard

#### 2. CORS Errors
**Error**: `Access to fetch at 'https://...' from origin 'https://...' has been blocked by CORS policy`
**Solution**: Add your Vercel URL to Railway CORS settings

#### 3. Login Not Working
**Check**:
- API URL is correct in Vercel environment variables
- Backend is running and accessible
- CORS is properly configured
- Check browser console for errors

#### 4. Build Failures
**Check**:
- Node.js version compatibility
- Dependencies are properly installed
- Build command is correct

### Debug Commands

#### Check API Configuration
```javascript
// In browser console
console.log('API URL:', process.env.REACT_APP_API_URL);
console.log('NODE_ENV:', process.env.NODE_ENV);
```

#### Test API Connection
```javascript
// In browser console
fetch('https://your-backend.railway.app/api/health/')
  .then(response => response.json())
  .then(data => console.log('API Response:', data))
  .catch(error => console.error('API Error:', error));
```

## Environment Variables Reference

### Required in Vercel
```bash
REACT_APP_API_URL=https://your-backend.railway.app/api
```

### Required in Railway (Backend)
```bash
CORS_ALLOWED_ORIGINS=https://your-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-frontend.vercel.app
```

## URLs After Deployment

- **Frontend**: `https://your-app.vercel.app`
- **Backend API**: `https://your-backend.railway.app/api`
- **Admin Panel**: `https://your-backend.railway.app/admin`

## Success Checklist

- [ ] Frontend deployed to Vercel
- [ ] Environment variable `REACT_APP_API_URL` set
- [ ] Backend CORS configured with Vercel URL
- [ ] Login functionality working
- [ ] Automatic deployments enabled
- [ ] All features tested

## Next Steps

1. **Custom Domain** (Optional): Configure a custom domain in Vercel
2. **Analytics**: Enable Vercel Analytics for performance monitoring
3. **Preview Deployments**: Use Vercel's preview deployments for testing
4. **Environment Management**: Set up different environments (staging, production)

Your frontend is now live and automatically deploying on every GitHub push! 🎉
