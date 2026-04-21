# Phase 1 API Contract (Auth + Farms + Houses + Alerts)

This contract is the baseline for the migrated iOS app.

## Auth

- `POST /api/auth/login/`
  - Request: `{ "username": "...", "password": "..." }`
  - Response: `{ "token": "...", "user": { "id": 1, "username": "...", "email": "...", "is_staff": true } }`
- `GET /api/auth/user/`
  - Header: `Authorization: Token <token>`
  - Response: `{ "user": { ... } }`
- `POST /api/auth/logout/`
  - Header: `Authorization: Token <token>`

## Farms

- `GET /api/farms/`
  - Header: `Authorization: Token <token>`
  - Response shape may be array or paginated object with `results`.
  - Fields used by iOS:
    - `id`
    - `name`
    - `total_houses`
    - `active_houses`

## Houses

- `GET /api/farms/{farm_id}/houses/`
  - Header: `Authorization: Token <token>`
  - Fields used by iOS:
    - `id`
    - `house_number`
    - `current_day` (fallback to `current_age_days`)
    - `is_active`
- `GET /api/houses/{house_id}/monitoring/latest/`
  - Header: `Authorization: Token <token>`
  - Fields used by iOS:
    - `average_temperature`
    - `humidity`
    - `static_pressure`
    - `water_consumption`
    - `feed_consumption`
    - `airflow_percentage`

## Alerts (water-alert lifecycle for Phase 1)

- `GET /api/houses/{house_id}/water/alerts/?include_resolved=true`
  - Header: `Authorization: Token <token>`
  - Response shape can be array or object with `results`.
  - Fields used by iOS:
    - `id`
    - `severity`
    - `message`
    - `house_number`
    - `created_at`
    - `is_acknowledged`
    - `increase_percentage`
- `POST /api/houses/water/alerts/{alert_id}/acknowledge/`
- `POST /api/houses/water/alerts/{alert_id}/snooze/` with body `{ "hours": 6 }`

## Normalization rules in iOS

- IDs from backend (`Int`) are converted to stable app UUIDs for SwiftUI identity.
- Collections are decoded from either:
  - raw array response, or
  - paginated object with `results`.
- If live endpoints fail, app keeps mock fallback data rather than blank screens.
