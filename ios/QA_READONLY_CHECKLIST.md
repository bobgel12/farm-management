# Read-Only MVP QA Checklist

## Organization Scoping

- Login as user from Organization A and verify only Organization A farms appear.
- Confirm farm detail only shows houses assigned through backend membership rules.
- Attempt direct navigation to unknown farm/house IDs and verify access is denied gracefully.

## Screen Behavior

- Dashboard loads summary counts and supports pull-to-refresh.
- Farm list loads, search works, empty state appears when no farms exist.
- Farm detail loads summary and houses list.
- House detail overview shows age/status/batch fields and handles null values.

## Error and Session Handling

- Invalid credentials show login error.
- Expired/invalid token forces logout path (`401` handling).
- Offline mode shows clear error and supports retry.

## Build/Distribution Gate

- Run decoder fixtures locally before each beta.
- Test on at least one physical iPhone and one simulator.
- Archive succeeds for Release with `API_BASE_URL_RELEASE` configured.
