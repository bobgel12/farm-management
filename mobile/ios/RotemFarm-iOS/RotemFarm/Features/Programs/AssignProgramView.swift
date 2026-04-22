import SwiftUI

struct AssignProgramView: View {
    @Environment(MockDataStore.self) private var store
    let program: Program
    @State private var selectedHouseIDs: Set<UUID> = []
    @State private var isSubmitting = false

    var body: some View {
        List {
            Section("Program") {
                VStack(alignment: .leading, spacing: 4) {
                    Text(program.name).font(AppFont.bodyBold)
                    Text(program.category).font(AppFont.caption).foregroundStyle(.secondary)
                }
            }

            Section("Select houses") {
                ForEach(store.housesForCurrentFarm) { house in
                    MultipleSelectionRow(
                        title: house.name,
                        isSelected: selectedHouseIDs.contains(house.id)
                    ) {
                        if selectedHouseIDs.contains(house.id) {
                            selectedHouseIDs.remove(house.id)
                        } else {
                            selectedHouseIDs.insert(house.id)
                        }
                    }
                }
            }
        }
        .navigationTitle("Assign program")
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button(isSubmitting ? "Assigning..." : "Assign") {
                    Task { await submit() }
                }
                .disabled(selectedHouseIDs.isEmpty || isSubmitting)
            }
        }
    }

    private func submit() async {
        isSubmitting = true
        defer { isSubmitting = false }
        await store.assignProgram(programId: program.id, houseIDs: Array(selectedHouseIDs))
    }
}

private struct MultipleSelectionRow: View {
    let title: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack {
                Text(title)
                Spacer()
                if isSelected {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundStyle(Color.farmGreen)
                }
            }
        }
        .buttonStyle(.plain)
    }
}

