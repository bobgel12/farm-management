import Foundation
import FarmManagementCore

@MainActor
final class AppState: ObservableObject {
    @Published var user: AuthUser?
    @Published var authError: String?

    private let container = AppContainer.shared

    var tokenStore: KeychainTokenStore { container.tokenStore }
    var authService: AuthService { container.authService }
    var farmService: FarmService { container.farmService }
    var houseService: HouseService { container.houseService }

    var isAuthenticated: Bool {
        user != nil && (tokenStore.readToken()?.isEmpty == false)
    }

    func restoreSession() async {
        guard tokenStore.readToken() != nil else { return }
        do {
            user = try await authService.currentUser()
            authError = nil
        } catch {
            tokenStore.clear()
            user = nil
            authError = nil
        }
    }

    func login(username: String, password: String) async -> Bool {
        do {
            let response = try await authService.login(username: username, password: password)
            tokenStore.save(token: response.token)
            user = response.user
            authError = nil
            return true
        } catch {
            authError = (error as? LocalizedError)?.errorDescription ?? "Login failed."
            return false
        }
    }

    func logout() {
        tokenStore.clear()
        user = nil
        authError = nil
    }
}
