import SwiftUI

struct TaskCenterView: View {
    @Environment(MockDataStore.self) private var store
    @State private var selectedStatus: TaskStatus?

    private var filteredTasks: [FarmTask] {
        guard let selectedStatus else { return store.tasks }
        return store.tasks.filter { $0.status == selectedStatus }
    }

    var body: some View {
        List {
            Section {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack {
                        filterChip("All", active: selectedStatus == nil) { selectedStatus = nil }
                        ForEach(TaskStatus.allCases, id: \.self) { status in
                            filterChip(status.label, active: selectedStatus == status) {
                                selectedStatus = status
                            }
                        }
                    }
                }
                .listRowInsets(EdgeInsets())
                .padding(.vertical, 6)
            }

            ForEach(filteredTasks) { task in
                NavigationLink(destination: TaskDetailView(task: task)) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(task.title).font(AppFont.bodyBold)
                        Text("\(task.assigneeName) · due \(task.dueAt.formatted(date: .omitted, time: .shortened))")
                            .font(AppFont.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .navigationTitle("Task Center")
    }

    private func filterChip(_ title: String, active: Bool, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Text(title)
                .font(.system(size: 12, weight: .semibold))
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(active ? Color.farmGreen : Color(uiColor: .tertiarySystemFill), in: Capsule())
                .foregroundStyle(active ? Color.white : .primary)
        }
        .buttonStyle(.plain)
    }
}

struct TaskDetailView: View {
    @Environment(MockDataStore.self) private var store
    let task: FarmTask

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            CardSection {
                VStack(alignment: .leading, spacing: 8) {
                    Text(task.title).font(AppFont.title)
                    Text(task.notes).font(AppFont.body)
                    Text("Assigned to \(task.assigneeName)")
                        .font(AppFont.caption)
                        .foregroundStyle(.secondary)
                }
            }

            SectionHeader(title: "Status update")
            CardSection {
                VStack(spacing: 8) {
                    ForEach(TaskStatus.allCases, id: \.self) { status in
                        Button {
                            store.updateTaskStatus(task.id, to: status)
                        } label: {
                            HStack {
                                Text(status.label)
                                Spacer()
                            }
                        }
                        .buttonStyle(SecondaryButtonStyle())
                    }
                }
            }
            Spacer()
        }
        .padding(14)
        .background(Color.appBackground)
        .navigationTitle("Task Detail")
    }
}

