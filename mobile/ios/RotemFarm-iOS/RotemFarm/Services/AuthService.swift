//
//  AuthService.swift
//  RotemFarm — Stubbed Sign in with Apple session.
//

import Foundation
import Observation
import SwiftUI

@Observable
@MainActor
final class AuthService {
    enum Status { case signedOut, signingIn, signedIn }
    private enum Keys {
        static let environment = "rotem.api.environment"
    }

    var status: Status = .signedOut
    var errorMessage: String?
    var username: String = ProcessInfo.processInfo.environment["ROTEM_IOS_USERNAME"] ?? ""
    var password: String = ProcessInfo.processInfo.environment["ROTEM_IOS_PASSWORD"] ?? ""
    var environment: APIEnvironment = .local

    private let apiClient: APIClient
    private weak var store: MockDataStore?

    init(apiClient: APIClient, store: MockDataStore) {
        self.apiClient = apiClient
        self.store = store
        if
            let saved = UserDefaults.standard.string(forKey: Keys.environment),
            let parsed = APIEnvironment(rawValue: saved)
        {
            environment = parsed
        }
        Task {
            try? await apiClient.setEnvironment(environment)
        }
    }

    static func previewSignedIn() -> AuthService {
        let apiClient = APIClient()
        let store = MockDataStore(apiClient: apiClient)
        let auth = AuthService(apiClient: apiClient, store: store)
        auth.status = .signedIn
        return auth
    }

    func restoreSessionIfPossible() {
        Task {
            if await apiClient.bootstrapToken() != nil {
                status = .signedIn
                await store?.refreshCoreDataIfNeeded()
            }
        }
    }

    func signInWithApple() async {
        if !username.isEmpty && !password.isEmpty {
            await signIn(username: username, password: password)
            return
        }
        errorMessage = "Sign in with Apple is not wired yet. Use username/password."
    }

    var currentBaseURLString: String {
        get async {
            await apiClient.baseURLString()
        }
    }

    func selectEnvironment(_ newEnvironment: APIEnvironment) async {
        guard environment != newEnvironment else { return }
        do {
            try await apiClient.setEnvironment(newEnvironment)
            environment = newEnvironment
            UserDefaults.standard.set(newEnvironment.rawValue, forKey: Keys.environment)
            await store?.resetSessionData()
            status = .signedOut
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func signIn(username: String, password: String) async {
        self.username = username
        self.password = password
        errorMessage = nil
        status = .signingIn

        do {
            _ = try await apiClient.login(username: username, password: password)
            status = .signedIn
            await store?.reloadCoreData()
        } catch {
            status = .signedOut
            errorMessage = error.localizedDescription
        }
    }

    func signOut() {
        Task {
            try? await apiClient.logout()
            await store?.resetSessionData()
            status = .signedOut
        }
    }
}
