//
//  RootView.swift
//  RotemFarm — Auth-gated tab bar host.
//

import SwiftUI

enum AppTab: Hashable { case home, operations, alerts, analytics, profile }

struct RootView: View {
    @Environment(AuthService.self) private var auth
    @Environment(MockDataStore.self) private var store
    @Environment(\.scenePhase) private var scenePhase
    @State private var selectedTab: AppTab = .home

    var body: some View {
        switch auth.status {
        case .signedOut, .signingIn:
            LoginView()
        case .signedIn:
            mainTabs
        }
    }

    private var mainTabs: some View {
        TabView(selection: $selectedTab) {
            DashboardView()
                .tabItem { Label("Home", systemImage: "house.fill") }
                .tag(AppTab.home)

            OperationsView()
                .tabItem { Label("Operations", systemImage: "square.grid.2x2.fill") }
                .tag(AppTab.operations)

            AlertsView()
                .tabItem { Label("Alerts", systemImage: "bell.badge.fill") }
                .tag(AppTab.alerts)

            AnalyticsHubView()
                .tabItem { Label("Analytics", systemImage: "chart.line.uptrend.xyaxis") }
                .tag(AppTab.analytics)

            ProfileView()
                .tabItem { Label("Profile", systemImage: "person.crop.circle.fill") }
                .tag(AppTab.profile)
        }
        .onChange(of: scenePhase) { _, phase in
            guard phase == .active, auth.status == .signedIn else { return }
            Task { await store.reloadSelectedFarmData() }
        }
    }
}

#Preview {
    RootView()
        .environment(MockDataStore.preview)
        .environment(AuthService.previewSignedIn())
}
