//
//  RotemFarmApp.swift
//  RotemFarm — App entry point.
//

import SwiftUI

@main
struct RotemFarmApp: App {
    @State private var store: MockDataStore
    @State private var auth: AuthService

    init() {
        let apiClient = APIClient()
        let store = MockDataStore(apiClient: apiClient)
        _store = State(initialValue: store)
        _auth = State(initialValue: AuthService(apiClient: apiClient, store: store))
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(store)
                .environment(auth)
                .tint(.farmGreen)
                .task { auth.restoreSessionIfPossible() }
        }
    }
}
