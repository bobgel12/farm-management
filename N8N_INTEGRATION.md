# n8n ↔ Farm Management Webapp Integration

This guide explains how to connect your Railway-hosted n8n instance with the farm-management webapp in both directions.

## Overview

| Direction | Flow |
|-----------|------|
| **Webapp → n8n** | User clicks "Run" in UI → Django API → n8n webhook URL |
| **n8n → Webapp** | n8n HTTP Request node → Django API (with `X-Cron-Secret`) |

Webhook URLs and secrets are stored on the backend only — never exposed to the browser.

---

## Environment Variables

Set these in **both** Railway projects (farm-management and n8n):

| Variable | Project | Purpose |
|----------|---------|---------|
| `CRON_SECRET` | farm-management | Validates inbound requests from n8n |
| `CRON_SECRET` | n8n | Used in HTTP Request node headers |
| `N8N_BASE_URL` | farm-management | Optional, documentation only |

Example (farm-management `.env` / Railway Variables):

```
CRON_SECRET=your-long-random-secret
N8N_BASE_URL=https://your-n8n.up.railway.app
```

---

## Webapp → n8n (Trigger from UI)

### 1. Create workflow in n8n

1. New workflow → add **Webhook** trigger node
2. HTTP Method: `POST`, Path: e.g. `/webhook/send-report`
3. **Activate** the workflow (production URL requires activation)
4. Copy the **Production URL**

### 2. Register workflow in webapp

**Option A — Organization Settings UI**

1. Go to **Organization Settings → Automations** tab (admin only)
2. Click **Add Workflow**
3. Fill in name, slug (`send_report`), and n8n webhook URL

**Option B — Django Admin**

Create an `AutomationWorkflow` row with organization, slug, and webhook URL.

### 3. Trigger from UI

- **Farm Dashboard** — quick-action buttons in the Houses toolbar
- **Integration Management dialog → Automations tab** — full list with Run/Test

### Payload sent to n8n

```json
{
  "workflow_slug": "send_report",
  "triggered_by_user_id": 12,
  "triggered_by_email": "user@farm.com",
  "organization_id": "uuid",
  "farm_id": 5,
  "farm_name": "North Farm",
  "timestamp": "2026-06-13T10:00:00Z",
  "payload": {}
}
```

Use in n8n expressions: `{{ $json.body.farm_id }}`, `{{ $json.body.triggered_by_email }}`, etc.

### API endpoints (Token auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/automations/` | List workflows (`?organization_id=&farm_id=`) |
| `POST` | `/api/automations/` | Create workflow (org admin) |
| `PATCH` | `/api/automations/{id}/` | Update workflow (org admin) |
| `DELETE` | `/api/automations/{id}/` | Delete workflow (org admin) |
| `POST` | `/api/automations/{slug}/trigger/` | Trigger workflow |
| `POST` | `/api/automations/{slug}/test/` | Test webhook (org admin) |

---

## n8n → Webapp (Trigger webapp actions)

### Option A — Unified dispatcher (recommended)

Single endpoint for all inbound actions:

```
POST https://your-farm-app.up.railway.app/api/webhooks/n8n/
Header: X-Cron-Secret: <CRON_SECRET>
Content-Type: application/json

{
  "action": "trigger_daily_emails",
  "farm_id": 5,
  "force": false
}
```

**Available actions:**

| action | Description |
|--------|-------------|
| `trigger_daily_emails` | Send daily task reminder emails |
| `trigger_daily_scrape` | Run Rotem data collection |
| `trigger_ml_analysis` | Start ML analysis (async Celery task) |
| `trigger_daily_report` | Generate daily report (async Celery task) |

### Option B — Direct cron endpoints

These existed before the unified dispatcher and still work:

| Action | Endpoint | Auth |
|--------|----------|------|
| Daily emails | `POST /api/tasks/trigger-daily-emails/` | `X-Cron-Secret` |
| Rotem scrape | `POST /api/rotem/trigger-daily-scrape/` | `X-Cron-Secret` |
| ML analysis | `POST /api/ml/trigger-analysis/` | `Authorization: Token <token>` |

### n8n HTTP Request node setup

1. Method: `POST`
2. URL: `https://your-farm-app.up.railway.app/api/webhooks/n8n/`
3. Headers:
   - `X-Cron-Secret`: `{{ $env.CRON_SECRET }}`
   - `Content-Type`: `application/json`
4. Body (JSON):
   ```json
   {
     "action": "trigger_daily_emails"
   }
   ```

---

## First end-to-end test

1. **n8n**: Create "Send Report" workflow with Webhook trigger → copy production URL
2. **farm-management Railway**: Set `CRON_SECRET`
3. **n8n Railway**: Set same `CRON_SECRET` as environment variable
4. **Webapp**: Organization Settings → Automations → Add workflow with slug `send_report`
5. **Webapp**: Farm Dashboard → click the workflow button
6. **n8n**: Check Executions tab — run should appear

---

## Security notes

- `CRON_SECRET` must be a long random string; reject requests when secret is set but header is wrong
- Workflow CRUD is restricted to organization admins (owner/admin roles)
- All user-facing triggers require Token authentication
- Trigger history is logged in `IntegrationLog` with `integration_type='n8n'`
