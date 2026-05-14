# FarmManagement iOS

Native iOS app migration workspace for the farm management platform.

## Phase 1 Defaults

- Deployment target: `iOS 16.0+`
- Device support: `iPhone` first (iPad can be enabled in a later phase)
- UI framework: `SwiftUI`
- Architecture: `MVVM` with feature modules
- Auth: backend token auth using `Authorization: Token <token>`

## Structure

- `FarmManagementApp/`: SwiftUI app sources
- `FarmManagementCore/`: shared networking/domain package and tests
- `fastlane/`: beta distribution automation

## Setup

1. Install Xcode 15+.
2. Open the `ios` folder in Xcode as a workspace root.
3. Add an iOS App target named `FarmManagementApp` and point its source root to `ios/FarmManagementApp`.
4. Add local package dependency from `ios/FarmManagementCore`.
5. Create build settings:
   - `API_BASE_URL_DEBUG`
   - `API_BASE_URL_RELEASE`

Environment values are read in `FarmManagementApp/Core/AppEnvironment.swift`.
