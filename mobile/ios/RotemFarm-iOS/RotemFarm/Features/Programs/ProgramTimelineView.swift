import SwiftUI

struct ProgramTimelineView: View {
    @Environment(MockDataStore.self) private var store
    let program: Program
    @State private var selectedDay: Int = 0
    @State private var tasks: [APIProgramTask] = []

    var body: some View {
        List {
            Section("Cycle day") {
                Stepper("Day \(selectedDay)", value: $selectedDay, in: -1...60)
            }
            Section("Tasks") {
                if tasks.isEmpty {
                    Text("No program tasks for this day.")
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(tasks, id: \.id) { task in
                        VStack(alignment: .leading, spacing: 4) {
                            Text(task.title).font(AppFont.bodyBold)
                            Text("\(task.priority.capitalized) · \(task.estimatedDuration) min")
                                .font(AppFont.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }
        }
        .navigationTitle("Program timeline")
        .task { await load() }
        .onChange(of: selectedDay) { _, _ in
            Task { await load() }
        }
    }

    private func load() async {
        tasks = await store.fetchProgramTasks(programId: program.id, day: selectedDay)
    }
}

