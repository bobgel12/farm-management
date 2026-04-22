# iOS Design/Backend Gap Matrix

This matrix tracks parity gaps between:
- iOS implementation in `mobile/ios/RotemFarm-iOS/RotemFarm`
- Stitch design package in `/Users/phucle/Downloads/stitch_rotem_multi_farm_monitor`
- Backend APIs under `backend/`

## P0 (must close first)

| Area | iOS Screen/File | Design expectation | Backend support | Gap | Action |
|---|---|---|---|---|---|
| Alerts lifecycle | `Features/Alerts/AlertsView.swift` | Acknowledge + snooze + resolve lifecycle actions | `POST /api/houses/water/alerts/{id}/{acknowledge,snooze,resolve}/` | Snooze/resolve partially missing in UI wiring | Wire snooze + resolve actions and state updates |
| Program persistence | `Features/Programs/ProgramManagerView.swift` | Program state reflects backend truth | `PATCH /api/programs/{id}/` | Toggle was local-only | Persist toggle to backend via APIClient |
| Flock fidelity | `Services/MockDataStore.swift`, `Features/Flocks/FlockDetailView.swift` | KPI/curve from live flock performance | `GET /api/flocks/{id}/performance/` | Synthetic curves/KPIs | Build curves and logs from performance records |
| Realtime freshness | `App/RootView.swift`, monitoring-heavy screens | Data refresh on foreground/view entry | Existing monitoring/farm endpoints | Stale snapshot perception | Add explicit foreground refresh trigger |

## P1 (parity and depth)

| Area | iOS Screen/File | Design expectation | Backend support | Gap | Action |
|---|---|---|---|---|---|
| Workers ops parity | `Features/Workers/WorkersManagementView.swift` | Search/filter + workforce summary | `GET /api/workers/?farm_id=` | Basic list only | Add search/filter and summary |
| Integration management detail | `Features/Admin/IntegrationManagementView.swift` | Health and activity visibility | `GET /api/farms/{id}/integration_status/` | Minimal status text | Surface sync/health metadata |
| Reports realism | `Features/Reports/ReportsView.swift` | Production-grade KPI sources | Mixed support; no dedicated energy/mortality aggregate endpoint | Synthetic random charts | Replace with backend-derived aggregates where available, annotate unsupported metrics |

## Platform stability/observability

| Area | File | Gap | Action |
|---|---|---|---|
| Mixed response envelopes | `Services/APIClient.swift` | Endpoint payloads vary (`[]` vs `{results}`) | Centralize decoder usage and avoid ad-hoc JSON parsing patterns |
| Debug visibility | `Services/APIClient.swift`, `Services/MockDataStore.swift` | Hard to trace stale data paths | Add toggleable verbose logs (`ROTEM_IOS_VERBOSE_LOGS=true`) for request/store refresh traces |

## Validation checklist

- Prod login succeeds and token is retained in keychain.
- Foregrounding app refreshes selected farm data.
- Alert snooze/resolve actions reflect in backend and UI list state.
- Program toggle persists after app restart.
- Flock detail chart reflects backend performance records when present.
- Workers screen supports search/filter and summary view.
- Verbose logs can be enabled with `ROTEM_IOS_VERBOSE_LOGS=true`.
