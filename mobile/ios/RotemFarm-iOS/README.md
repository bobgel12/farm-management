# RotemFarm — iOS app (stub-data build)

Native iOS companion app for broiler farms running Rotem controllers. This is the initial stub-data build that implements every tab and the main detail screens from the HTML UX mockups. Once the backend (`farm-management` repo) exposes the v2 API described in `../PLAN.md`, swap `MockDataStore` for a real `APIClient` — the rest of the code won't change.

## Stack
- **iOS 17+** · Swift 5.9 · SwiftUI
- **Swift Charts** for all history/comparison charts
- **@Observable** for state (iOS 17 Observation framework)
- **AuthenticationServices** for Sign in with Apple (stub)
- **LocalAuthentication** for Face ID confirmation on setpoint changes

## Generate the Xcode project

This repo uses [XcodeGen](https://github.com/yonaskolb/XcodeGen) so the project file is regenerable.

```bash
# one-time
brew install xcodegen

# from RotemFarm-iOS/
xcodegen generate
open RotemFarm.xcodeproj
```

Then press **⌘R** in Xcode to run on the iPhone 15 simulator.

## Folder layout

```
RotemFarm/
├── App/              # entry point + tab bar host
├── DesignSystem/     # colors, typography, reusable components
├── Models/           # domain types
├── Services/         # mock data + auth
├── Features/
│   ├── Auth/         # Sign in with Apple
│   ├── Dashboard/    # Home tab (mockup §2.1)
│   ├── Houses/       # list, detail, sensor history (§2.2, §2.3, §3.1)
│   ├── Resources/    # water, feed, heater (§8.2–§8.4)
│   ├── Alerts/       # inbox + detail (§4.1, §4.2)
│   ├── Tips/         # AI tips hub (§5.1)
│   ├── Reports/      # rolled-up farm KPIs (§6.3)
│   ├── Flocks/       # flock list + growth curve (§6.1, §6.2)
│   └── Settings/     # profile, team, pair controller (§7)
└── Resources/        # Info.plist, assets
```

## Stubbed vs real

| Area | This build | Real build plan |
|---|---|---|
| Data | In-memory `MockDataStore` (refreshes at app launch) | `APIClient` hitting the v2 endpoints in `../PLAN.md` §3.2 |
| Auth | Sign in with Apple button that synthesizes a session | Full Apple identity-token → backend JWT exchange |
| Push | — | APNs HTTP/2 direct with Critical Alerts entitlement |
| Offline | Ephemeral (in-memory) | SwiftData cache + outbox actor |
| Set-points | No-op with Face ID prompt | Real POST to `/houses/:id/setpoints` (audited) |

## What's implemented

- 5-tab app: Home · Houses · Alerts · Reports · Profile
- Sign in with Apple gate (stub accepts any tap)
- Design tokens (forest-green brand + iOS system colors)
- Reusable components: `SensorCard`, `HouseCard`, `KPICard`, `AICard`, `PillBadge`, `HeroMetricCard`, `SectionHeader`
- Dashboard with hero flock card, sensor grid, AI tip
- House list → house detail → sensor history (with Swift Chart + target band)
- Water / feed / heater day-over-day detail views
- Alert inbox grouped by severity → alert detail with AI fix suggestion
- Tips hub sheet from dashboard
- Reports tab with KPI tiles and trend charts
- Flocks sub-flow with growth curve vs breed target
- Profile with team management and pair-controller wizard

## Known stubs / next steps

1. No real networking yet.
2. No push handling — `UNUserNotificationCenter` permission prompt is wired but no APNs registration.
3. No unit tests yet (scaffolding ready).
4. Localization is English-only (strings are in code, not yet extracted to `Localizable.strings`).
5. `DeviceSupport` for iPad is off (iPhone only for v1).

## Adding a new screen

1. Create a new `View` under `Features/<area>/`.
2. Reach data via `@Environment(MockDataStore.self) private var store`.
3. Wire it into navigation from the relevant list view with a `NavigationLink(value:)`.
4. Add a case to the parent's `.navigationDestination(for:)`.
