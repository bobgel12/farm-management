import SwiftUI

struct RootView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        Group {
            if appState.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
    }
}

struct MainTabView: View {
    var body: some View {
        TabView {
            DashboardView()
                .tabItem {
                    Label("Dashboard", systemImage: "chart.bar.fill")
                }
            FarmListView()
                .tabItem {
                    Label("Farms", systemImage: "leaf.fill")
                }
            SessionView()
                .tabItem {
                    Label("Session", systemImage: "person.crop.circle")
                }
        }
        .tint(.green)
    }
}

struct SessionView: View {
    @EnvironmentObject private var appState: AppState

    var body: some View {
        NavigationStack {
            List {
                Section("Environment") {
                    Text("Deployment: \(AppEnvironment.deploymentTarget)")
                    Text("Devices: \(AppEnvironment.devicePolicy)")
                    Text("API: \(AppEnvironment.apiBaseURL.absoluteString)")
                }
                Section("Account") {
                    Text(appState.user?.username ?? "Unknown user")
                    Button("Logout", role: .destructive) {
                        appState.logout()
                    }
                }
            }
            .navigationTitle("Session")
        }
    }
}
