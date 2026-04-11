import SwiftUI
import FarmManagementCore

@main
struct FarmManagementIOSApp: App {
    @StateObject private var appState = AppState()

    var body: some Scene {
        WindowGroup {
            RootView()
                .environmentObject(appState)
                .task {
                    await appState.restoreSession()
                }
        }
    }
}
