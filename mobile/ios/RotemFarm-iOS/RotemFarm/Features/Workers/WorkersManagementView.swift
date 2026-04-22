import SwiftUI

struct WorkersManagementView: View {
    @Environment(MockDataStore.self) private var store
    @State private var searchText = ""
    @State private var selectedRole: UserRole?

    private var filteredWorkers: [WorkerProfile] {
        store.workers.filter { worker in
            let roleOK = selectedRole == nil || worker.role == selectedRole
            let query = searchText.trimmingCharacters(in: .whitespacesAndNewlines)
            let textOK = query.isEmpty
                || worker.name.localizedCaseInsensitiveContains(query)
                || worker.farmName.localizedCaseInsensitiveContains(query)
                || worker.phone.localizedCaseInsensitiveContains(query)
            return roleOK && textOK
        }
    }

    var body: some View {
        List {
            Section("Filters") {
                TextField("Search name/farm/phone", text: $searchText)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()

                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: 8) {
                        roleChip("All", isActive: selectedRole == nil) { selectedRole = nil }
                        ForEach(UserRole.allCases, id: \.self) { role in
                            roleChip(role.displayName, isActive: selectedRole == role) {
                                selectedRole = role
                            }
                        }
                    }
                    .padding(.vertical, 4)
                }
            }

            Section("Summary") {
                HStack {
                    Label("Total", systemImage: "person.3.fill")
                    Spacer()
                    Text("\(filteredWorkers.count)")
                }
                HStack {
                    Label("Farms covered", systemImage: "leaf.fill")
                    Spacer()
                    Text("\(Set(filteredWorkers.map(\.farmName)).count)")
                }
            }

            ForEach(filteredWorkers) { worker in
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(worker.name).font(AppFont.bodyBold)
                        Spacer()
                        PillBadge(text: worker.role.displayName, style: .info)
                    }
                    Text(worker.phone).font(AppFont.caption).foregroundStyle(.secondary)
                    Text("\(worker.farmName) · \(worker.assignedHouseIds.count) assigned houses")
                        .font(AppFont.caption).foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }
        }
        .navigationTitle("Workers")
    }

    private func roleChip(_ title: String, isActive: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 12, weight: .semibold))
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(isActive ? Color.farmGreen : Color(uiColor: .tertiarySystemFill), in: Capsule())
                .foregroundStyle(isActive ? Color.white : .primary)
        }
        .buttonStyle(.plain)
    }
}

