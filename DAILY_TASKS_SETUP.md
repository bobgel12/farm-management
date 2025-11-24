# Daily Tasks Setup Guide

This guide explains how to set up and configure daily automated tasks for the Chicken House Management System.

## Overview

The system supports two main daily tasks:
1. **Daily Task Email Reminders** - Sends task reminders to farm workers
2. **Daily Rotem Data Collection** - Collects and aggregates sensor data from Rotem API

## Task 1: Daily Task Email Reminders

### Purpose
Automatically send daily task reminder emails to farm workers who have opted in to receive them.

### Schedule
- **Default**: Daily at 9:00 PM (21:00) UTC
- **Configurable**: Via Railway cron or external cron service

### Setup Options

#### Option A: Railway Cron (Recommended for Railway deployments)

The cron job is configured in `railway.json`:

```json
{
  "cron": {
    "daily-tasks": {
      "schedule": "0 21 * * *",
      "command": "cd /app && python manage.py send_daily_tasks"
    }
  }
}
```

**Note**: Railway cron jobs may not always be reliable. If they don't work, use Option B.

#### Option B: External Cron Service (Recommended for reliability)

Use an external cron service like [cron-job.org](https://cron-job.org) or [EasyCron](https://www.easycron.com) to call the API endpoint.

**API Endpoint**: `POST /api/tasks/trigger-daily-emails/`

**Setup Steps**:
1. Sign up for a free cron service account
2. Create a new cron job with:
   - **URL**: `https://your-domain.com/api/tasks/trigger-daily-emails/`
   - **Method**: POST
   - **Schedule**: `0 21 * * *` (9 PM daily)
   - **Headers**: 
     - `Content-Type: application/json`
     - `X-Cron-Secret: your-secret-token` (optional, for security)

**Security (Optional)**:
To secure the endpoint, set `CRON_SECRET` in your environment variables and include it in the `X-Cron-Secret` header.

**Example curl command**:
```bash
curl -X POST https://your-domain.com/api/tasks/trigger-daily-emails/ \
  -H "Content-Type: application/json" \
  -H "X-Cron-Secret: your-secret-token" \
  -d '{"force": false}'
```

**Query Parameters**:
- `force`: Force resend even if already sent today (default: false)
- `farm_id`: Send for specific farm only (optional)

### Manual Testing

Test the email sending manually:

```bash
# Send emails for all farms
python manage.py send_daily_tasks

# Send for specific farm
python manage.py send_daily_tasks --farm-id 1

# Force resend (even if already sent today)
python manage.py send_daily_tasks --force

# Test email configuration
python manage.py send_daily_tasks --test --farm-id 1 --test-email your@email.com
```

### Troubleshooting

1. **Emails not sending**:
   - Check `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` are set in Railway
   - Verify SMTP settings in `settings_prod.py`
   - Check logs for error messages

2. **Cron job not running**:
   - Verify Railway cron configuration in `railway.json`
   - Check Railway logs for cron execution
   - Consider using external cron service (Option B)

3. **"No active workers found"**:
   - Ensure workers have `receive_daily_tasks=True` in the database
   - Verify workers are marked as `is_active=True`

## Task 2: Daily Rotem Data Collection

### Purpose
Collect sensor data from Rotem API daily and aggregate it for analytics and ML model training.

### Schedule
- **Default**: Daily at 2:00 AM (02:00) UTC
- **Configurable**: Via Railway cron or external cron service

### Setup Options

#### Option A: Railway Cron

Configured in `railway.json`:

```json
{
  "cron": {
    "daily-rotem-scrape": {
      "schedule": "0 2 * * *",
      "command": "cd /app && python manage.py collect_rotem_data_daily"
    }
  }
}
```

#### Option B: External Cron Service

**API Endpoint**: `POST /api/rotem/trigger-daily-scrape/`

**Setup Steps**:
1. Create a cron job with:
   - **URL**: `https://your-domain.com/api/rotem/trigger-daily-scrape/`
   - **Method**: POST
   - **Schedule**: `0 2 * * *` (2 AM daily)
   - **Headers**: 
     - `Content-Type: application/json`
     - `X-Cron-Secret: your-secret-token` (optional)

**Query Parameters**:
- `farm_id`: Collect data for specific farm only (optional)

**Example curl command**:
```bash
curl -X POST https://your-domain.com/api/rotem/trigger-daily-scrape/ \
  -H "Content-Type: application/json" \
  -H "X-Cron-Secret: your-secret-token"
```

### Manual Testing

Test data collection manually:

```bash
# Collect data for all active farms
python manage.py collect_rotem_data_daily

# Collect for specific farm
python manage.py collect_rotem_data_daily --farm-id farm123
```

### What It Does

1. **Data Collection**: 
   - Connects to Rotem API for each active farm
   - Collects sensor data (temperature, humidity, pressure, etc.)
   - Stores raw data points in `RotemDataPoint` model

2. **Data Aggregation**:
   - Automatically aggregates raw data into daily summaries
   - Creates `RotemDailySummary` records with:
     - Average, min, max values per data type
     - Anomaly counts
     - Total data points collected
   - Improves query performance for analytics
   - Reduces storage requirements

3. **ML Model Training**:
   - ML service automatically uses aggregated data when available
   - Falls back to raw data points if needed
   - More efficient training with aggregated summaries

## Data Aggregation

### Purpose
Aggregate raw sensor data points into daily summaries for:
- Faster analytics queries
- Efficient ML model training
- Reduced storage requirements
- Better performance for failure prediction

### Models

**RotemDailySummary**: Stores daily aggregated metrics per controller
- Temperature metrics (avg, min, max)
- Humidity metrics (avg, min, max)
- Static pressure metrics (avg, min, max)
- Wind speed metrics (avg, min, max)
- Water/feed consumption metrics (avg, min, max)
- Quality metrics (anomalies, warnings, errors count)

### Manual Aggregation

Aggregate existing data:

```bash
# Aggregate data for yesterday
python manage.py aggregate_rotem_data --date 2024-01-15

# Aggregate last 7 days
python manage.py aggregate_rotem_data --days 7

# Aggregate for specific controller
python manage.py aggregate_rotem_data --controller-id 123
```

## Environment Variables

Required environment variables for daily tasks:

```bash
# Email Configuration (for daily task emails)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@chickenmanagement.com

# Rotem API Credentials (for data collection)
ROTEM_USERNAME=your-rotem-username
ROTEM_PASSWORD=your-rotem-password

# Optional: Cron Security
CRON_SECRET=your-secret-token-for-cron-authentication
```

## Monitoring

### Check Task Execution

1. **Email Task Logs**:
   - Check `EmailTask` model in Django admin
   - View email history via API: `GET /api/tasks/email-history/`

2. **Data Collection Logs**:
   - Check `RotemScrapeLog` model in Django admin
   - View scrape logs via API: `GET /api/rotem/logs/`

3. **Aggregation Status**:
   - Check `RotemDailySummary` model in Django admin
   - Verify summaries are created daily

### Railway Logs

View Railway deployment logs:
```bash
railway logs
```

Or via Railway dashboard: Deployments → View Logs

## Troubleshooting

### Daily Emails Not Sending

1. **Check Email Configuration**:
   ```bash
   python manage.py send_daily_tasks --test --farm-id 1 --test-email your@email.com
   ```

2. **Verify Workers**:
   - Workers must have `receive_daily_tasks=True`
   - Workers must be `is_active=True`
   - Farm must have active houses with tasks

3. **Check Cron Execution**:
   - View Railway logs for cron job execution
   - Test API endpoint manually
   - Verify cron schedule in `railway.json`

### Data Collection Failing

1. **Check Rotem Credentials**:
   - Verify `ROTEM_USERNAME` and `ROTEM_PASSWORD` are set
   - Test credentials manually via scraper

2. **Check Network Connectivity**:
   - Ensure Railway can reach Rotem API
   - Check firewall rules if applicable

3. **View Scrape Logs**:
   ```bash
   # Via Django shell
   python manage.py shell
   >>> from rotem_scraper.models import RotemScrapeLog
   >>> RotemScrapeLog.objects.order_by('-started_at')[:5]
   ```

### Aggregation Not Working

1. **Check Data Points Exist**:
   - Verify `RotemDataPoint` records exist for the date
   - Check controller is active and connected

2. **Run Aggregation Manually**:
   ```bash
   python manage.py aggregate_rotem_data --date 2024-01-15
   ```

3. **Check for Errors**:
   - View Django logs for aggregation errors
   - Verify database permissions

## Best Practices

1. **Schedule Times**:
   - Email reminders: 9 PM (after work hours)
   - Data collection: 2 AM (low traffic time)

2. **Monitoring**:
   - Set up alerts for failed cron jobs
   - Monitor email delivery rates
   - Track data collection success rates

3. **Data Retention**:
   - Keep raw data points for 30-90 days
   - Keep daily summaries indefinitely
   - Archive old data if needed

4. **Security**:
   - Use `CRON_SECRET` for API endpoints
   - Rotate secrets periodically
   - Monitor API endpoint access logs

## Support

For issues or questions:
1. Check logs first
2. Test manually using management commands
3. Verify environment variables
4. Review this documentation

