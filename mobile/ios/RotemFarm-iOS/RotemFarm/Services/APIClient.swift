import Foundation

enum APIClientError: Error, LocalizedError {
    case invalidURL
    case unauthorized
    case server(String)
    case decoding

    var errorDescription: String? {
        switch self {
        case .invalidURL: "Invalid API URL."
        case .unauthorized: "Unauthorized. Please sign in again."
        case .server(let message): message
        case .decoding: "Failed to decode server response."
        }
    }
}

struct AuthSession {
    let token: String
    let user: APIUser
}

struct APIUser {
    let id: Int
    let username: String
    let email: String
    let isStaff: Bool
}

struct APIFarm {
    let id: Int
    let name: String
    let totalHouses: Int
    let activeHouses: Int
    let rotemFarmID: String?
}

struct APIHouse {
    let id: Int
    let houseNumber: Int
    let currentDay: Int
    let isActive: Bool
}

struct APIMonitoring {
    let averageTemperature: Double?
    let humidity: Double?
    let staticPressure: Double?
    let waterConsumption: Double?
    let feedConsumption: Double?
    let airflowPercentage: Double?
}

struct APIFreshnessMeta {
    let sourceTimestamp: Date?
    let fetchedAt: Date?
    let ageSeconds: Int?
    let isStale: Bool
    let refreshState: String
    let canRefreshNow: Bool
}

struct APIEnvelope<T> {
    let data: T
    let meta: APIFreshnessMeta?
}

struct APIWaterAlert {
    let id: Int
    let severity: String
    let message: String
    let houseNumber: Int?
    let createdAt: Date?
    let isAcknowledged: Bool
    let increasePercentage: Double?
}

struct APIFlock {
    let id: Int
    let houseID: Int?
    let batchNumber: String
    let breedName: String
    let arrivalDate: Date?
    let expectedHarvestDate: Date?
    let currentAgeDays: Int
    let initialChickenCount: Int
    let currentChickenCount: Int
    let isActive: Bool
    let status: String
    let mortalityRate: Double?
}

struct APIFlockPerformance {
    let id: Int
    let flockID: Int?
    let recordDate: Date?
    let flockAgeDays: Int?
    let averageWeightGrams: Double?
    let feedConversionRatio: Double?
    let dailyFeedConsumptionKg: Double?
    let dailyWaterConsumptionLiters: Double?
    let mortalityRate: Double?
    let livability: Double?
}

struct APIHouseMonitoringPoint {
    let timestamp: Date
    let averageTemperature: Double?
    let humidity: Double?
    let staticPressure: Double?
    let airflowPercentage: Double?
    let waterConsumption: Double?
    let feedConsumption: Double?
}

struct APIHouseMonitoringKpis {
    let heaterHours24h: Double?
    let waterToday: Double?
    let waterYesterday: Double?
    let feedToday: Double?
    let feedYesterday: Double?
    let waterFeedRatioToday: Double?
}

struct APIRotemWaterHistoryPoint {
    let date: Date?
    let growthDay: Int?
    let consumptionAvg: Double
}

struct APIRotemTemperatureHistoryPoint {
    let date: Date?
    let growthDay: Int
    let minValue: Double?
    let avgValue: Double?
    let maxValue: Double?
}

struct APIRotemFeedHistoryPoint {
    let date: Date?
    let growthDay: Int
    let dailyFeedTotal: Double
    let feedPerBird: Double?
    let changePercent: Double?
}

struct APIFarmHouseMeta {
    let houseID: Int
    let houseNumber: Int
    let capacity: Int?
    let isIntegrated: Bool
    let currentAgeDays: Int?
    let lastSystemSync: Date?
}

struct APIFarmHouseMonitoringCard {
    let houseID: Int
    let houseNumber: Int
    let averageTemperature: Double?
    let humidity: Double?
    let staticPressure: Double?
    let airflowPercentage: Double?
    let waterConsumption: Double?
    let feedConsumption: Double?
    let growthDay: Int?
    let houseCurrentDay: Int?
    let activeAlarmsCount: Int
}

struct APIFarmMonitoringSnapshotHouse {
    let houseID: Int
    let houseNumber: Int
    let currentDay: Int?
    let averageTemperature: Double?
    let humidity: Double?
    let staticPressure: Double?
    let airflowPercentage: Double?
    let waterConsumption: Double?
    let feedConsumption: Double?
    let isConnected: Bool
    let alarmStatus: String
}

struct APIFarmMonitoringSnapshotAlert {
    let houseID: Int
    let activeCount: Int
    let highestSeverity: String
    let latestMessage: String?
}

struct APIFarmMonitoringSnapshotResult {
    let houses: [APIFarmMonitoringSnapshotHouse]
    let alertsByHouseID: [Int: APIFarmMonitoringSnapshotAlert]
    let freshness: APIFreshnessMeta?
}

struct APIFarmMonitoringDashboardResult {
    let totalHouses: Int
    let alertsSummaryTotalActive: Int
    let houses: [APIFarmHouseMonitoringCard]
    let freshness: APIFreshnessMeta?
}

/// Unified iOS snapshot — all sensor fields from one cache-consistent response.
struct APIFarmIOSSnapshotHouse {
    let houseID: Int
    let houseNumber: Int
    let currentDay: Int?
    let averageTemperature: Double?
    let humidity: Double?
    let staticPressure: Double?
    let airflowPercentage: Double?
    let waterConsumption: Double?
    let feedConsumption: Double?
    let isConnected: Bool
    let alarmStatus: String
    let dataStatus: String  // "ok" | "stale" | "failed" | "db_fallback"
}

struct APIFarmIOSSnapshotAlert {
    let houseID: Int
    let activeCount: Int
    let highestSeverity: String
    let latestMessage: String?
}

struct APIFarmIOSSnapshotResult {
    let farmID: Int
    let farmName: String
    let houses: [APIFarmIOSSnapshotHouse]
    let alertsByHouseID: [Int: APIFarmIOSSnapshotAlert]
    let alertsSummaryTotalActive: Int
    let freshness: APIFreshnessMeta?
    let circuitOpen: Bool
}

struct APITask {
    let id: Int
    let houseID: Int?
    let taskName: String
    let description: String
    let dayOffset: Int
    let isCompleted: Bool
    let completedBy: String
    let notes: String
}

struct APIWorker {
    let id: Int
    let name: String
    let role: String
    let phone: String
    let farmID: Int?
    let isActive: Bool
}

struct APIProgram {
    let id: Int
    let name: String
    let durationDays: Int
    let totalTasks: Int
    let isActive: Bool
}

struct APIProgramTask {
    let id: Int
    let day: Int
    let title: String
    let priority: String
    let estimatedDuration: Int
    let isRequired: Bool
}

struct APIFarmIntegrationStatus {
    let farmID: Int
    let integrationType: String
    let integrationStatus: String
    let lastSync: Date?
}

enum APIEnvironment: String, CaseIterable {
    case local
    case prod

    var displayName: String {
        switch self {
        case .local: "Local"
        case .prod: "Prod"
        }
    }

    var baseURLString: String {
        switch self {
        case .local:
            return "http://localhost:8002"
        case .prod:
            // Production Railway backend endpoint.
            return "https://farm-management-production-54e4.up.railway.app"
        }
    }
}

actor APIClient {
    private let session: URLSession
    private let tokenStore: TokenStore
    private var baseURL: URL
    private var token: String?
    private let verboseLogging: Bool
    private let diagnosticsEnabled: Bool

    init(
        baseURLString: String = ProcessInfo.processInfo.environment["ROTEM_API_BASE_URL"] ?? "http://localhost:8002",
        session: URLSession = .shared,
        tokenStore: TokenStore = KeychainTokenStore()
    ) {
        self.session = session
        self.tokenStore = tokenStore
        // Default matches docker-compose host mapping (8002 -> container :8000). Override with ROTEM_API_BASE_URL for host-run Django on :8000.
        self.baseURL = URL(string: baseURLString) ?? URL(string: "http://localhost:8002")!
        self.token = tokenStore.loadToken()
        self.verboseLogging = (ProcessInfo.processInfo.environment["ROTEM_IOS_VERBOSE_LOGS"] ?? "").lowercased() == "true"
        self.diagnosticsEnabled = (ProcessInfo.processInfo.environment["ROTEM_IOS_DIAGNOSTICS"] ?? "true").lowercased() != "false"
    }

    func setEnvironment(_ environment: APIEnvironment) throws {
        guard let newURL = URL(string: environment.baseURLString) else {
            throw APIClientError.invalidURL
        }
        baseURL = newURL
        try tokenStore.clear()
        token = nil
    }

    func baseURLString() -> String {
        baseURL.absoluteString.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
    }

    func bootstrapToken() -> String? { token }

    func login(username: String, password: String) async throws -> AuthSession {
        let payload = ["username": username, "password": password]
        let data = try await request(path: "/api/auth/login/", method: "POST", payload: payload, requiresAuth: false)
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let token = json["token"] as? String,
            let userJSON = json["user"] as? [String: Any],
            let userID = userJSON["id"] as? Int,
            let username = userJSON["username"] as? String
        else {
            throw APIClientError.decoding
        }
        let user = APIUser(
            id: userID,
            username: username,
            email: (userJSON["email"] as? String) ?? "",
            isStaff: (userJSON["is_staff"] as? Bool) ?? false
        )
        try tokenStore.save(token: token)
        self.token = token
        return AuthSession(token: token, user: user)
    }

    func logout() async throws {
        _ = try await request(path: "/api/auth/logout/", method: "POST", payload: nil, requiresAuth: true)
        try tokenStore.clear()
        token = nil
    }

    func clearToken() throws {
        try tokenStore.clear()
        token = nil
    }

    func fetchUser() async throws -> APIUser {
        let data = try await request(path: "/api/auth/user/", method: "GET", payload: nil, requiresAuth: true)
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let userJSON = json["user"] as? [String: Any],
            let userID = userJSON["id"] as? Int,
            let username = userJSON["username"] as? String
        else {
            throw APIClientError.decoding
        }
        return APIUser(
            id: userID,
            username: username,
            email: (userJSON["email"] as? String) ?? "",
            isStaff: (userJSON["is_staff"] as? Bool) ?? false
        )
    }

    func fetchFarms() async throws -> [APIFarm] {
        let data = try await request(path: "/api/farms/", method: "GET", payload: nil, requiresAuth: true)
        let items = try decodeCollection(data: data)
        return items.compactMap { item in
            guard let id = item["id"] as? Int, let name = item["name"] as? String else { return nil }
            return APIFarm(
                id: id,
                name: name,
                totalHouses: (item["total_houses"] as? Int) ?? 0,
                activeHouses: (item["active_houses"] as? Int) ?? 0,
                rotemFarmID: (item["rotem_farm_id"] as? String) ?? (item["farm_id"] as? String)
            )
        }
    }

    func fetchFarmHouseMeta(farmID: Int) async throws -> [APIFarmHouseMeta] {
        let data = try await request(
            path: "/api/farms/\(farmID)/",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let houses = json["houses"] as? [[String: Any]]
        else {
            throw APIClientError.decoding
        }
        return houses.compactMap { item in
            guard let houseID = item["id"] as? Int, let houseNumber = item["house_number"] as? Int else {
                return nil
            }
            return APIFarmHouseMeta(
                houseID: houseID,
                houseNumber: houseNumber,
                capacity: item["capacity"] as? Int,
                isIntegrated: (item["is_integrated"] as? Bool) ?? false,
                currentAgeDays: item["current_age_days"] as? Int,
                lastSystemSync: (item["last_system_sync"] as? String).flatMap(parseISODate)
            )
        }
    }

    func fetchFarmMonitoringDashboard(farmID: Int) async throws -> APIFarmMonitoringDashboardResult {
        let data = try await request(
            path: "/api/farms/\(farmID)/houses/monitoring/dashboard/?mode=live",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 90
        )
        guard
            let root = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        else {
            throw APIClientError.decoding
        }
        let envelope = decodeEnvelope(root)
        let payload = envelope.payload
        guard let houses = payload["houses"] as? [[String: Any]] else {
            throw APIClientError.decoding
        }
        let alertsSummary = payload["alerts_summary"] as? [String: Any]
        let totalActiveAlerts = (alertsSummary?["total_active"] as? Int) ?? 0
        let totalHouses = (payload["total_houses"] as? Int) ?? houses.count
        let cards: [APIFarmHouseMonitoringCard] = houses.compactMap { item in
            guard let houseID = item["house_id"] as? Int, let houseNumber = item["house_number"] as? Int else {
                return nil
            }
            return APIFarmHouseMonitoringCard(
                houseID: houseID,
                houseNumber: houseNumber,
                averageTemperature: jsonDouble(from: item, keys: ["average_temperature", "temperature"]),
                humidity: jsonDouble(from: item, keys: ["humidity"]),
                staticPressure: jsonDouble(from: item, keys: ["static_pressure", "pressure"]),
                airflowPercentage: jsonDouble(from: item, keys: ["airflow_percentage", "ventilation_level"]),
                waterConsumption: jsonDouble(from: item, keys: ["water_consumption", "water"]),
                feedConsumption: jsonDouble(from: item, keys: ["feed_consumption", "feed"]),
                growthDay: item["growth_day"] as? Int,
                houseCurrentDay: item["current_day"] as? Int,
                activeAlarmsCount: (item["active_alarms_count"] as? Int) ?? 0
            )
        }
        diagnostic("fetchFarmMonitoringDashboard farmID=\(farmID) totalHouses=\(totalHouses) cards=\(cards.count) fresh=\(String(describing: envelope.meta)) samples=\(previewObject(cards.prefix(3).map { ["house": $0.houseNumber, "temp": String(describing: $0.averageTemperature), "humidity": String(describing: $0.humidity), "pressure": String(describing: $0.staticPressure), "airflow": String(describing: $0.airflowPercentage), "water": String(describing: $0.waterConsumption), "feed": String(describing: $0.feedConsumption)] }, maxChars: 1200))")
        return APIFarmMonitoringDashboardResult(
            totalHouses: totalHouses,
            alertsSummaryTotalActive: totalActiveAlerts,
            houses: cards,
            freshness: envelope.meta
        )
    }

    func fetchFarmMonitoringSnapshot(farmID: Int) async throws -> APIFarmMonitoringSnapshotResult {
        let data = try await request(
            path: "/api/farms/\(farmID)/houses/monitoring/snapshot/?mode=live",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 90
        )
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw APIClientError.decoding
        }
        let envelope = decodeEnvelope(root)
        let payload = envelope.payload
        guard let houses = payload["houses"] as? [[String: Any]] else {
            throw APIClientError.decoding
        }
        let mappedHouses = houses.compactMap { item -> APIFarmMonitoringSnapshotHouse? in
            guard
                let houseID = item["house_id"] as? Int,
                let houseNumber = item["house_number"] as? Int
            else { return nil }
            return APIFarmMonitoringSnapshotHouse(
                houseID: houseID,
                houseNumber: houseNumber,
                currentDay: item["current_day"] as? Int,
                averageTemperature: item["average_temperature"] as? Double,
                humidity: item["humidity"] as? Double,
                staticPressure: item["static_pressure"] as? Double,
                airflowPercentage: item["airflow_percentage"] as? Double,
                waterConsumption: item["water_consumption"] as? Double,
                feedConsumption: item["feed_consumption"] as? Double,
                isConnected: (item["is_connected"] as? Bool) ?? true,
                alarmStatus: (item["alarm_status"] as? String) ?? "normal"
            )
        }

        var alertsByHouseID: [Int: APIFarmMonitoringSnapshotAlert] = [:]
        if let alertsRaw = payload["alerts_by_house"] as? [String: Any] {
            for (houseIDRaw, alertRaw) in alertsRaw {
                guard
                    let houseID = Int(houseIDRaw),
                    let alert = alertRaw as? [String: Any]
                else { continue }
                alertsByHouseID[houseID] = APIFarmMonitoringSnapshotAlert(
                    houseID: houseID,
                    activeCount: (alert["active_count"] as? Int) ?? 0,
                    highestSeverity: (alert["highest_severity"] as? String) ?? "normal",
                    latestMessage: alert["latest_message"] as? String
                )
            }
        }
        return APIFarmMonitoringSnapshotResult(
            houses: mappedHouses,
            alertsByHouseID: alertsByHouseID,
            freshness: envelope.meta
        )
    }

    /// Unified iOS snapshot: all sensor data for a farm in one cache-consistent response.
    /// Replaces the three parallel fetchFarmMonitoringDashboard / fetchFarmHouseSensorData /
    /// fetchFarmMonitoringSnapshot calls and eliminates cross-cycle data inconsistency.
    func fetchFarmIOSSnapshot(farmID: Int) async throws -> APIFarmIOSSnapshotResult {
        let data = try await request(
            path: "/api/farms/\(farmID)/ios/snapshot/?mode=live",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 90
        )
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw APIClientError.decoding
        }
        let envelope = decodeEnvelope(root)
        let payload = envelope.payload
        let freshness = envelope.meta
        let rawMeta = root["meta"] as? [String: Any]

        let farmID = payload["farm_id"] as? Int ?? farmID
        let farmName = payload["farm_name"] as? String ?? ""
        let circuitOpen = (rawMeta?["circuit_open"] as? Bool) ?? false

        let rawHouses = payload["houses"] as? [[String: Any]] ?? []
        diagnostic("fetchFarmIOSSnapshot farmID=\(farmID) farmName=\(farmName) rawHouses=\(rawHouses.count) payloadKeys=\(payload.keys.sorted()) meta=\(String(describing: rawMeta))")
        let mappedHouses: [APIFarmIOSSnapshotHouse] = rawHouses.compactMap { h in
            guard let houseID = h["house_id"] as? Int else { return nil }
            func snapDouble(_ key: String) -> Double? {
                guard let raw = h[key] else { return nil }
                if let v = raw as? Double { return v }
                if let v = raw as? Int { return Double(v) }
                if let n = raw as? NSNumber { return n.doubleValue }
                if let s = raw as? String {
                    let t = s.trimmingCharacters(in: .whitespacesAndNewlines).replacingOccurrences(of: ",", with: "")
                    if t.isEmpty { return nil }
                    return Double(t)
                }
                return nil
            }
            let currentDay: Int? = (h["current_day"] as? Int)
                ?? (h["growth_day"] as? Int)
                ?? (h["age_days"] as? Int)
            return APIFarmIOSSnapshotHouse(
                houseID: houseID,
                houseNumber: (h["house_number"] as? Int) ?? houseID,
                currentDay: currentDay,
                averageTemperature: snapDouble("average_temperature"),
                humidity: snapDouble("humidity"),
                staticPressure: snapDouble("static_pressure"),
                airflowPercentage: snapDouble("airflow_percentage"),
                waterConsumption: snapDouble("water_consumption"),
                feedConsumption: snapDouble("feed_consumption"),
                isConnected: (h["is_connected"] as? Bool) ?? false,
                alarmStatus: (h["alarm_status"] as? String) ?? "normal",
                dataStatus: (h["data_status"] as? String) ?? "ok"
            )
        }
        if rawHouses.isEmpty {
            diagnostic("fetchFarmIOSSnapshot EMPTY houses rawPayload=\(previewObject(payload, maxChars: 1500))")
        } else {
            let samples = rawHouses.prefix(3).map { h in
                [
                    "house_id": h["house_id"] ?? "nil",
                    "house_number": h["house_number"] ?? "nil",
                    "temp": h["average_temperature"] ?? "nil",
                    "humidity": h["humidity"] ?? "nil",
                    "pressure": h["static_pressure"] ?? "nil",
                    "airflow": h["airflow_percentage"] ?? "nil",
                    "water": h["water_consumption"] ?? "nil",
                    "feed": h["feed_consumption"] ?? "nil",
                    "status": h["data_status"] ?? "nil"
                ]
            }
            diagnostic("fetchFarmIOSSnapshot mappedHouses=\(mappedHouses.count) samples=\(previewObject(samples, maxChars: 1500))")
        }

        var alertsByHouseID: [Int: APIFarmIOSSnapshotAlert] = [:]
        if let rawAlerts = payload["alerts_by_house"] as? [String: [String: Any]] {
            for (houseIDStr, alertData) in rawAlerts {
                guard let houseID = Int(houseIDStr) else { continue }
                alertsByHouseID[houseID] = APIFarmIOSSnapshotAlert(
                    houseID: houseID,
                    activeCount: (alertData["active_count"] as? Int) ?? 0,
                    highestSeverity: (alertData["highest_severity"] as? String) ?? "low",
                    latestMessage: alertData["latest_message"] as? String
                )
            }
        }

        let alertsSummary = payload["alerts_summary"] as? [String: Any] ?? [:]
        let alertsTotal = (alertsSummary["total_active"] as? Int) ?? 0

        return APIFarmIOSSnapshotResult(
            farmID: farmID,
            farmName: farmName,
            houses: mappedHouses,
            alertsByHouseID: alertsByHouseID,
            alertsSummaryTotalActive: alertsTotal,
            freshness: freshness,
            circuitOpen: circuitOpen
        )
    }

    /// Web parity endpoint used by frontend dashboard cards.
    /// Returns monitoring by house number for a farm.
    func fetchFarmHouseSensorData(farmID: Int) async throws -> [Int: APIMonitoring] {
        let data = try await request(
            path: "/api/farms/\(farmID)/house-sensor-data/",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let houses = json["houses"] as? [String: Any]
        else {
            throw APIClientError.decoding
        }

        func sensorCurrent(_ sensors: [String: Any], _ key: String) -> Double? {
            guard let sensor = sensors[key] as? [String: Any] else { return nil }
            if let value = sensor["current"] as? Double { return value }
            if let value = sensor["current"] as? Int { return Double(value) }
            if let value = sensor["current"] as? String { return Double(value) }
            return nil
        }

        var result: [Int: APIMonitoring] = [:]
        for (houseNumberKey, rawValue) in houses {
            guard
                let houseNumber = Int(houseNumberKey),
                let housePayload = rawValue as? [String: Any],
                let sensors = housePayload["sensors"] as? [String: Any]
            else {
                continue
            }
            let canonical = housePayload["canonical"] as? [String: Any]

            let monitoring = APIMonitoring(
                averageTemperature: (canonical?["temperature"] as? Double) ?? sensorCurrent(sensors, "temperature"),
                humidity: (canonical?["humidity"] as? Double) ?? sensorCurrent(sensors, "humidity"),
                staticPressure: (canonical?["static_pressure"] as? Double) ?? sensorCurrent(sensors, "static_pressure"),
                waterConsumption: (canonical?["water_consumption"] as? Double) ?? sensorCurrent(sensors, "water_consumption") ?? sensorCurrent(sensors, "water"),
                feedConsumption: (canonical?["feed_consumption"] as? Double) ?? sensorCurrent(sensors, "feed_consumption"),
                airflowPercentage: (canonical?["airflow_percentage"] as? Double) ?? sensorCurrent(sensors, "airflow_percentage") ?? sensorCurrent(sensors, "airflow") ?? sensorCurrent(sensors, "ventilation_level")
            )
            result[houseNumber] = monitoring
        }
        return result
    }

    func refreshFarmMonitoringNow(farmID: Int) async throws -> APIFreshnessMeta? {
        let data = try await request(
            path: "/api/farms/\(farmID)/houses/monitoring/refresh/",
            method: "POST",
            payload: [:],
            requiresAuth: true
        )
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw APIClientError.decoding
        }
        return parseMeta(json["meta"] as? [String: Any])
    }

    func triggerFarmScrape(rotemFarmID: String) async throws {
        _ = try await request(
            path: "/api/rotem/scraper/scrape_farm/",
            method: "POST",
            payload: ["farm_id": rotemFarmID],
            requiresAuth: true
        )
    }

    func fetchHouses(farmID: Int) async throws -> [APIHouse] {
        let data = try await request(path: "/api/farms/\(farmID)/houses/", method: "GET", payload: nil, requiresAuth: true)
        guard let items = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else {
            throw APIClientError.decoding
        }
        return items.compactMap { item in
            guard let id = item["id"] as? Int else { return nil }
            return APIHouse(
                id: id,
                houseNumber: (item["house_number"] as? Int) ?? id,
                currentDay: (item["current_day"] as? Int) ?? ((item["current_age_days"] as? Int) ?? 0),
                isActive: (item["is_active"] as? Bool) ?? true
            )
        }
    }

    /// Per-house latest monitoring defaults to direct Rotem data via the backend.
    func fetchLatestMonitoring(houseID: Int, mode: String = "live") async throws -> APIMonitoring? {
        let safeMode = mode.lowercased() == "live" ? "live" : "cached"
        do {
            let data = try await request(
                path: "/api/houses/\(houseID)/monitoring/latest/?mode=\(safeMode)",
                method: "GET",
                payload: nil,
                requiresAuth: true,
                timeoutOverride: 90
            )
            guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                return nil
            }
            let item = decodeEnvelope(root).payload
            let env = item["environment"] as? [String: Any] ?? [:]
            let consumption = item["consumption"] as? [String: Any] ?? [:]
            let ventilation = item["ventilation"] as? [String: Any] ?? [:]
            func firstNonNil(_ primary: Double?, _ fallbacks: Double?...) -> Double? {
                if let v = primary { return v }
                for f in fallbacks {
                    if let v = f { return v }
                }
                return nil
            }
            return APIMonitoring(
                averageTemperature: firstNonNil(
                    jsonDouble(from: item, keys: ["average_temperature", "avg_temperature", "temperature"]),
                    jsonDouble(from: env, keys: ["average_temperature", "avg_temperature", "temperature"])
                ),
                humidity: firstNonNil(
                    jsonDouble(from: item, keys: ["humidity", "relative_humidity", "rh"]),
                    jsonDouble(from: env, keys: ["humidity", "relative_humidity", "rh"])
                ),
                staticPressure: firstNonNil(
                    jsonDouble(from: item, keys: ["static_pressure", "pressure"]),
                    jsonDouble(from: env, keys: ["static_pressure", "pressure"])
                ),
                waterConsumption: firstNonNil(
                    jsonDouble(from: item, keys: ["water_consumption", "water_today", "water"]),
                    jsonDouble(from: consumption, keys: ["water_consumption", "water"])
                ),
                feedConsumption: firstNonNil(
                    jsonDouble(from: item, keys: ["feed_consumption", "feed_today", "feed"]),
                    jsonDouble(from: consumption, keys: ["feed_consumption", "feed"])
                ),
                airflowPercentage: firstNonNil(
                    jsonDouble(from: item, keys: ["airflow_percentage", "ventilation_level", "ventilation"]),
                    jsonDouble(from: ventilation, keys: ["airflow_percentage", "ventilation_level", "ventilation_level_pct"])
                )
            )
        } catch APIClientError.server {
            return nil
        }
    }

    func fetchWaterAlerts(houseID: Int) async throws -> [APIWaterAlert] {
        let data = try await request(path: "/api/houses/\(houseID)/water/alerts/?include_resolved=true", method: "GET", payload: nil, requiresAuth: true)
        let items = try decodeCollection(data: data)
        return items.compactMap { item in
            guard let id = item["id"] as? Int else { return nil }
            let createdAt = (item["created_at"] as? String).flatMap(parseISODate)
            return APIWaterAlert(
                id: id,
                severity: (item["severity"] as? String) ?? "info",
                message: (item["message"] as? String) ?? "Alert",
                houseNumber: item["house_number"] as? Int,
                createdAt: createdAt,
                isAcknowledged: (item["is_acknowledged"] as? Bool) ?? false,
                increasePercentage: item["increase_percentage"] as? Double
            )
        }
    }

    func fetchFlocks(farmID: Int) async throws -> [APIFlock] {
        let data = try await request(
            path: "/api/flocks/?farm_id=\(farmID)",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        let items = try decodeCollection(data: data)
        return items.compactMap(mapFlock)
    }

    func fetchFlockDetail(flockID: Int) async throws -> APIFlock {
        let data = try await request(
            path: "/api/flocks/\(flockID)/",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        guard
            let item = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let flock = mapFlock(item)
        else {
            throw APIClientError.decoding
        }
        return flock
    }

    func fetchFlockPerformance(flockID: Int) async throws -> [APIFlockPerformance] {
        let data = try await request(
            path: "/api/flocks/\(flockID)/performance/",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        let items = try decodeCollection(data: data)
        return items.compactMap(mapFlockPerformance)
    }

    func fetchTasks(houseID: Int) async throws -> [APITask] {
        let data = try await request(
            path: "/api/houses/\(houseID)/tasks/",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        let items = try decodeCollection(data: data)
        return items.compactMap { item in
            guard let id = item["id"] as? Int else { return nil }
            return APITask(
                id: id,
                houseID: (item["house"] as? Int),
                taskName: (item["task_name"] as? String) ?? "Task \(id)",
                description: (item["description"] as? String) ?? "",
                dayOffset: (item["day_offset"] as? Int) ?? 0,
                isCompleted: (item["is_completed"] as? Bool) ?? false,
                completedBy: (item["completed_by"] as? String) ?? "",
                notes: (item["notes"] as? String) ?? ""
            )
        }
    }

    func updateTaskStatus(taskID: Int, status: String, notes: String? = nil) async throws {
        var payload: [String: Any] = ["status": status]
        if let notes, !notes.isEmpty {
            payload["notes"] = notes
        }
        _ = try await request(
            path: "/api/tasks/\(taskID)/status/",
            method: "POST",
            payload: payload,
            requiresAuth: true
        )
    }

    func fetchWorkers(farmID: Int) async throws -> [APIWorker] {
        let data = try await request(
            path: "/api/workers/?farm_id=\(farmID)",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        let items = try decodeCollection(data: data)
        return items.compactMap { item in
            guard let id = item["id"] as? Int else { return nil }
            return APIWorker(
                id: id,
                name: (item["name"] as? String) ?? "Worker \(id)",
                role: (item["role"] as? String) ?? "Worker",
                phone: (item["phone"] as? String) ?? "",
                farmID: farmID,
                isActive: (item["is_active"] as? Bool) ?? true
            )
        }
    }

    func fetchPrograms() async throws -> [APIProgram] {
        let data = try await request(path: "/api/programs/", method: "GET", payload: nil, requiresAuth: true)
        let items = try decodeCollection(data: data)
        return items.compactMap { item in
            guard let id = item["id"] as? Int else { return nil }
            return APIProgram(
                id: id,
                name: (item["name"] as? String) ?? "Program \(id)",
                durationDays: (item["duration_days"] as? Int) ?? 0,
                totalTasks: (item["total_tasks"] as? Int) ?? 0,
                isActive: (item["is_active"] as? Bool) ?? false
            )
        }
    }

    func updateProgram(programID: Int, isActive: Bool) async throws {
        _ = try await request(
            path: "/api/programs/\(programID)/",
            method: "PATCH",
            payload: ["is_active": isActive],
            requiresAuth: true
        )
    }

    func fetchProgramTasks(programID: Int, day: Int? = nil) async throws -> [APIProgramTask] {
        let endpoint: String
        if let day {
            endpoint = "/api/programs/\(programID)/tasks/day/\(day)/"
        } else {
            endpoint = "/api/programs/\(programID)/tasks/"
        }
        let data = try await request(path: endpoint, method: "GET", payload: nil, requiresAuth: true)
        let items = try decodeCollection(data: data)
        return items.compactMap { item in
            guard let id = item["id"] as? Int else { return nil }
            return APIProgramTask(
                id: id,
                day: (item["day"] as? Int) ?? 0,
                title: (item["title"] as? String) ?? "Task \(id)",
                priority: (item["priority"] as? String) ?? "medium",
                estimatedDuration: (item["estimated_duration"] as? Int) ?? 0,
                isRequired: (item["is_required"] as? Bool) ?? false
            )
        }
    }

    func assignProgram(programID: Int, farmIDs: [Int], houseIDs: [Int]) async throws {
        _ = try await request(
            path: "/api/programs/\(programID)/assign/",
            method: "POST",
            payload: ["farm_ids": farmIDs, "house_ids": houseIDs, "regenerate_tasks": true],
            requiresAuth: true
        )
    }

    func fetchFarmIntegrationStatus(farmID: Int) async throws -> APIFarmIntegrationStatus {
        let data = try await request(
            path: "/api/farms/\(farmID)/integration_status/",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw APIClientError.decoding
        }
        return APIFarmIntegrationStatus(
            farmID: farmID,
            integrationType: (json["integration_type"] as? String) ?? "none",
            integrationStatus: (json["status"] as? String) ?? "unknown",
            lastSync: (json["last_sync"] as? String).flatMap(parseISODate)
        )
    }

    func updateFarmIntegration(farmID: Int, integrationType: String, username: String?, password: String?) async throws {
        var payload: [String: Any] = ["integration_type": integrationType]
        if let username { payload["rotem_username"] = username }
        if let password { payload["rotem_password"] = password }
        _ = try await request(
            path: "/api/farms/\(farmID)/configure_integration/",
            method: "POST",
            payload: payload,
            requiresAuth: true
        )
    }

    func fetchHouseMonitoringHistory(
        houseID: Int,
        limit: Int,
        startDate: Date? = nil,
        endDate: Date? = nil
    ) async throws -> [APIHouseMonitoringPoint] {
        let safeLimit = min(max(limit, 1), 500)
        var query = "limit=\(safeLimit)"
        if let startDate {
            query += "&start_date=\(Self.isoFormatter.string(from: startDate))"
        }
        if let endDate {
            query += "&end_date=\(Self.isoFormatter.string(from: endDate))"
        }
        let data = try await request(
            path: "/api/houses/\(houseID)/monitoring/history/?mode=live&\(query)",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 90
        )
        guard
            let root = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        else {
            throw APIClientError.decoding
        }
        let payload = decodeEnvelope(root).payload
        guard let results = payload["results"] as? [[String: Any]] else {
            throw APIClientError.decoding
        }
        return results.compactMap { item in
            let timestampString = (item["source_timestamp"] as? String) ?? (item["timestamp"] as? String)
            guard let timestamp = timestampString.flatMap(parseISODate) else { return nil }
            return APIHouseMonitoringPoint(
                timestamp: timestamp,
                averageTemperature: item["average_temperature"] as? Double,
                humidity: item["humidity"] as? Double,
                staticPressure: item["static_pressure"] as? Double,
                airflowPercentage: item["airflow_percentage"] as? Double,
                waterConsumption: item["water_consumption"] as? Double,
                feedConsumption: item["feed_consumption"] as? Double
            )
        }
        .sorted(by: { $0.timestamp < $1.timestamp })
    }

    func fetchHouseMonitoringKpis(houseID: Int) async throws -> APIHouseMonitoringKpis {
        let data = try await request(
            path: "/api/houses/\(houseID)/monitoring/kpis/?mode=live",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 90
        )
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw APIClientError.decoding
        }
        let json = decodeEnvelope(root).payload
        let heater = json["heater_runtime"] as? [String: Any]
        let waterDod = json["water_day_over_day"] as? [String: Any]
        let feedDod = json["feed_day_over_day"] as? [String: Any]
        let ratio = json["water_feed_ratio"] as? [String: Any]
        return APIHouseMonitoringKpis(
            heaterHours24h: heater?["hours_24h"] as? Double,
            waterToday: waterDod?["current"] as? Double,
            waterYesterday: waterDod?["previous"] as? Double,
            feedToday: feedDod?["current"] as? Double,
            feedYesterday: feedDod?["previous"] as? Double,
            waterFeedRatioToday: ratio?["today"] as? Double
        )
    }

    /// Farm-level water compare: one Rotem login, all houses, cache-backed.
    /// Returns a dict keyed by backend house ID → list of water history points.
    func fetchFarmWaterCompare(farmID: Int, days: Int = 5) async throws -> [Int: [APIRotemWaterHistoryPoint]] {
        let safeDays = min(max(days, 1), 30)
        // This endpoint does one Rotem login + N sequential house fetches on the backend.
        // Allow up to 60 s for an 8-house farm on a cold cache.
        let data = try await request(
            path: "/api/rotem/farms/\(farmID)/water-compare/?days=\(safeDays)",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 60
        )
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let housesRaw = json["houses"] as? [String: Any]
        else {
            throw APIClientError.decoding
        }
        var result: [Int: [APIRotemWaterHistoryPoint]] = [:]
        for (houseIDStr, rowsAny) in housesRaw {
            guard
                let houseID = Int(houseIDStr),
                let rows = rowsAny as? [[String: Any]]
            else { continue }
            var points: [APIRotemWaterHistoryPoint] = []
            for row in rows {
                let consumption = jsonDouble(from: row, keys: ["consumption_avg", "consumption", "water_consumption"]) ?? 0
                let date = (row["date"] as? String).flatMap(parseISODate)
                let growthDay = row["growth_day"] as? Int
                points.append(APIRotemWaterHistoryPoint(date: date, growthDay: growthDay, consumptionAvg: consumption))
            }
            result[houseID] = points
        }
        return result
    }

    /// Direct RotemNet water history (non-DB): sourced from scraper command stream.
    func fetchRotemWaterHistory(houseID: Int, days: Int = 5, allHistory: Bool = false) async throws -> [APIRotemWaterHistoryPoint] {
        let query: String
        if allHistory {
            query = "house_id=\(houseID)&all_history=true"
        } else {
            let safeDays = min(max(days, 1), 30)
            query = "house_id=\(houseID)&days=\(safeDays)"
        }
        let data = try await request(
            path: "/api/rotem/daily-summaries/water-history/?\(query)",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 90
        )
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let rows = json["water_history"] as? [[String: Any]]
        else {
            throw APIClientError.decoding
        }
        var result: [APIRotemWaterHistoryPoint] = []
        result.reserveCapacity(rows.count)
        var skippedNilConsumption = 0
        var maxParsed: Double = 0
        var firstConsumptionDebug = "nil"
        if let first = rows.first, let v = first["consumption_avg"] ?? first["consumption"] {
            firstConsumptionDebug = "\(Swift.type(of: v))|\(String(describing: v))"
        }
        for row in rows {
            let consumption = jsonDouble(from: row, keys: ["consumption_avg", "consumption", "water_consumption"])
            if consumption == nil { skippedNilConsumption += 1 }
            guard let consumption else { continue }
            maxParsed = max(maxParsed, consumption)
            let date = (row["date"] as? String).flatMap(parseISODate)
            let growthDay = row["growth_day"] as? Int
            result.append(
                APIRotemWaterHistoryPoint(
                    date: date,
                    growthDay: growthDay,
                    consumptionAvg: consumption
                )
            )
        }
        // #region agent log
        FarmDebugLog.post(
            hypothesisId: "A",
            location: "APIClient.swift:fetchRotemWaterHistory",
            message: "water_history parse",
            data: [
                "houseID": houseID,
                "rawRows": rows.count,
                "parsedRows": result.count,
                "skippedNilConsumption": skippedNilConsumption,
                "firstConsumptionField": firstConsumptionDebug,
                "maxParsedConsumption": maxParsed
            ]
        )
        // #endregion
        return result
    }

    /// Direct RotemNet temperature history (CommandID 35 via backend facade).
    func fetchRotemTemperatureHistory(houseID: Int) async throws -> [APIRotemTemperatureHistoryPoint] {
        let data = try await request(
            path: "/api/rotem/daily-summaries/temperature-history/?house_id=\(houseID)",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 90
        )
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let rows = json["temperature_history"] as? [[String: Any]]
        else {
            throw APIClientError.decoding
        }
        return rows.compactMap { row in
            guard let growthDay = row["growth_day"] as? Int else { return nil }
            let date = (row["date"] as? String).flatMap(parseISODate)
            return APIRotemTemperatureHistoryPoint(
                date: date,
                growthDay: growthDay,
                minValue: row["min_value"] as? Double,
                avgValue: row["avg_value"] as? Double,
                maxValue: row["max_value"] as? Double
            )
        }
        .sorted(by: { $0.growthDay < $1.growthDay })
    }

    /// Direct RotemNet feed history (CommandID 41 via backend facade).
    func fetchRotemFeedHistory(houseID: Int, days: Int = 5, allHistory: Bool = false) async throws -> [APIRotemFeedHistoryPoint] {
        let query: String
        if allHistory {
            query = "house_id=\(houseID)&all_history=true"
        } else {
            let safeDays = min(max(days, 1), 30)
            query = "house_id=\(houseID)&days=\(safeDays)"
        }
        let data = try await request(
            path: "/api/rotem/daily-summaries/feed-history/?\(query)",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 90
        )
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let rows = json["feed_history"] as? [[String: Any]]
        else {
            throw APIClientError.decoding
        }
        return rows.compactMap { row in
            guard let growthDay = row["growth_day"] as? Int else { return nil }
            let total = jsonDouble(from: row, keys: ["daily_feed_total", "daily_feed", "feed_consumption"]) ?? 0.0
            let date = (row["date"] as? String).flatMap(parseISODate)
            return APIRotemFeedHistoryPoint(
                date: date,
                growthDay: growthDay,
                dailyFeedTotal: total,
                feedPerBird: row["feed_per_bird"] as? Double,
                changePercent: row["change_percent"] as? Double
            )
        }
        .sorted(by: { $0.growthDay < $1.growthDay })
    }

    func fetchHouseHeaterHistory(houseID: Int, days: Int = 5) async throws -> [DailyResourcePoint] {
        let safeDays = min(max(days, 1), 30)
        let data = try await request(
            path: "/api/houses/\(houseID)/heater-history/?mode=live",
            method: "GET",
            payload: nil,
            requiresAuth: true,
            timeoutOverride: 90
        )
        guard
            let root = try JSONSerialization.jsonObject(with: data) as? [String: Any]
        else {
            return []
        }
        let json = decodeEnvelope(root).payload
        guard
            let heaterHistory = json["heater_history"] as? [String: Any],
            let daily = heaterHistory["daily"] as? [[String: Any]]
        else {
            return []
        }
        let points: [DailyResourcePoint] = daily.compactMap { item in
            guard let growthDay = item["growth_day"] as? Int else { return nil }
            let date = (item["date"] as? String).flatMap(parseISODate) ?? Date()
            let hours = jsonDouble(from: item, keys: ["total_hours", "hours"]) ?? 0
            return DailyResourcePoint(day: growthDay, date: date, value: hours, target: nil, isAnomaly: false)
        }.sorted(by: { $0.date < $1.date })
        return Array(points.suffix(safeDays))
    }

    func acknowledgeWaterAlert(id: Int) async throws {
        _ = try await request(path: "/api/houses/water/alerts/\(id)/acknowledge/", method: "POST", payload: [:], requiresAuth: true)
    }

    func snoozeWaterAlert(id: Int, hours: Int) async throws {
        _ = try await request(path: "/api/houses/water/alerts/\(id)/snooze/", method: "POST", payload: ["hours": max(1, hours)], requiresAuth: true)
    }

    func resolveWaterAlert(id: Int) async throws {
        _ = try await request(path: "/api/houses/water/alerts/\(id)/resolve/", method: "POST", payload: [:], requiresAuth: true)
    }

    private func decodeCollection(data: Data) throws -> [[String: Any]] {
        let json = try JSONSerialization.jsonObject(with: data)
        if let array = json as? [[String: Any]] {
            return array
        }
        if let object = json as? [String: Any], let results = object["results"] as? [[String: Any]] {
            return results
        }
        throw APIClientError.decoding
    }

    private func decodeEnvelope(_ root: [String: Any]) -> (payload: [String: Any], meta: APIFreshnessMeta?) {
        if let payload = root["data"] as? [String: Any] {
            return (payload, parseMeta(root["meta"] as? [String: Any]))
        }
        return (root, nil)
    }

    private func parseMeta(_ raw: [String: Any]?) -> APIFreshnessMeta? {
        guard let raw else { return nil }
        let sourceTimestamp = (raw["source_timestamp"] as? String).flatMap(parseISODate)
        let fetchedAt = (raw["fetched_at"] as? String).flatMap(parseISODate)
        return APIFreshnessMeta(
            sourceTimestamp: sourceTimestamp,
            fetchedAt: fetchedAt,
            ageSeconds: raw["age_seconds"] as? Int,
            isStale: (raw["is_stale"] as? Bool) ?? false,
            refreshState: (raw["refresh_state"] as? String) ?? "idle",
            canRefreshNow: (raw["can_refresh_now"] as? Bool) ?? true
        )
    }

    private func mapFlock(_ item: [String: Any]) -> APIFlock? {
        guard let id = item["id"] as? Int else { return nil }
        let batchNumber = (item["batch_number"] as? String) ?? "Flock \(id)"
        let breedName = (item["breed_name"] as? String)
            ?? ((item["breed"] as? [String: Any])?["name"] as? String)
            ?? "Unknown breed"
        return APIFlock(
            id: id,
            houseID: item["house"] as? Int,
            batchNumber: batchNumber,
            breedName: breedName,
            arrivalDate: (item["arrival_date"] as? String).flatMap(parseISODate),
            expectedHarvestDate: (item["expected_harvest_date"] as? String).flatMap(parseISODate),
            currentAgeDays: (item["current_age_days"] as? Int) ?? 0,
            initialChickenCount: (item["initial_chicken_count"] as? Int) ?? 0,
            currentChickenCount: (item["current_chicken_count"] as? Int) ?? 0,
            isActive: (item["is_active"] as? Bool) ?? false,
            status: (item["status"] as? String) ?? "unknown",
            mortalityRate: item["mortality_rate"] as? Double
        )
    }

    private func mapFlockPerformance(_ item: [String: Any]) -> APIFlockPerformance? {
        guard let id = item["id"] as? Int else { return nil }
        return APIFlockPerformance(
            id: id,
            flockID: item["flock"] as? Int,
            recordDate: (item["record_date"] as? String).flatMap(parseISODate),
            flockAgeDays: item["flock_age_days"] as? Int,
            averageWeightGrams: item["average_weight_grams"] as? Double,
            feedConversionRatio: item["feed_conversion_ratio"] as? Double,
            dailyFeedConsumptionKg: item["daily_feed_consumption_kg"] as? Double,
            dailyWaterConsumptionLiters: item["daily_water_consumption_liters"] as? Double,
            mortalityRate: item["mortality_rate"] as? Double,
            livability: item["livability"] as? Double
        )
    }

    /// JSON numbers may decode as `Double`, `Int`, or `NSNumber`.
    private func jsonDouble(from row: [String: Any], keys: [String]) -> Double? {
        for key in keys {
            guard let raw = row[key] else { continue }
            if raw is NSNull { continue }
            if let d = raw as? Double { return d }
            if let i = raw as? Int { return Double(i) }
            if let n = raw as? NSNumber { return n.doubleValue }
            if let s = raw as? String {
                let t = s.trimmingCharacters(in: .whitespacesAndNewlines).replacingOccurrences(of: ",", with: "")
                if t.isEmpty { continue }
                if let d = Double(t) { return d }
            }
        }
        return nil
    }

    private func parseISODate(_ value: String) -> Date? {
        if let date = Self.isoFormatterWithFractional.date(from: value) {
            return date
        }
        if let date = Self.isoFormatter.date(from: value) {
            return date
        }
        // Accept yyyy-MM-dd date-only payloads from DRF serializers.
        return Self.dateOnlyFormatter.date(from: value)
    }

    private static let isoFormatterWithFractional: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatter
    }()

    private static let isoFormatter: ISO8601DateFormatter = {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        return formatter
    }()

    private static let dateOnlyFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = TimeZone(secondsFromGMT: 0)
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter
    }()

    private func request(
        path: String,
        method: String,
        payload: [String: Any]?,
        requiresAuth: Bool,
        timeoutOverride: TimeInterval? = nil
    ) async throws -> Data {
        guard let url = URL(string: path, relativeTo: baseURL) else {
            throw APIClientError.invalidURL
        }

        let started = Date()

        var request = URLRequest(url: url)
        request.httpMethod = method
        // Prevent views from appearing frozen when upstream endpoints stall.
        request.timeoutInterval = timeoutOverride ?? 12
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        if requiresAuth {
            guard let token else { throw APIClientError.unauthorized }
            request.setValue("Token \(token)", forHTTPHeaderField: "Authorization")
        }
        if let payload {
            request.httpBody = try JSONSerialization.data(withJSONObject: payload)
        }

        log("-> \(method) \(url.absoluteString) auth=\(requiresAuth)")
        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.server("No response from server.")
        }
        let elapsed = Date().timeIntervalSince(started)
        log("<- \(http.statusCode) \(url.absoluteString) \(String(format: "%.2fs", elapsed)) body=\(previewBody(data))")

        switch http.statusCode {
        case 200..<300:
            return data
        case 401:
            throw APIClientError.unauthorized
        default:
            if
                let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                let message = (json["error"] as? String) ?? (json["message"] as? String)
            {
                throw APIClientError.server(message)
            }
            throw APIClientError.server("Request failed (\(http.statusCode)).")
        }
    }

    private func log(_ message: String) {
        guard verboseLogging else { return }
        print("[APIClient] \(message)")
    }

    private func diagnostic(_ message: String) {
        guard diagnosticsEnabled else { return }
        print("[APIClient][diagnostic] \(message)")
    }

    private func previewBody(_ data: Data, maxChars: Int = 400) -> String {
        guard !data.isEmpty else { return "<empty>" }
        let text = String(decoding: data, as: UTF8.self)
        if text.count <= maxChars {
            return text
        }
        return String(text.prefix(maxChars)) + "..."
    }

    private func previewObject(_ value: Any, maxChars: Int = 1000) -> String {
        let data = (try? JSONSerialization.data(withJSONObject: value, options: [.prettyPrinted]))
        let text = data.map { String(decoding: $0, as: UTF8.self) } ?? String(describing: value)
        if text.count <= maxChars {
            return text
        }
        return String(text.prefix(maxChars)) + "..."
    }
}

// #region agent log
/// Sends one JSON payload to the Cursor debug ingest (iOS Simulator → host).
enum FarmDebugLog {
    private static let endpoint = URL(string: "http://127.0.0.1:7446/ingest/1f94348e-18e7-4829-95a8-c88970a05b9d")!
    private static let sessionId = "ed7eeb"
    private static let isEnabled = (ProcessInfo.processInfo.environment["ROTEM_IOS_AGENT_LOGS"] ?? "").lowercased() == "true"

    static func post(hypothesisId: String, location: String, message: String, data: [String: Any]) {
        guard isEnabled else { return }
        Task.detached {
            var payload: [String: Any] = [
                "sessionId": sessionId,
                "timestamp": Int(Date().timeIntervalSince1970 * 1000),
                "hypothesisId": hypothesisId,
                "location": location,
                "message": message,
                "data": data
            ]
            guard let body = try? JSONSerialization.data(withJSONObject: payload) else { return }
            var req = URLRequest(url: endpoint)
            req.httpMethod = "POST"
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.setValue(sessionId, forHTTPHeaderField: "X-Debug-Session-Id")
            req.httpBody = body
            _ = try? await URLSession.shared.data(for: req)
        }
    }
}
// #endregion
