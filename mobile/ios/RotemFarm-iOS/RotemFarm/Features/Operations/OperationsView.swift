import SwiftUI

struct OperationsView: View {
    @Environment(MockDataStore.self) private var store

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    SectionHeader(title: "Farm operations")
                    farmHeader

                    SectionHeader(title: "Monitoring")
                    CardSection {
                        VStack(spacing: 10) {
                            NavigationLink(destination: FarmMonitoringCardsView()) {
                                ValueRow(systemImage: "square.grid.2x2.fill", iconColor: .stateInfo, title: "Farm monitoring cards", value: "Temp, water, feed, sync")
                            }
                            NavigationLink(destination: CompareView()) {
                                ValueRow(systemImage: "chart.xyaxis.line", iconColor: .farmGreen, title: "House comparison dashboard", value: "Cross-house trend")
                            }
                        }
                    }

                    SectionHeader(title: "Houses")
                    ForEach(store.housesForCurrentFarm.sorted(by: { $0.name < $1.name })) { house in
                        NavigationLink(value: house) {
                            HouseCardMini(
                                houseName: house.name,
                                subtitle: "\(house.birdCount.formatted()) birds",
                                state: house.state,
                                pillText: house.pillText,
                                stats: [
                                    ("Day", "\(house.flockDay)"),
                                    ("Water", Self.formatWaterLive(store, house)),
                                    ("Heater", Self.formatHeaterForHouse(store, house))
                                ]
                            )
                        }
                        .buttonStyle(.plain)
                    }

                    SectionHeader(title: "Workflows")
                    CardSection {
                        VStack(spacing: 10) {
                            NavigationLink(destination: TaskCenterView()) {
                                ValueRow(systemImage: "checklist", iconColor: .farmGreen, title: "Task center", value: "\(store.tasks.count) tasks")
                            }
                            NavigationLink(destination: ProgramManagerView()) {
                                ValueRow(systemImage: "slider.horizontal.3", iconColor: .stateWarning, title: "Program management", value: "\(store.programs.count) programs")
                            }
                            NavigationLink(destination: WorkersManagementView()) {
                                ValueRow(systemImage: "person.3.fill", iconColor: .stateInfo, title: "Workers", value: "\(store.workers.count) staff")
                            }
                        }
                    }
                }
                .padding(14)
            }
            .background(Color.appBackground)
            .navigationTitle("Operations")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    FarmSwitcherMenu()
                }
            }
            .navigationDestination(for: House.self) { house in
                HouseDetailView(house: house)
            }
            .task { await store.refreshCoreDataIfNeeded() }
            .refreshable { await store.reloadCoreData() }
        }
    }

    /// Realtime-only water value from Rotem monitoring history.
    private static func formatWaterLive(_ store: MockDataStore, _ house: House) -> String {
        if !store.isRealtimeLoadedForHouse(house.id) {
            return "Loading..."
        }
        guard let v = store.waterForOperationsList(houseId: house.id) else { return "—" }
        return String(format: "%.0f L", v)
    }

    /// Realtime-only heater value from Rotem heater history.
    private static func formatHeaterForHouse(_ store: MockDataStore, _ house: House) -> String {
        if !store.isRealtimeLoadedForHouse(house.id) {
            return "Loading..."
        }
        if let h = store.heaterHoursForOperationsList(houseId: house.id) {
            return String(format: "%.1f h", h)
        }
        return "—"
    }

    private var farmHeader: some View {
        CardSection {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text(store.currentFarm.name).font(AppFont.title)
                    Text("\(store.housesForCurrentFarm.count) houses · \(store.currentFarm.totalBirds.formatted()) birds")
                        .font(AppFont.caption)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                PillBadge(text: store.currentFarm.alertSummary, style: .warning)
            }
        }
    }
}

