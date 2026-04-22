# iOS Parity Validation Report

This validation report checks implemented parity work against the Stitch design bundle and Phase 2 API contract.

## Validation Method

- Static route/model/view-model review across backend and iOS code.
- Lint diagnostics review for modified files.
- Runtime command checks attempted (`python3 manage.py check`) but local Python environment does not include Django in this shell.

## Per-Screen Validation

| Screen | API availability | iOS wiring | Result |
|---|---|---|---|
| Farms list | `GET /api/farms/`, `GET /api/farms/{id}/` | Farm switcher + current farm summaries | partial |
| Farm dashboard | Monitoring dashboard endpoint available | Dashboard uses live farm/house/alert data | pass |
| House monitoring | latest/history/kpis/detail endpoints available | House detail and charts consume live monitoring | partial |
| House tasks | house tasks + status update endpoint available | Task center now loads API tasks and writes status updates | pass |
| Workers list | worker list endpoints available | Workers view now populated from API | pass |
| Alerts center | per-house alerts + global feed endpoint available | Existing alerts UI supports lifecycle actions; feed available for expansion | partial |
| Program library | list/detail/tasks endpoints available | Program manager now loads live programs | pass |
| Program timeline | day-based endpoint available | New `ProgramTimelineView` loads day-filtered tasks | pass |
| Assign program | bulk assign endpoint available | New `AssignProgramView` writes assignment to backend | pass |
| Integration management | integration status/config endpoints available | New `IntegrationManagementView` reads/saves integration config | pass |

## Role and Organization Scope Validation

- Added organization-scoped filtering in:
  - `backend/tasks/views.py` (task/house queries).
  - `backend/houses/views.py` (farm/house/water alerts queries).
  - `backend/rotem_scraper/views.py` (data and summary queries).
- Existing farm/flock scoping remains in farm viewsets.

## Loading/Empty/Error/Offline

- **Loading:** existing iOS store loading state reused by new live fetches.
- **Empty:** tasks/programs/workers/timeline screens show empty lists gracefully.
- **Error:** API failures set `store.lastError` without crashing flow.
- **Offline:** network failures degrade to empty/state error messaging, no hard crash.

## Residual Risk / Next Hardening Steps

1. Add explicit cross-farm alert feed UI in `AlertsView` to consume `water_alerts_feed`.
2. Add richer task lifecycle fields (`assigned_to`, due date, priority) in backend model for full design parity.
3. Add integration activity logs endpoint and timeline UI section.
4. Run full backend tests and iOS build in a configured environment (Django + Xcode toolchain).
