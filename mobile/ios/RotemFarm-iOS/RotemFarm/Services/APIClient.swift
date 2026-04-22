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
    let waterConsumption: Double?
    let feedConsumption: Double?
    let growthDay: Int?
    let houseCurrentDay: Int?
    let activeAlarmsCount: Int
}

struct APIFarmMonitoringDashboardResult {
    let totalHouses: Int
    let alertsSummaryTotalActive: Int
    let houses: [APIFarmHouseMonitoringCard]
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
            path: "/api/farms/\(farmID)/houses/monitoring/dashboard/",
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
        let alertsSummary = json["alerts_summary"] as? [String: Any]
        let totalActiveAlerts = (alertsSummary?["total_active"] as? Int) ?? 0
        let totalHouses = (json["total_houses"] as? Int) ?? houses.count
        let cards: [APIFarmHouseMonitoringCard] = houses.compactMap { item in
            guard let houseID = item["house_id"] as? Int, let houseNumber = item["house_number"] as? Int else {
                return nil
            }
            return APIFarmHouseMonitoringCard(
                houseID: houseID,
                houseNumber: houseNumber,
                averageTemperature: item["average_temperature"] as? Double,
                waterConsumption: item["water_consumption"] as? Double,
                feedConsumption: item["feed_consumption"] as? Double,
                growthDay: item["growth_day"] as? Int,
                houseCurrentDay: item["current_day"] as? Int,
                activeAlarmsCount: (item["active_alarms_count"] as? Int) ?? 0
            )
        }
        return APIFarmMonitoringDashboardResult(
            totalHouses: totalHouses,
            alertsSummaryTotalActive: totalActiveAlerts,
            houses: cards
        )
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

    func fetchLatestMonitoring(houseID: Int) async throws -> APIMonitoring? {
        do {
            let data = try await request(path: "/api/houses/\(houseID)/monitoring/latest/", method: "GET", payload: nil, requiresAuth: true)
            guard let item = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                return nil
            }
            return APIMonitoring(
                averageTemperature: item["average_temperature"] as? Double,
                humidity: item["humidity"] as? Double,
                staticPressure: item["static_pressure"] as? Double,
                waterConsumption: item["water_consumption"] as? Double,
                feedConsumption: item["feed_consumption"] as? Double,
                airflowPercentage: item["airflow_percentage"] as? Double
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
            path: "/api/houses/\(houseID)/monitoring/history/?\(query)",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let results = json["results"] as? [[String: Any]]
        else {
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
            path: "/api/houses/\(houseID)/monitoring/kpis/",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        guard let json = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
            throw APIClientError.decoding
        }
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

    /// Direct RotemNet water history (non-DB): sourced from scraper command stream.
    func fetchRotemWaterHistory(houseID: Int, days: Int = 5) async throws -> [APIRotemWaterHistoryPoint] {
        let safeDays = min(max(days, 1), 30)
        let data = try await request(
            path: "/api/rotem/daily-summaries/water-history/?house_id=\(houseID)&days=\(safeDays)",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let rows = json["water_history"] as? [[String: Any]]
        else {
            throw APIClientError.decoding
        }
        return rows.compactMap { row in
            let consumption = (row["consumption_avg"] as? Double)
                ?? (row["consumption"] as? Double)
                ?? (row["water_consumption"] as? Double)
            guard let consumption else { return nil }
            let date = (row["date"] as? String).flatMap(parseISODate)
            let growthDay = row["growth_day"] as? Int
            return APIRotemWaterHistoryPoint(
                date: date,
                growthDay: growthDay,
                consumptionAvg: consumption
            )
        }
    }

    func fetchHouseHeaterHistory(houseID: Int) async throws -> [DailyResourcePoint] {
        let data = try await request(
            path: "/api/houses/\(houseID)/heater-history/",
            method: "GET",
            payload: nil,
            requiresAuth: true
        )
        guard
            let json = try JSONSerialization.jsonObject(with: data) as? [String: Any],
            let heaterHistory = json["heater_history"] as? [String: Any],
            let daily = heaterHistory["daily"] as? [[String: Any]]
        else {
            return []
        }
        return daily.compactMap { item in
            guard let growthDay = item["growth_day"] as? Int else { return nil }
            let date = (item["date"] as? String).flatMap(parseISODate) ?? Date()
            let hours = (item["total_hours"] as? Double) ?? 0
            return DailyResourcePoint(day: growthDay, date: date, value: hours, target: nil, isAnomaly: false)
        }.sorted(by: { $0.day < $1.day })
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
        requiresAuth: Bool
    ) async throws -> Data {
        guard let url = URL(string: path, relativeTo: baseURL) else {
            throw APIClientError.invalidURL
        }

        let started = Date()

        var request = URLRequest(url: url)
        request.httpMethod = method
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

    private func previewBody(_ data: Data, maxChars: Int = 400) -> String {
        guard !data.isEmpty else { return "<empty>" }
        let text = String(decoding: data, as: UTF8.self)
        if text.count <= maxChars {
            return text
        }
        return String(text.prefix(maxChars)) + "..."
    }
}
