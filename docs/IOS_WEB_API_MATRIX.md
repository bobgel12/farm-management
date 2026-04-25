# iOS vs Web API matrix and load-time notes

This document maps **which client calls which Django routes**, **query parameters** (`mode`, cache bust), and **when** calls typically fire. Use it for parity debugging and performance work.

## Production base URL alignment

| Client | Default production API base | Notes |
|--------|----------------------------|--------|
| Web (`frontend/src/services/api.ts`) | `https://farm-management-production-54e4.up.railway.app/api` | Falls back to this when `REACT_APP_API_URL` is unset in production builds. |
| iOS (`APIClient` `APIEnvironment.prod`) | `https://farm-management-production-54e4.up.railway.app` | Paths include `/api/...`; equivalent origin to web default above. |

Override web with `REACT_APP_API_URL` on Vercel if you intentionally point at another deployment.

## `mode=cached` policy (shared contract)

Backend monitoring endpoints support `?mode=cached` to read **pre-upserted cache** (`FarmMonitoringCache` / `HouseMonitoringCache`) when present, avoiding synchronous Rotem calls on routine reads.

| Value | Intended use |
|-------|----------------|
| `mode=cached` (or default on some routes — see backend) | Fast reads for dashboards and mobile; relies on cron / refresh endpoint to populate cache. |
| Omitted / `mode=live` (if supported) | Fresher data at cost of Rotem latency; use sparingly. |

**Web** (`frontend/src/services/monitoringApi.ts`) uses `mode=cached` on: latest monitoring, farm dashboard, house KPIs, farm houses monitoring “all”, and heater history GET — aligned with iOS.

**iOS** (`APIClient.swift`) already appends `mode=cached` on dashboard, latest, KPIs, and heater-history where applicable.

## Endpoint matrix (monitoring + Rotem parity)

| Endpoint | Web caller | iOS caller | Query params / notes |
|----------|------------|------------|----------------------|
| `GET /api/farms/` | Various contexts | `fetchFarms` | — |
| `GET /api/farms/{id}/` | `UnifiedFarmDashboard` | — | Farm detail |
| `GET /api/farms/{id}/houses/` | — | `fetchHouses` | House list |
| `GET /api/farms/{id}/house-sensor-data/` | `UnifiedFarmDashboard` | `fetchFarmHouseSensorData` | Web parity / canonical sensors |
| `GET /api/farms/{id}/houses/monitoring/dashboard/` | `monitoringApi.getFarmMonitoringDashboard` | `fetchFarmMonitoringDashboard` | **`mode=cached` (web + iOS)** |
| `GET /api/farms/{id}/houses/monitoring/all/` | `monitoringApi.getFarmHousesMonitoring` | — | Web monitoring list |
| `POST /api/farms/{id}/houses/monitoring/refresh/` | — | `refreshFarmMonitoringNow` | Force cache refresh |
| `GET /api/houses/{id}/monitoring/latest/` | `monitoringApi.getHouseLatestMonitoring` | `fetchLatestMonitoring` | **`mode=cached` (web + iOS)** |
| `GET /api/houses/{id}/monitoring/history/` | `monitoringApi.getHouseMonitoringHistory`, charts | `fetchHouseMonitoringHistory` | `limit`, `start_date`, `end_date` |
| `GET /api/houses/{id}/monitoring/kpis/` | `monitoringApi.getHouseMonitoringKpis` | `fetchHouseMonitoringKpis` | **`mode=cached` (web + iOS)**; web may add `dod_reference_date`, `_` cache bust |
| `GET /api/houses/{id}/monitoring/stats/` | `monitoringApi.getHouseMonitoringStats` | — | Web only |
| `GET /api/houses/{id}/heater-history/` | `monitoringApi.getHouseHeaterHistory` | `fetchHouseHeaterHistory` | **`mode=cached` (web + iOS)**; optional `_` bust on web |
| `POST /api/houses/{id}/heater-history/refresh/` | `monitoringApi.refreshHouseHeaterHistory` | — | Web refresh |
| `GET /api/houses/{id}/water/alerts/` | `monitoringApi` / direct `api.get` | `fetchWaterAlerts` | iOS may use `include_resolved` |
| `GET /api/rotem/daily-summaries/water-history/` | — | `fetchRotemWaterHistory` | `house_id`, `days` |
| `GET /api/rotem/daily-summaries/temperature-history/` | — | `fetchRotemTemperatureHistory` | `house_id` |
| `GET /api/rotem/daily-summaries/feed-history/` | — | `fetchRotemFeedHistory` | `house_id` |
| `POST /api/rotem/scraper/scrape_farm/` | Sync flows | `triggerFarmScrape` | Farm scrape trigger |

## iOS farm reload fan-out (`reloadSelectedFarmData`)

Rough sequence (after this performance pass):

1. `GET /farms/{id}/houses/`
2. `GET .../monitoring/dashboard/?mode=cached` and `GET .../house-sensor-data/` (parallel where applicable in code paths)
3. **Per house (batched parallel, concurrency 6):** `GET .../monitoring/latest/?mode=cached` and `GET .../water/alerts/...` — builds `House` + alarm rows.
4. **Per house (unbounded TaskGroup, same as before):** KPIs + Rotem water history + heater history for realtime tiles.
5. `GET /flocks?farm_id=` then **batched parallel (4-wide):** `GET /flocks/{id}/performance/` per flock.

Web farm dashboard first paint typically uses **fewer** calls (`/farms/id/`, `house-sensor-data`, `monitoring/dashboard`) before per-house drill-down.

## Instrumentation checklist (optional)

- **Web:** Chrome DevTools Network — filter `api/farms`, `monitoring`, `house-sensor-data`; note waterfall vs parallel.
- **iOS:** Enable `ROTEM_IOS_VERBOSE_LOGS=true` — `APIClient` logs request duration per call.
- Compare **same farm id** and **same production host** when measuring.

## Related docs

- [mobile/ios/RotemFarm-iOS/docs/ROTEM_API_BACKEND_COVERAGE.md](../mobile/ios/RotemFarm-iOS/docs/ROTEM_API_BACKEND_COVERAGE.md) — Rotem upstream sample coverage.
