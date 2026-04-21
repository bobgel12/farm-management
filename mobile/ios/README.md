# iOS Migration Notes

This directory contains the migrated Claude iOS app at `mobile/ios/RotemFarm-iOS`.

## What was migrated

- SwiftUI app source from the Claude project.
- XcodeGen manifest (`project.yml`) as the project source of truth.
- Assets and app resources.

## Run locally

1. Install XcodeGen:
   - `brew install xcodegen`
2. Generate project from `mobile/ios/RotemFarm-iOS`:
   - `xcodegen generate`
3. Open project:
   - `open RotemFarm.xcodeproj`

## Backend config

- Default API base URL in app code: **`http://localhost:8002`** (matches this repo’s **Docker Compose** host mapping `8002:8000`).
- If you run Django on the **host** at port **8000** instead, set `ROTEM_API_BASE_URL=http://localhost:8000` (Xcode scheme env or shell).
- **Docker Compose:** Django listens on `0.0.0.0:8000` inside the container; the host sees it at **8002**. For the **Simulator**, `http://localhost:8002` is correct.
- **Physical device:** use your Mac’s LAN address and the same host port, e.g. `http://192.168.x.x:8002`, and ensure the phone can reach that host (same Wi‑Fi, firewall allows inbound).

Set the base URL wherever you inject env for runs:

- Xcode: **Product → Scheme → Edit Scheme → Run → Arguments → Environment Variables** → add `ROTEM_API_BASE_URL`
- Or pass it when opening from the shell (see `scripts/setup-run-ios.sh`).

### Sign-in (API / iOS)

From `docker-compose.yml` / seeding, the default admin user is **`admin` / `admin123`** unless overridden in your `.env`. The iOS login screen can prefill credentials via:

- `ROTEM_IOS_USERNAME`
- `ROTEM_IOS_PASSWORD`
