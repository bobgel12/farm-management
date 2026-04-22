# iOS Webapp Parity Matrix (Rotem Multi-Farm)

This matrix maps the Stitch design package to current backend/iOS support and highlights required implementation coverage.

## Status Key

- `ready`: backend contract and iOS behavior are available.
- `partial`: backend or iOS exists but design-level behavior is incomplete.
- `missing`: no current implementation.

## Screen to API to Field Coverage

| Screen | Design Source | Backend APIs | Key Fields | iOS Status | API Status | Gap |
|---|---|---|---|---|---|---|
| Farms list | `farms_list/code.html` | `GET /api/farms/`, `GET /api/farms/{id}/` | `id`, `name`, `active_houses`, `houses[]`, `integration_status` | partial | ready | Dedicated farms list/filter screen parity not complete in iOS. |
| Farm dashboard | `farm_dashboard/code.html` | `GET /api/farms/{farm_id}/houses/monitoring/dashboard/` | `total_houses`, `alerts_summary`, per-house `average_temperature`, `water_consumption`, `feed_consumption`, `growth_day` | ready | ready | Minor visual parity only. |
| House monitoring | `house_monitoring/code.html` | `GET /api/houses/{id}/monitoring/latest/`, `.../history/`, `.../kpis/`, `.../details/` | `average_temperature`, `humidity`, `static_pressure`, `airflow_percentage`, `source_timestamp` | partial | ready | Setpoint/control actions and extra sensor channels need parity. |
| House tasks | `house_tasks/code.html` | `GET /api/houses/{id}/tasks/`, `POST /api/tasks/{id}/complete/` | `task_name`, `description`, `day_offset`, `is_completed`, `completed_by`, `notes` | partial | partial | Missing richer status lifecycle and assignment metadata. |
| Workers list | `workers_list/code.html` | `GET /api/workers/?farm_id=`, `GET /api/farms/{id}/workers/` | `id`, `name`, `email`, `phone`, `role`, `is_active` | partial | ready | Search/filter presence and assignment workflows needed. |
| Alerts center | `alerts_center/code.html` | `GET /api/houses/water/alerts/feed/`, `POST .../acknowledge/`, `.../resolve/`, `.../snooze/` | `severity`, `message`, `house_number`, `created_at`, `is_acknowledged`, `is_resolved` | partial | partial | Cross-farm inbox actions now available, full alert categories still limited. |
| Program library | `program_library/code.html` | `GET /api/programs/`, `GET /api/programs/{id}/tasks/` | `name`, `duration_days`, `total_tasks`, `is_active` | partial | ready | Add categorization/tags and richer metadata for full parity. |
| Program timeline | `program_timeline/code.html` | `GET /api/programs/{id}/tasks/day/{day}/` | `day`, `title`, `priority`, `estimated_duration`, `is_required` | partial | ready | Needs deep task state/progress overlays for full parity. |
| Assign program | `assign_program/code.html` | `POST /api/programs/{id}/assign/` | `farm_ids[]`, `house_ids[]`, response `updated_farms`, `updated_houses` | partial | partial | New endpoint and iOS flow added; bulk UX polish still needed. |
| Integration management | `integration_management/code.html` | `GET /api/farms/{id}/integration_status/`, `POST /api/farms/{id}/configure_integration/`, `.../test_connection/`, `.../sync_data/` | `integration_type`, `integration_status`, `last_sync` | partial | ready | Need logs/history endpoint for full design parity. |

## Contract Alignment Notes

- Phase 2 contract endpoints for flocks and monitoring history are already supported.
- Monitoring history contract fields (`source_timestamp` with `timestamp` fallback) are supported.
- Collection wrapper tolerance (`[]` vs `{results: []}`) is already handled by the iOS API client.

## Priority Gaps to Close

1. Task and worker operational lifecycle parity (assignment, richer status states).
2. Integration activity logs endpoint and UI timeline.
3. Program assignment analytics (affected flocks/tasks impact preview).
