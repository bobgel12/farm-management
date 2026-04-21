# Phase 2 API Contract (Flocks + Sensor History)

This contract extends Phase 1 with live flock and monitoring history wiring.

## Flocks

- `GET /api/flocks/?farm_id={farm_id}`
  - Header: `Authorization: Token <token>`
  - Response shape can be array or object with `results`.
  - Fields used by iOS:
    - `id`
    - `house`
    - `batch_number`
    - `breed_name` (or `breed.name`)
    - `arrival_date`
    - `expected_harvest_date`
    - `current_age_days`
    - `initial_chicken_count`
    - `current_chicken_count`
    - `is_active`
    - `status`
    - `mortality_rate`

- `GET /api/flocks/{flock_id}/`
  - Header: `Authorization: Token <token>`
  - Used for future detail enrichment.

- `GET /api/flocks/{flock_id}/performance/`
  - Header: `Authorization: Token <token>`
  - Response shape can be array or object with `results`.
  - Fields used by iOS:
    - `record_date`
    - `flock_age_days`
    - `average_weight_grams`
    - `feed_conversion_ratio`
    - `daily_feed_consumption_kg`
    - `daily_water_consumption_liters`
    - `mortality_rate`
    - `livability`

## Sensor history

- `GET /api/houses/{house_id}/monitoring/history/?limit={N}`
  - Header: `Authorization: Token <token>`
  - Returns object with `results` list.
  - Timestamp source in each item:
    - Prefer `source_timestamp`
    - Fallback to `timestamp`
  - Metric fields currently consumed by iOS:
    - `average_temperature`
    - `humidity`
    - `static_pressure`
    - `airflow_percentage`

## Date parsing in iOS

- iOS supports:
  - ISO8601 with fractional seconds
  - ISO8601 without fractional seconds
  - `yyyy-MM-dd` date-only values

## Backend access control notes

- Flock endpoints should require authenticated access and organization-scoped data.
- Non-staff users should only read data for organizations they belong to.

## Device/LAN note

- For physical iPhone testing, point `ROTEM_API_BASE_URL` to host LAN IP and mapped port:
  - Example: `http://192.168.1.50:8002`
- Ensure Django `ALLOWED_HOSTS` (and any proxy) allow that host/IP.
