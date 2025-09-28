# Rotem Scraper Setup Guide

## 🎯 Overview

The Rotem scraper automatically collects data from the RotemNetWeb platform every 5 minutes and performs ML analysis on the collected data. This guide will help you set up the credentials and test the system.

## 🔧 Setup Instructions

### 1. Local Development Setup

#### Step 1: Create Environment File
```bash
# Copy the example environment file
cp env.example .env

# Edit the .env file and add your Rotem credentials
nano .env
```

#### Step 2: Add Rotem Credentials
Add these lines to your `.env` file:
```bash
ROTEM_USERNAME=your-actual-rotem-username
ROTEM_PASSWORD=your-actual-rotem-password
```

#### Step 3: Start the System
```bash
# Start all services
make up

# Or start development environment
make dev
```

#### Step 4: Test the Scraper
```bash
# Test the Rotem scraper
make rotem-test
```

### 2. Railway Production Setup

#### Step 1: Add Environment Variables
In your Railway project dashboard:
1. Go to Variables tab
2. Add the following variables:
   - `ROTEM_USERNAME` = your-rotem-username
   - `ROTEM_PASSWORD` = your-rotem-password

#### Step 2: Deploy
```bash
# Deploy to Railway
make deploy-railway
```

## 🧪 Testing Commands

### Available Make Commands

```bash
# Setup Rotem credentials (creates .env if needed)
make rotem-setup

# Test the Rotem scraper
make rotem-test

# View Rotem scraper logs
make rotem-logs

# Show all available commands
make help-rotem
```

### Manual Testing

```bash
# Test scraper directly
docker-compose exec backend python manage.py test_scraper

# Check scraper logs
docker-compose logs backend | grep -i rotem

# View collected data in Django admin
# Visit: http://localhost:8002/admin/
```

## 📊 Data Collection

### What Gets Collected
- **Farm Information**: Farm details, gateway information
- **User Information**: User accounts and permissions
- **Controller Data**: Hardware controllers and their status
- **Sensor Data**: Temperature, humidity, pressure readings
- **ML Predictions**: Anomaly detection, failure predictions, optimizations

### Collection Schedule
- **Data Scraping**: Every 5 minutes
- **ML Analysis**: Every hour
- **Data Retention**: 1 year of historical data

## 🔍 Monitoring

### Check Scraper Status
```bash
# View recent scrape logs
docker-compose exec backend python manage.py shell
>>> from rotem_scraper.models import RotemScrapeLog
>>> RotemScrapeLog.objects.order_by('-started_at')[:5]
```

### View Collected Data
```bash
# Check data points
docker-compose exec backend python manage.py shell
>>> from rotem_scraper.models import RotemDataPoint
>>> RotemDataPoint.objects.count()
```

### API Endpoints
- `/api/rotem/data/` - Raw data points
- `/api/rotem/predictions/` - ML predictions
- `/api/rotem/controllers/` - Controller information
- `/api/rotem/farms/` - Farm information

## 🚨 Troubleshooting

### Common Issues

#### 1. "Invalid username or password"
- Check your Rotem credentials in `.env` file
- Verify credentials work on RotemNetWeb website
- Ensure no extra spaces in username/password

#### 2. "Module not found" errors
- Rebuild Docker containers: `make build`
- Restart services: `make restart`

#### 3. No data being collected
- Check scraper logs: `make rotem-logs`
- Verify credentials are correct
- Check if RotemNetWeb is accessible

#### 4. Celery tasks not running
- Ensure Redis is running: `docker-compose ps`
- Check Celery worker logs: `docker-compose logs backend`

### Debug Commands

```bash
# Check environment variables
docker-compose exec backend python -c "from django.conf import settings; print('ROTEM_USERNAME:', settings.ROTEM_USERNAME)"

# Test database connection
docker-compose exec backend python manage.py dbshell

# Check Celery status
docker-compose exec backend celery -A chicken_management inspect active
```

## 📈 Performance Monitoring

### Key Metrics
- **Scraping Success Rate**: Should be 99%+
- **Data Processing Time**: <30 seconds
- **ML Analysis Time**: <2 minutes
- **API Response Time**: <200ms

### Log Files
- Django logs: `logs/django.log`
- Rotem scraper logs: Available in Docker logs
- Celery logs: Available in Docker logs

## 🔐 Security Notes

- Never commit `.env` file to version control
- Use strong, unique passwords for Rotem account
- Rotate credentials regularly
- Monitor scraping logs for suspicious activity
- Use environment variables in production

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review the logs: `make rotem-logs`
3. Test credentials manually on RotemNetWeb
4. Verify all services are running: `make status`

## 🎉 Success Indicators

You'll know the system is working when:
- ✅ `make rotem-test` shows successful data collection
- ✅ Data appears in Django admin at `/admin/`
- ✅ API endpoints return data
- ✅ No errors in logs
- ✅ Celery tasks are running automatically
