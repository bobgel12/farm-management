import SwiftUI

struct AdminToolsView: View {
    @Environment(MockDataStore.self) private var store

    var body: some View {
        List {
            Section("Communication") {
                ValueRow(systemImage: "envelope.fill", iconColor: .stateInfo, title: "Email manager", value: "Templates, test send", showsChevron: false)
                ValueRow(systemImage: "message.badge.fill", iconColor: .farmGreen, title: "Notification channels", value: "Push + email", showsChevron: false)
            }

            Section("Security") {
                ValueRow(systemImage: "lock.shield.fill", iconColor: .stateCritical, title: "Security settings", value: "Password, sessions", showsChevron: false)
                ValueRow(systemImage: "person.badge.key.fill", iconColor: .stateWarning, title: "Role permissions", value: "Org scoped", showsChevron: false)
            }

            Section("Rotem dashboard") {
                ForEach(store.rotemHealth) { health in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(health.farmName).font(AppFont.bodyBold)
                        Text("\(health.devicesOnline)/\(health.devicesTotal) devices online")
                            .font(AppFont.caption)
                            .foregroundStyle(.secondary)
                        Text("\(health.criticalCount) critical · \(health.warningCount) warning")
                            .font(AppFont.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Admin Tools")
    }
}

