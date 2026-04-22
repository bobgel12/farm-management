import SwiftUI

struct FarmMonitoringCard: Identifiable {
    let id: Int
    let houseNumber: Int
    let capacity: Int?
    let isIntegrated: Bool
    let ageDays: Int?
    let temperature: Double?
    let water: Double?
    let feed: Double?
    let lastSync: Date?
}

struct FarmMonitoringCardsView: View {
    @Environment(MockDataStore.self) private var store
    @State private var cards: [FarmMonitoringCard] = []
    @State private var isLoading = false

    var body: some View {
        ScrollView {
            if isLoading && cards.isEmpty {
                ProgressView("Loading house monitoring...")
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.top, 40)
            } else if cards.isEmpty {
                Text("No house monitoring data available.")
                    .font(AppFont.body)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .center)
                    .padding(.top, 40)
            } else {
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    ForEach(cards) { card in
                        cardView(card)
                    }
                }
                .padding(14)
            }
        }
        .background(Color.appBackground)
        .navigationTitle("Farm Monitoring")
        .toolbar {
            ToolbarItem(placement: .topBarLeading) {
                FarmSwitcherMenu()
            }
        }
        .task {
            await loadCards()
        }
        .task(id: store.currentFarmId) {
            await loadCards()
        }
        .refreshable {
            await loadCards(forceRefresh: true)
        }
    }

    private func cardView(_ card: FarmMonitoringCard) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("House \(card.houseNumber)")
                    .font(AppFont.titleMedium)
                Spacer()
                PillBadge(text: card.isIntegrated ? "Integrated" : "Manual", style: card.isIntegrated ? .info : .neutral)
            }
            Text("Capacity: \((card.capacity ?? 0).formatted())")
                .font(AppFont.body)
                .foregroundStyle(.secondary)
            Text("Age: \((card.ageDays ?? 0).formatted()) days")
                .font(AppFont.body)
                .foregroundStyle(.secondary)
            Text("Temperature: \(value(card.temperature, suffix: "°C"))")
                .font(AppFont.body)
                .foregroundStyle(.secondary)
            Text("Water: \(value(card.water, suffix: "L"))")
                .font(AppFont.body)
                .foregroundStyle(.secondary)
            Text("Feed: \(value(card.feed, suffix: "LB"))")
                .font(AppFont.body)
                .foregroundStyle(.secondary)
            Text("Last Sync: \(lastSyncText(card.lastSync))")
                .font(AppFont.body)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
    }

    private func value(_ number: Double?, suffix: String) -> String {
        guard let number else { return "N/A" }
        return "\(Int(number).formatted())\(suffix)"
    }

    private func lastSyncText(_ date: Date?) -> String {
        guard let date else { return "N/A" }
        let seconds = Int(-date.timeIntervalSinceNow)
        if seconds < 60 { return "Just now" }
        if seconds < 3600 { return "\(seconds / 60)m ago" }
        if seconds < 86_400 { return "\(seconds / 3600)h ago" }
        return date.formatted(date: .abbreviated, time: .shortened)
    }

    private func loadCards(forceRefresh: Bool = false) async {
        guard let backendFarmID = store.currentFarm.backendId else { return }
        isLoading = true
        if forceRefresh {
            await store.refreshMonitoringNowForCurrentFarm()
        } else {
            await store.refreshRotemDataForCurrentFarm()
        }

        async let metaTask = store.fetchFarmHouseMeta(farmBackendID: backendFarmID)
        async let monitoringTask = store.fetchFarmMonitoringDashboard(farmBackendID: backendFarmID)
        let (meta, monitoring) = await (metaTask, monitoringTask)

        let monitoringByHouse = Dictionary(uniqueKeysWithValues: monitoring.map { ($0.houseID, $0) })
        cards = meta.sorted(by: { $0.houseNumber < $1.houseNumber }).map { house in
            let live = monitoringByHouse[house.houseID]
            return FarmMonitoringCard(
                id: house.houseID,
                houseNumber: house.houseNumber,
                capacity: house.capacity,
                isIntegrated: house.isIntegrated,
                ageDays: house.currentAgeDays,
                temperature: live?.averageTemperature,
                water: live?.waterConsumption,
                feed: live?.feedConsumption,
                lastSync: house.lastSystemSync
            )
        }
        isLoading = false
    }
}

