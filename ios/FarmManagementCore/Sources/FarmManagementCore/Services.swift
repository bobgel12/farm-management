import Foundation

public final class AuthService {
    private let client: APIClient

    public init(client: APIClient) {
        self.client = client
    }

    public func login(username: String, password: String) async throws -> LoginResponse {
        let payload = ["username": username, "password": password]
        let data = try JSONSerialization.data(withJSONObject: payload)
        return try await client.request(path: "auth/login/", method: "POST", body: data, authenticated: false)
    }

    public func currentUser() async throws -> AuthUser {
        let response: UserInfoResponse = try await client.request(path: "auth/user/")
        return response.user
    }
}

public final class FarmService {
    private let client: APIClient

    public init(client: APIClient) {
        self.client = client
    }

    public func fetchFarms() async throws -> [FarmSummary] {
        let response: FlexibleListResponse<FarmSummary> = try await client.request(path: "farms/")
        return response.values
    }

    public func fetchFarmDetail(id: Int) async throws -> FarmDetail {
        do {
            return try await client.request(path: "farms/\(id)/")
        } catch APIError.server(let statusCode, _) where statusCode >= 500 || statusCode == 404 {
            do {
                // Backend has both router and legacy farm endpoints; fall back when detail route fails.
                return try await client.request(path: "farms-legacy/\(id)/")
            } catch APIError.server(let legacyStatusCode, _) where legacyStatusCode == 404 {
                // Final fallback: reconstruct detail from list + farm houses endpoint.
                let farms = try await fetchFarms()
                guard let farm = farms.first(where: { $0.id == id }) else {
                    throw APIError.server(statusCode: 404, message: "Farm \(id) not found in current farm list.")
                }
                let houses = try await fetchFarmHouses(farmID: id)
                return FarmDetail(
                    id: farm.id,
                    organization: farm.organization,
                    name: farm.name,
                    location: farm.location,
                    description: farm.description,
                    contactPerson: nil,
                    contactPhone: nil,
                    contactEmail: nil,
                    isActive: farm.isActive,
                    totalHouses: farm.totalHouses,
                    activeHouses: farm.activeHouses,
                    houses: houses
                )
            }
        }
    }

    private func fetchFarmHouses(farmID: Int) async throws -> [HouseSummary] {
        let response: FlexibleListResponse<HouseSummary> = try await client.request(path: "farms/\(farmID)/houses/")
        return response.values
    }

    public func fetchFarmMonitoring(farmID: Int) async throws -> FarmMonitoringResponse {
        try await client.request(path: "farms/\(farmID)/houses/monitoring/all/")
    }

    public func fetchFarmMonitoringDashboard(farmID: Int) async throws -> FarmMonitoringDashboardResponse {
        try await client.request(path: "farms/\(farmID)/houses/monitoring/dashboard/")
    }

    public func fetchFarmComparison(farmID: Int) async throws -> HouseComparisonResponse {
        try await client.request(path: "houses/comparison/?farm_id=\(farmID)")
    }
}

public final class HouseService {
    private let client: APIClient

    public init(client: APIClient) {
        self.client = client
    }

    public func fetchHouseDetail(id: Int) async throws -> HouseDetail {
        try await client.request(path: "houses/\(id)/")
    }

    public func fetchHouseDetails(id: Int) async throws -> HouseDetailsResponse {
        try await client.request(path: "houses/\(id)/details/")
    }

    public func fetchHouseMonitoringKpis(id: Int) async throws -> HouseMonitoringKpisResponse {
        try await client.request(path: "houses/\(id)/monitoring/kpis/")
    }

    public func fetchHouseWaterHistory(id: Int) async throws -> WaterHistoryResponse {
        try await client.request(path: "rotem/daily-summaries/water-history/?house_id=\(id)")
    }
}
