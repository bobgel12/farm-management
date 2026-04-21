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
            // Keep aligned with frontend/src/services/api.ts production URL.
            return "https://farm-management-production.up.railway.app"
        }
    }
}

actor APIClient {
    private let session: URLSession
    private let tokenStore: TokenStore
    private var baseURL: URL
    private var token: String?

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
                activeHouses: (item["active_houses"] as? Int) ?? 0
            )
        }
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

    func fetchHouseMonitoringHistory(houseID: Int, limit: Int) async throws -> [APIHouseMonitoringPoint] {
        let safeLimit = min(max(limit, 1), 500)
        let data = try await request(
            path: "/api/houses/\(houseID)/monitoring/history/?limit=\(safeLimit)",
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
                airflowPercentage: item["airflow_percentage"] as? Double
            )
        }
        .sorted(by: { $0.timestamp < $1.timestamp })
    }

    func acknowledgeWaterAlert(id: Int) async throws {
        _ = try await request(path: "/api/houses/water/alerts/\(id)/acknowledge/", method: "POST", payload: [:], requiresAuth: true)
    }

    func snoozeWaterAlert(id: Int, hours: Int) async throws {
        _ = try await request(path: "/api/houses/water/alerts/\(id)/snooze/", method: "POST", payload: ["hours": max(1, hours)], requiresAuth: true)
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

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.server("No response from server.")
        }

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
}
