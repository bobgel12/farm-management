import Foundation
import FarmManagementCore

final class AppContainer {
    static let shared = AppContainer()

    let tokenStore = KeychainTokenStore()
    lazy var apiClient = APIClient(baseURL: AppEnvironment.apiBaseURL, tokenProvider: tokenStore)
    lazy var authService = AuthService(client: apiClient)
    lazy var farmService = FarmService(client: apiClient)
    lazy var houseService = HouseService(client: apiClient)

    private init() {}
}
