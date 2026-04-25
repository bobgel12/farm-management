# Rotem API Documentation and Backend Coverage Validation

This document catalogs the provided Rotem API samples and validates whether the current backend already uses each upstream endpoint.

For **iOS vs web REST usage**, `mode=cached` alignment, and production base URL notes, see the repo-wide matrix: [IOS_WEB_API_MATRIX.md](../../../../docs/IOS_WEB_API_MATRIX.md).

## Source Samples

- `api1.json`
- `api2.json`
- `api3.json`
- `api4.json`
- `api5.json`
- `api6.json`
- `temperature_history_api7.json`
- `water_history_api8.json`
- `feed_history_api9.json`
- `heater_history_api10.json`

## High-level Categorization

### Authentication and Session Context

- `Login` (implied prerequisite across all samples through auth headers/cookies)

### Farm and App Bootstrap Metadata

- `GetFarmRegistration`
- `GetComparisonDisplayFields`
- `JsGlobals_GetJsGlobals`
- `GetHouseData` (menu/page schema)

### Live Monitoring

- `GetSiteControllersInfo`
- `RNBL_GetCommandData` with `CommandID=0`

### Historical Monitoring

- `RNBL_GetCommandData` with:
  - `CommandID=35` (temperature history)
  - `CommandID=40` (water history)
  - `CommandID=41` (feed history)
  - `CommandID=43` (heater runtime history)

---

## Endpoint Reference (Per Sample)

## 1) `api1.json` - GetFarmRegistration

- **Endpoint**: `.../Services/AllServices.svc/GetFarmRegistration`
- **Method**: `POST`
- **Request body**: `prmFarmRegistrationParams.GatewayCode`
- **Headers/session**:
  - `userToken`
  - `farmConnectionToken`
  - `contextId`
  - `ASP.NET_SessionId` cookie
- **Response highlights**:
  - `reponseObj.FarmRegistration` (farm identity/address/profile)
  - `DtIntegrators`, `DtCountries`, `DtSegments`
  - envelope flags: `isInSession`, `isAuthorize`, `isSucceed`, `ErrorObj`
- **Purpose**: Farm registration/profile metadata bootstrap.

## 2) `api2.json` - GetComparisonDisplayFields

- **Endpoint**: `.../Services/AllServices.svc/GetComparisonDisplayFields`
- **Method**: `POST`
- **Request body**: `{}`
- **Headers/session**: same session/auth pattern
- **Response highlights**:
  - array of display field definitions:
    - `FieldName`, `DisplayFieldName`, `DisplayGroupName`
    - `IsSelected`, `IsEditable`, `CaptionLanguageKey`
- **Purpose**: Comparison UI field configuration metadata.

## 3) `api3.json` - GetSiteControllersInfo

- **Endpoint**: `.../Services/AllServices.svc/GetSiteControllersInfo`
- **Method**: `POST`
- **Request body**: `null`
- **Headers/session**: same session/auth pattern
- **Response highlights**:
  - `reponseObj.FarmHouses[]` per house with:
    - `HouseNumber`, `ConnectionStatus`, `GrowthDay`
    - `Data` sections (`Temperature`, `Humidity`, `Pressure`, `DailyWater`, `DailyFeed`, ...)
  - each metric includes current/target/alarm information
- **Purpose**: Live per-house controller state and top-level metrics.

## 4) `api4.json` - JsGlobals_GetJsGlobals

- **Endpoint**: `.../Services/AllServices.svc/JsGlobals_GetJsGlobals`
- **Method**: `POST`
- **Request body**: `{}`
- **Headers/session**: same session/auth pattern
- **Response highlights**:
  - very large global config payload:
    - app settings
    - enum maps
    - localization dictionaries
- **Purpose**: Client bootstrap globals and localization metadata.

## 5) `api5.json` - GetHouseData

- **Endpoint**: `.../Services/AllServices.svc/GetHouseData`
- **Method**: `POST`
- **Request body**:
  - `prmGetMenuParams.HouseNumber`
  - `prmGetMenuParams.RoomNumber`
  - `prmGetMenuParams.ClientLanguageIndex`
- **Headers/session**: same session/auth pattern
- **Response highlights**:
  - menu/page schema:
    - `Menu`, `SubMenus`
    - page descriptors, element configs, caching flags
- **Purpose**: Dynamic house menu and page definition metadata.

## 6) `api6.json` - RNBL_GetCommandData (CommandID 0)

- **Endpoint**: `.../Services/AllServices.svc/RNBL_GetCommandData`
- **Method**: `POST`
- **Request body**:
  - `prmGetCommandDataParams.CommandID = "0"`
  - house/room/language and cache flags
- **Headers/session**: same session/auth pattern
- **Response highlights**:
  - `reponseObj.dsData` with sections such as:
    - `General`, `TempSensor`, `Consumption`
    - `DigitalOut`, `AnalogOut`
    - short history segments
  - includes metadata table (`MDT`) and formatted companion views
- **Purpose**: Primary live command bundle for house operational telemetry.

## 7) `temperature_history_api7.json` - RNBL_GetCommandData (CommandID 35)

- **Endpoint**: `.../Services/AllServices.svc/RNBL_GetCommandData`
- **Method**: `POST`
- **Request body**: `CommandID = 35`
- **Headers/session**: same session/auth pattern
- **Response highlights**:
  - history table model and rows:
    - growth day
    - min/avg/max temperature values
- **Purpose**: Temperature history data table.

## 8) `water_history_api8.json` - RNBL_GetCommandData (CommandID 40)

- **Endpoint**: `.../Services/AllServices.svc/RNBL_GetCommandData`
- **Method**: `POST`
- **Request body**: `CommandID = 40`
- **Headers/session**: same session/auth pattern
- **Response highlights**:
  - growth-day records with:
    - total daily water
    - change percentage
    - line-level water values
    - cooling/fogger/flushing fields
- **Purpose**: Water consumption history.

## 9) `feed_history_api9.json` - RNBL_GetCommandData (CommandID 41)

- **Endpoint**: `.../Services/AllServices.svc/RNBL_GetCommandData`
- **Method**: `POST`
- **Request body**: `CommandID = 41`
- **Headers/session**: same session/auth pattern
- **Response highlights**:
  - growth-day feed records with:
    - daily total feed and delta
    - per-bird feed
    - feeder-line breakdown and deltas
- **Purpose**: Feed consumption history.

## 10) `heater_history_api10.json` - RNBL_GetCommandData (CommandID 43)

- **Endpoint**: `.../Services/AllServices.svc/RNBL_GetCommandData`
- **Method**: `POST`
- **Request body**: `CommandID = 43`
- **Headers/session**: same session/auth pattern
- **Response highlights**:
  - growth-day heater runtime rows:
    - per heater device runtime (`HeaterDevice_1..16`)
    - time-like values
- **Purpose**: Heater runtime history.

---

## Backend Usage Mapping

## Rotem upstream client

- Core class: `backend/rotem_scraper/scraper.py`
- Key methods:
  - `login()`
  - `get_js_globals()`
  - `get_site_controllers_info()`
  - `get_comparison_display_fields()`
  - `get_farm_registration()`
  - `get_command_data()`
  - `get_water_history()` (`CommandID=40`)
  - `get_heater_history()` (`CommandID=43`)

## App API routes consuming those upstream calls

- `backend/houses/views.py`
  - `/api/houses/{house_id}/monitoring/latest/` -> `GetSiteControllersInfo`
  - `/api/houses/{house_id}/monitoring/history/` -> `CommandID=40` (+ live append from `GetSiteControllersInfo`)
  - `/api/houses/{house_id}/monitoring/kpis/` -> `CommandID=40` + `CommandID=43`
  - `/api/houses/{house_id}/heater-history/` -> `CommandID=43`
  - `/api/farms/{farm_id}/houses/monitoring/all/` -> `GetSiteControllersInfo`
  - `/api/farms/{farm_id}/houses/monitoring/dashboard/` -> `GetSiteControllersInfo`
  - `/api/houses/comparison/` -> `GetSiteControllersInfo`
- `backend/houses/services/monitoring_cache_service.py`
  - farm/house cache upsert pipeline using:
    - `GetSiteControllersInfo`
    - `CommandID=40`
    - `CommandID=43`
- `backend/rotem_scraper/views.py`
  - `/api/rotem/daily-summaries/water-history/` -> `CommandID=40`
- `backend/integrations/views.py`
  - `/api/farms/{farm_id}/house-sensor-data/` -> `CommandID=0` through integration wrapper

---

## Coverage Matrix (Samples vs Backend)


| Sample       | Upstream endpoint / command  | Backend usage status  | Where used                                                                        |
| ------------ | ---------------------------- | --------------------- | --------------------------------------------------------------------------------- |
| `api1.json`  | `GetFarmRegistration`        | **Used**              | `rotem_scraper/scraper.py` (`get_farm_registration`) in batch scrape flow         |
| `api2.json`  | `GetComparisonDisplayFields` | **Used**              | `rotem_scraper/scraper.py` (`get_comparison_display_fields`) in batch scrape flow |
| `api3.json`  | `GetSiteControllersInfo`     | **Used**              | `houses/views.py`, `houses/services/monitoring_cache_service.py`                  |
| `api4.json`  | `JsGlobals_GetJsGlobals`     | **Used**              | `rotem_scraper/scraper.py` (`get_js_globals`) in batch scrape flow                |
| `api5.json`  | `GetHouseData`               | **Not used**          | no current direct backend call                                                    |
| `api6.json`  | `RNBL_GetCommandData (0)`    | **Used**              | `integrations/rotem.py` / `integrations/views.py` (`house-sensor-data`)           |
| `api7.json`  | `RNBL_GetCommandData (35)`   | **Not used directly** | no direct handler wired                                                           |
| `api8.json`  | `RNBL_GetCommandData (40)`   | **Used**              | water history + monitoring history/KPIs + cache service                           |
| `api9.json`  | `RNBL_GetCommandData (41)`   | **Not used directly** | no direct feed-history endpoint wired                                             |
| `api10.json` | `RNBL_GetCommandData (43)`   | **Used**              | heater history + KPIs + cache service                                             |


---

## Validation Summary

- Backend currently uses the majority of critical live/history Rotem paths:
  - `GetSiteControllersInfo`
  - `RNBL_GetCommandData` for `0`, `40`, `43`
  - plus bootstrap endpoints in scrape flows.
- Missing direct support remains for:
  - `GetHouseData`
  - explicit temperature history command (`35`)
  - explicit feed history command (`41`)

---

## Known Contract Mismatches (Web vs iOS)

## 1) Endpoint source mismatch

- Web home/overview uses `/api/farms/{farm_id}/house-sensor-data/`.
- iOS has mixed consumption between house monitoring endpoints and this parity endpoint.
- Effect: iOS can show stale or empty cards while web shows valid rows.

## 2) Sensor key mismatch risk

- Backend `house-sensor-data` response uses nested sensor keys that do not always match iOS field expectations exactly.
- Example pattern to normalize consistently:
  - backend `water` -> iOS `waterConsumption`
  - backend ventilation section -> iOS airflow percentage field

## 3) History coverage mismatch

- Sample commands include dedicated temperature (`35`) and feed (`41`) historical tables.
- Backend currently surfaces water (`40`) and heater (`43`) first-class, but not dedicated `35`/`41` routes.

---

## Recommended Next Steps (Prioritized)

1. Standardize a single iOS home/overview data source (prefer `/api/farms/{id}/house-sensor-data/` parity path or equivalent normalized cache endpoint).
2. Add explicit response normalization layer in backend for sensor key names to eliminate web/iOS drift.
3. Add optional backend endpoints for `CommandID=35` and `CommandID=41` if those historical views are required by product scope.
4. Keep cache metadata (`age_seconds`, `is_stale`, `refresh_state`) on all monitoring endpoints so clients can safely show loading/stale/error states without fake values.