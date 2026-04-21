//
//  RootView.swift
//  RotemFarm — Auth-gated tab bar host.
//

import SwiftUI

enum AppTab: Hashable { case home, houses, alerts, reports, profile }

struct RootView: View {
    @Environment(AuthService.self) private var auth
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

            HousesView()
                .tabItem { Label("Houses", systemImage: "square.grid.2x2.fill") }
                .tag(AppTab.houses)

            AlertsView()
                .tabItem { Label("Alerts", systemImage: "bell.badge.fill") }
                .tag(AppTab.alerts)

            ReportsView()
                .tabItem { Label("Reports", systemImage: "chart.line.uptrend.xyaxis") }
                .tag(AppTab.reports)

            ProfileView()
                .tabItem { Label("Profile", systemImage: "person.crop.circle.fill") }
                .tag(AppTab.profile)
        }
    }
}

#Preview {
    RootView()
        .environment(MockDataStore.preview)
        .environment(AuthService.previewSignedIn())
}
