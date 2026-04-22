# RotemNet Web App — Scraping & API Reference

This document describes how this project interacts with **RotemNetWeb** (`rotemnetweb.com`). The integration uses **authenticated JSON POST requests** to the same **ASP.NET WCF-style** endpoints the browser app calls (`AllServices.svc`). It is not traditional HTML scraping.

Use only credentials you are authorized to use. Respect Rotem’s terms of service and applicable laws.

---

## 1. Architecture at a glance

| Layer | Role |
|--------|------|
| **Entry** | `RotemScraper` in `backend/rotem_scraper/scraper.py` |
| **Django** | `DjangoRotemScraperService` persists data; Celery / management commands trigger runs |
| **Transport** | `requests.Session` with JSON bodies, browser-like headers, session cookies |

After login, the platform may redirect API calls to a **farm-specific host path** (for example `Host3_V1`). That base URL is taken from the login payload (`WebServerUrl`) and used for all subsequent service calls.

---

## 2. Base URLs

| Purpose | Typical URL |
|---------|-------------|
| **Login (fixed)** | `https://rotemnetweb.com/Latest/Services/AllServices.svc/Login` |
| **Post-login services** | `{WebServerUrl}/Services/AllServices.svc/{EndpointName}` |

`WebServerUrl` is normalized to an absolute URL with a trailing slash (for example `https://rotemnetweb.com/Host3_V1/`). If it is missing from the login response, the code defaults to `https://rotemnetweb.com/Host3_V1/`.

**Referer** for authenticated calls is built as:

`{WebServerUrl}rotemWebApp/Main.html`

---

## 3. Authentication

### 3.1 Request

**POST** `https://rotemnetweb.com/Latest/Services/AllServices.svc/Login`

**Headers (additional):**

- `Referer`: `https://rotemnetweb.com/Latest/rotemWebApp/User.html`
- `userToken`: `null`

**JSON body:**

```json
{
  "prmUsername": "<username>",
  "prmPassword": "<password>",
  "prmIsNativeAppLogin": false,
  "prmIsKeepMeSignedIn": false
}
```

### 3.2 Data you can extract from a successful login

| Field / artifact | Where it comes from | Use |
|------------------|---------------------|-----|
| **`WebServerUrl`** | Top-level or nested (`reponseObj` / `responseObj`, `FarmUser`, `FarmConnectionInfo`) | Base URL for all service calls after login |
| **`UserToken`** | `responseObj.FarmUser.UserToken` | Header `userToken` on subsequent requests |
| **`ConnectionToken`** | `responseObj.FarmConnectionInfo.ConnectionToken` | Header `farmConnectionToken` |
| **`GatewayName`** | `responseObj.FarmConnectionInfo.GatewayName` | Used as **GatewayCode** for `GetSiteControllersInfo` |
| **`ASP.NET_SessionId`** | Session cookie | Session continuity with the server |
| **Logical errors** | `isSucceed: false`, `exceptionMessage`, `ErrorObj` | Failure reasons even when HTTP status is 200 |

If `UserToken` or `ConnectionToken` is missing, the account may lack farm selection/context.

### 3.3 Headers for authenticated service calls

Common additions (see `RotemScraper` in code):

- `X-Requested-With`: `XMLHttpRequest`
- `userToken`: JWT from login
- `farmConnectionToken`: connection token from login
- `authorization`: often empty string (as sent by the web app)
- `userLanguage`: e.g. `ENGLISH`
- `Content-Type`: `application/json;charset=UTF-8`
- `Origin`: `https://rotemnetweb.com`

---

## 4. Service “commands” (endpoints) and extractable data

All of the following use **POST** with JSON unless noted. The full URL is:

`{WebServerUrl}Services/AllServices.svc/<EndpointName>`

### 4.1 `JsGlobals_GetJsGlobals`

| Item | Value |
|------|--------|
| **Body** | `{}` |
| **Typical use** | Client configuration / global settings used by the web app |

**Extractable:** Platform or UI configuration as returned by the API (structure is vendor-defined JSON). Used in this project as part of a full scrape payload (`js_globals`).

---

### 4.2 `GetSiteControllersInfo`

| Item | Value |
|------|--------|
| **Body** | `{ "prmSiteControllersInfoParams": { "GatewayCode": "<gateway>" } }` |

`GatewayCode` is normally **`FarmConnectionInfo.GatewayName`** from login (the scraper falls back to a default only if that attribute is missing—production data should use the login value).

**Extractable:** Information about **site controllers** (hardware / gateway side) for the farm—structure is vendor JSON (`site_controllers_info` in a full scrape).

---

### 4.3 `GetComparisonDisplayFields`

| Item | Value |
|------|--------|
| **Body** | `{}` |

**Extractable:** **Field metadata** for comparison views (which columns/fields the UI can show). Useful for understanding how the web app labels and groups metrics (`comparison_display_fields`).

---

### 4.4 `GetFarmRegistration`

| Item | Value |
|------|--------|
| **Body** | `{}` |

**Extractable:** **Farm registration** details as returned by Rotem (`farm_registration`): farm identity, registration-related fields—exact schema is vendor-defined.

---

### 4.5 `RNBL_GetCommandData` (per-house live / command data)

This is the main endpoint for **house-level operational and sensor data**. The scraper calls it for **houses 1–8** with **CommandID `"0"`** (general / default command bundle).

| Item | Value |
|------|--------|
| **Body** | See below |

**Example `prmGetCommandDataParams`:**

```json
{
  "prmGetCommandDataParams": {
    "CommandID": "0",
    "IsSetPointCommand": false,
    "HouseNumber": "2",
    "RoomNumber": -1,
    "ClientLanguageIndex": 1,
    "IsIgnoreCache": false,
    "PageNumber": -1,
    "IsLoadPageFromCache": false
  }
}
```

**Other `CommandID` values used in this codebase:**

| CommandID | Purpose |
|-----------|---------|
| **`"0"`** | General house command data (default scrape) |
| **`"40"`** | Water-related history / consumption (`get_water_history`) |
| **`"43"`** | Heater runtime history (`get_heater_history`, parsed in `parse_heater_history_records`) |

The water anomaly module comments that **`"48"`** may provide more granular (e.g. hourly) water data; that path is not wired into the default scrape loop.

**Typical response shape (conceptual):**

- Top-level: `isSucceed`, `isAuthorize`, `isInSession`, `reponseObj` / `responseObj` (note the common **`reponseObj` typo** in API responses).
- Inside `responseObj`: **`dsData`** with sections such as:
  - **`General`**: array of objects with `ParameterKeyName`, `ParameterValue`, `ParameterUnitType`, etc.
  - **`TempSensor`**: per-sensor rows (temperature, ammonia, wind, etc.).
  - **`Consumption`**: water, feed, and related consumption parameters.
  - **`DigitalOut`**: outputs (fans, heaters, lights); may use `ParameterData` for numeric values.
  - **`Data`**: tabular history for some command types (e.g. water or heater history), depending on `CommandID`.

**What this project extracts into `RotemDataPoint` (from CommandID `0`):**

- **General:** mapped parameters include average/outside temperature, humidity, static pressure, setpoint, growth day, feed/water consumption, CFM, bird count, livability, connection status (see `_get_parameter_type_and_unit` in `scraper_service.py`).
- **TempSensor:** tunnel/attic/wind chill temperatures, numbered temperature sensors, ammonia, wind speed/direction (`_get_sensor_type_and_unit_from_name`).
- **Consumption:** numeric consumption metrics.
- **DigitalOut:** numeric values taken from `ParameterData` where applicable.

If no numeric points are parsed, the service may **fall back to simulated points** for testing (see `_create_simulated_data_points`).

**Heater history (CommandID `43`):** rows under `dsData.Data` with fields like `HistoryRecord_Heaters_GrowthDay`, `HistoryRecord_Heaters_HeaterDevice_*`, totals—normalized into per–growth-day records with per-device minutes.

---

## 5. Commands you can run in this repository

Paths assume repo root; adjust if you run from `backend/`.

| Command | What it does |
|---------|----------------|
| `python backend/rotem_scraper/scraper.py <username> <password> [-o file.json]` | Standalone POC: login, call all services above, houses 1–8 command data, write JSON |
| `cd backend && python manage.py test_scraper` | Scrape using **default** env credentials (`ROTEM_USERNAME` / `ROTEM_PASSWORD`) and save via Django |
| `cd backend && python manage.py test_scraper --farm-id <rotem_farm_id_or_db_id>` | Scrape for a specific **Rotem-integrated** farm |
| `cd backend && python manage.py test_scraper --all-farms` | Scrape every active farm with Rotem credentials |
| `make rotem-test` | Docker: runs `test_scraper` inside the backend container (see `Makefile`) |
| `cd backend && python manage.py collect_rotem_data_daily` | Scheduled-style daily collection (see `DAILY_TASKS_SETUP.md`) |
| Celery task `scrape_rotem_data` | Automated periodic scrape (when workers are running) |

**Internal REST API (Django)** — for triggering or inspecting stored data (prefix depends on main URLconf, often `/api/rotem/`):

- `POST .../scraper/scrape_farm/` — body: `{ "farm_id": "<id>" }`
- `POST .../scraper/scrape_all/` — all farms
- `GET .../data/`, `.../controllers/`, `.../logs/`, etc.

---

## 6. Debugging failed requests

`RotemScraper` can print a **reproducible `curl`** for failed `RNBL_GetCommandData` calls (`_log_curl_debug`), including URL, selected headers, and JSON body—useful for manual comparison with browser network captures.

On `isAuthorize: false` or `isInSession: false`, the scraper may **re-login once** and retry the same house/command.

---

## 7. Related files

| File | Role |
|------|------|
| `backend/rotem_scraper/scraper.py` | Login, all service methods, command IDs, heater/water helpers |
| `backend/rotem_scraper/services/scraper_service.py` | Maps API JSON to `RotemDataPoint`, farm, controller |
| `backend/houses/services/monitoring_service.py` | Builds `HouseMonitoringSnapshot` from command data |
| `ROTEM_SETUP_GUIDE.md` (repo root) | Env vars, Docker, troubleshooting |

---

## 8. Summary table: endpoint → typical extracted data

| Service endpoint | Primary data |
|------------------|--------------|
| `Login` | Tokens, gateway, web server URL, session |
| `JsGlobals_GetJsGlobals` | Client/global config JSON |
| `GetSiteControllersInfo` | Controller / gateway info |
| `GetComparisonDisplayFields` | Comparison UI field definitions |
| `GetFarmRegistration` | Farm registration payload |
| `RNBL_GetCommandData` (`CommandID` **0**) | Live house: general params, temp sensors, consumption, digital outputs |
| `RNBL_GetCommandData` (`CommandID` **40**) | Water history / consumption series (`dsData.Data` or similar) |
| `RNBL_GetCommandData` (`CommandID` **43**) | Heater runtime history by growth day and device |

This reference reflects the implementation in this repository; Rotem may add or change fields without notice.
