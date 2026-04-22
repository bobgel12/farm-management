import SwiftUI

struct ProgramManagerView: View {
    @Environment(MockDataStore.self) private var store
    @State private var selectedProgramID: UUID?

    var body: some View {
        List {
            ForEach(store.programs) { program in
                Section {
                    HStack {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(program.name).font(AppFont.bodyBold)
                            Text("\(program.category) · \(program.assignedHouseIds.count) houses")
                                .font(AppFont.caption)
                                .foregroundStyle(.secondary)
                        }
                        Spacer()
                        Toggle("", isOn: Binding(
                            get: { program.isActive },
                            set: { _ in store.toggleProgram(program.id) }
                        ))
                        .labelsHidden()
                    }
                    NavigationLink("Program timeline") {
                        ProgramTimelineView(program: program)
                    }
                    NavigationLink("Assign to houses") {
                        AssignProgramView(program: program)
                    }
                }
            }
            NavigationLink("Integration management") {
                IntegrationManagementView()
            }
        }
        .navigationTitle("Programs")
        .task {
            selectedProgramID = store.programs.first?.id
        }
    }
}

