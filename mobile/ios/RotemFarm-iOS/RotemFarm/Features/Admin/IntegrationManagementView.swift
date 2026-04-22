import SwiftUI

struct IntegrationManagementView: View {
    @Environment(MockDataStore.self) private var store
    @State private var integrationType = "rotem"
    @State private var username = ""
    @State private var password = ""
    @State private var statusText = "Unknown"
    @State private var lastSyncText = "N/A"
    @State private var isLoading = false

    var body: some View {
        Form {
            Section("Current status") {
                Text(statusText)
                Text("Last sync: \(lastSyncText)")
                    .font(AppFont.caption)
                    .foregroundStyle(.secondary)
            }

            Section("Configuration") {
                Picker("Integration type", selection: $integrationType) {
                    Text("Rotem").tag("rotem")
                    Text("None").tag("none")
                }
                TextField("Rotem username", text: $username)
                    .textInputAutocapitalization(.never)
                SecureField("Rotem password", text: $password)
            }
        }
        .navigationTitle("Integration")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button(isLoading ? "Saving..." : "Save") {
                    Task { await save() }
                }
                .disabled(isLoading)
            }
        }
        .task {
            await refreshStatus()
        }
    }

    private func refreshStatus() async {
        guard let status = await store.fetchCurrentFarmIntegrationStatus() else { return }
        statusText = "\(status.integrationType.capitalized) · \(status.integrationStatus)"
        integrationType = status.integrationType
        if let last = status.lastSync {
            lastSyncText = last.formatted(date: .abbreviated, time: .shortened)
        } else {
            lastSyncText = "Never"
        }
    }

    private func save() async {
        isLoading = true
        defer { isLoading = false }
        await store.updateCurrentFarmIntegration(
            type: integrationType,
            username: username.isEmpty ? nil : username,
            password: password.isEmpty ? nil : password
        )
        await refreshStatus()
    }
}

