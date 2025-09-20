# Railway Deployment Troubleshooting

## Common Railway Deployment Issues

### 1. Frontend Build Errors

#### Error: `npm ci --only=production` failed
**Problem**: Invalid npm command
**Solution**: Use `npm ci` instead of `npm ci --only=production`

#### Error: Frontend build fails
**Problem**: Missing dependencies or build issues
**Solutions**:
1. **Use Nixpacks instead of Docker**:
   ```bash
   # Use the build script method
   cp railway-build.json .railway.json
   railway up
   ```

2. **Check package.json**:
   ```bash
   # Ensure all dependencies are listed
   cd frontend
   npm install
   npm run build
   ```

3. **Use separate build steps**:
   ```bash
   # Build frontend first
   cd frontend
   npm ci
   npm run build
   
   # Then deploy
   railway up
   ```

### 2. Docker Build Errors

#### Error: `failed to solve: process did not complete successfully`
**Problem**: Docker build step failed
**Solutions**:
1. **Use Nixpacks instead**:
   ```bash
   cp railway-build.json .railway.json
   railway up
   ```

2. **Fix Dockerfile**:
   - Ensure all commands are valid
   - Check file paths and permissions
   - Use correct base images

3. **Test Docker locally**:
   ```bash
   docker build -t chicken-house .
   docker run -p 8000:8000 chicken-house
   ```

### 3. Database Connection Issues

#### Error: `OperationalError: no such table`
**Problem**: Database migrations not run
**Solution**:
```bash
railway run python manage.py migrate
```

#### Error: `psycopg2.OperationalError: could not connect to server`
**Problem**: Database not accessible
**Solutions**:
1. **Check DATABASE_URL**:
   ```bash
   railway run env | grep DATABASE_URL
   ```

2. **Verify database service**:
   - Go to Railway dashboard
   - Check if PostgreSQL service is running
   - Verify connection string

3. **Test connection**:
   ```bash
   railway run python manage.py dbshell
   ```

### 4. Environment Variable Issues

#### Error: `SECRET_KEY` not set
**Problem**: Missing environment variables
**Solution**:
1. **Set in Railway dashboard**:
   - Go to Variables tab
   - Add `SECRET_KEY=your-secret-key`
   - Add `DEBUG=False`

2. **Set via CLI**:
   ```bash
   railway variables set SECRET_KEY=your-secret-key
   railway variables set DEBUG=False
   ```

#### Error: Email not working
**Problem**: Email configuration missing
**Solution**:
```bash
railway variables set EMAIL_HOST=smtp.gmail.com
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True
railway variables set EMAIL_HOST_USER=your-email@gmail.com
railway variables set EMAIL_HOST_PASSWORD=your-app-password
railway variables set DEFAULT_FROM_EMAIL=noreply@yourdomain.com
```

### 5. Static Files Issues

#### Error: Static files not found
**Problem**: Static files not collected
**Solution**:
```bash
railway run python manage.py collectstatic --noinput
```

#### Error: WhiteNoise configuration
**Problem**: Static file serving issues
**Solution**: Ensure `whitenoise` is in requirements.txt and middleware is configured

### 6. Port and Health Check Issues

#### Error: Health check failed
**Problem**: App not responding on health check path
**Solutions**:
1. **Check health endpoint**:
   ```bash
   curl https://your-app.railway.app/api/health/
   ```

2. **Verify start command**:
   ```bash
   # Should be something like:
   python manage.py runserver 0.0.0.0:$PORT
   ```

3. **Check logs**:
   ```bash
   railway logs
   ```

## Deployment Methods

### Method 1: Nixpacks (Recommended)
```bash
# Use build script
cp railway-build.json .railway.json
railway up
```

**Pros**:
- Faster builds
- Automatic dependency detection
- Less configuration needed

**Cons**:
- Less control over build process
- May not work with complex setups

### Method 2: Docker
```bash
# Use Docker
cp railway.json .railway.json
railway up
```

**Pros**:
- Full control over build process
- Consistent environment
- Works with complex setups

**Cons**:
- Slower builds
- More configuration needed
- Can fail on build errors

### Method 3: Manual Build
```bash
# Build frontend first
cd frontend
npm ci
npm run build
cd ..

# Deploy backend
railway up
```

**Pros**:
- Full control
- Can debug build issues
- Works with any setup

**Cons**:
- Manual process
- Requires local build

## Debugging Commands

### Check Deployment Status
```bash
railway status
```

### View Logs
```bash
# All logs
railway logs

# Recent logs
railway logs --tail 50

# Follow logs
railway logs --follow
```

### Run Commands
```bash
# Run shell
railway run python manage.py shell

# Run migrations
railway run python manage.py migrate

# Create superuser
railway run python manage.py createsuperuser

# Check environment
railway run env
```

### Test Locally
```bash
# Test with Railway environment
railway run python manage.py runserver

# Test Docker build
docker build -t chicken-house .
docker run -p 8000:8000 chicken-house
```

## Environment Variables Checklist

### Required Variables
- [ ] `SECRET_KEY` - Django secret key
- [ ] `DATABASE_URL` - PostgreSQL connection string
- [ ] `DEBUG` - Set to `False` for production
- [ ] `ALLOWED_HOSTS` - Comma-separated list of allowed hosts

### Email Variables
- [ ] `EMAIL_HOST` - SMTP server (e.g., smtp.gmail.com)
- [ ] `EMAIL_PORT` - SMTP port (usually 587)
- [ ] `EMAIL_USE_TLS` - Set to `True`
- [ ] `EMAIL_HOST_USER` - Your email address
- [ ] `EMAIL_HOST_PASSWORD` - Your email password/app password
- [ ] `DEFAULT_FROM_EMAIL` - From email address

### Optional Variables
- [ ] `ADMIN_USERNAME` - Admin username
- [ ] `ADMIN_PASSWORD` - Admin password
- [ ] `ADMIN_EMAIL` - Admin email
- [ ] `CORS_ALLOWED_ORIGINS` - CORS origins
- [ ] `CSRF_TRUSTED_ORIGINS` - CSRF trusted origins

## Quick Fixes

### If Build Fails
1. Try Nixpacks method
2. Check package.json dependencies
3. Verify Node.js version
4. Test build locally

### If App Won't Start
1. Check environment variables
2. Run database migrations
3. Check start command
4. Verify port configuration

### If Database Issues
1. Check DATABASE_URL format
2. Verify PostgreSQL service is running
3. Run migrations
4. Check database permissions

### If Email Not Working
1. Verify SMTP credentials
2. Check email environment variables
3. Test with a simple email
4. Check email provider settings

## Getting Help

1. **Check Railway logs**: `railway logs`
2. **Test locally**: Build and run locally first
3. **Check Railway docs**: https://docs.railway.app
4. **Railway Discord**: https://discord.gg/railway
5. **GitHub Issues**: Check project repository

## Success Checklist

- [ ] App builds successfully
- [ ] App starts without errors
- [ ] Database migrations run
- [ ] Health check passes
- [ ] Admin panel accessible
- [ ] API endpoints working
- [ ] Email configuration working
- [ ] Static files served correctly
- [ ] Cron jobs scheduled
- [ ] Monitoring set up

---

**🎉 Once all items are checked, your Chicken House Management System should be running smoothly on Railway!**
