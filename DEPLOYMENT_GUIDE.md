# Vercel Deployment Guide for React SPA

## ✅ Simplified Configuration

Your Vercel deployment has been simplified and optimized for React SPA routing.

### Configuration Files

#### Root `vercel.json` (Main Configuration)
```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/build",
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

#### Frontend `vercel.json` (Backup Configuration)
```json
{
  "rewrites": [
    {
      "source": "/(.*)",
      "destination": "/index.html"
    }
  ]
}
```

## 🚀 Deployment Steps

### Option 1: Deploy via Vercel Dashboard (Recommended)

1. **Push to GitHub/GitLab/Bitbucket**
   ```bash
   git add .
   git commit -m "Ready for Vercel deployment"
   git push origin main
   ```

2. **Connect to Vercel**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your repository
   - Vercel will auto-detect the configuration

3. **Deploy**
   - Vercel will automatically build and deploy
   - Your app will be available at `https://your-project.vercel.app`

### Option 2: Deploy via Vercel CLI

1. **Install Vercel CLI**
   ```bash
   npm install -g vercel
   ```

2. **Login to Vercel**
   ```bash
   vercel login
   ```

3. **Deploy from Project Root**
   ```bash
   cd /Users/phuc.le/personal/project/chicken_house_management
   vercel
   ```

4. **Follow Prompts**
   - Set up project name
   - Choose framework: Other
   - Build command: `cd frontend && npm run build`
   - Output directory: `frontend/build`

## 🔧 How It Works

### SPA Routing Support
The `rewrites` configuration ensures:
- All routes (`/`, `/farms`, `/programs`, etc.) serve `index.html`
- React Router handles client-side navigation
- No 404 errors on direct URL access or page refresh

### Build Process
1. Vercel runs `cd frontend && npm run build`
2. Builds React app in `frontend/build`
3. Serves static files with SPA routing

### Performance Optimizations
- Static files are cached appropriately
- React app is optimized for production
- Bundle size: ~196kB gzipped

## ✅ Verification Checklist

After deployment, test these routes:
- [ ] `/` - Dashboard loads
- [ ] `/farms` - Farm list loads
- [ ] `/farms/1` - Farm detail loads
- [ ] `/programs` - Program manager loads
- [ ] `/farms/1/workers` - Worker list loads
- [ ] Direct URL access works (no 404s)
- [ ] Page refresh works on any route
- [ ] Browser back/forward buttons work

## 🐛 Troubleshooting

### Common Issues

1. **404 on Direct URL Access**
   - Ensure `vercel.json` has the rewrite rule
   - Check that `outputDirectory` points to correct build folder

2. **Build Failures**
   - Check Node.js version (requires >=18.0.0)
   - Ensure all dependencies are in `package.json`
   - Check build logs in Vercel dashboard

3. **Routing Issues**
   - Verify React Router is properly configured
   - Check that all routes are defined in your app

### Environment Variables
If you need environment variables:
1. Go to Vercel Dashboard → Project Settings → Environment Variables
2. Add variables like `REACT_APP_API_URL`
3. Redeploy the project

## 📊 Performance

- **Build Time**: ~2-3 minutes
- **Bundle Size**: 196kB gzipped
- **First Load**: Optimized with code splitting
- **Caching**: Static assets cached for 1 year

## 🔄 Continuous Deployment

Once connected to Git:
- Every push to `main` branch triggers automatic deployment
- Preview deployments for pull requests
- Rollback to previous versions if needed

---

**Your React SPA is now ready for production deployment on Vercel! 🎉**
