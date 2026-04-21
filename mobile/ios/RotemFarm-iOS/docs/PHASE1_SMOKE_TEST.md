# Phase 1 Smoke Test Checklist

## Preconditions

- Backend running and reachable at configured `ROTEM_API_BASE_URL`.
- At least one farm, one house, and monitoring/alert data in backend.
- Valid user credentials available.

## Test steps

- [ ] Launch app and confirm login screen appears.
- [ ] Sign in with valid credentials and verify transition to tab UI.
- [ ] Open Home tab and verify farm/house metrics render from backend.
- [ ] Pull-to-refresh Home and confirm no crash and data reload.
- [ ] Open Houses tab and verify list uses backend house data.
- [ ] Open one house detail and verify live metric cards render.
- [ ] Open Alerts tab and verify backend alerts appear.
- [ ] Open alert detail and acknowledge alert; confirm alert becomes acknowledged in list.
- [ ] Sign out from Profile tab and verify session is cleared and app returns to login.

## Phase 1 done criteria

- App builds from `mobile/ios/RotemFarm-iOS`.
- Auth token flow works end-to-end.
- Farms/houses/alerts display live backend data.
- Core alert acknowledge round-trip works.
