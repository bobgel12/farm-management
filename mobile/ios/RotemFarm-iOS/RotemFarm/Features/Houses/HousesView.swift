//
//  HousesView.swift
//  RotemFarm — Houses tab: list view of all houses on the current farm.
//

import SwiftUI

enum HouseFilter: String, CaseIterable {
    case status, map, production
    var label: String {
        switch self {
        case .status:     "Status"
        case .map:        "Floor map"
        case .production: "Production"
        }
    }
}

struct HousesView: View {
    @Environment(MockDataStore.self) private var store
    @State private var filter: HouseFilter = .status

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 10) {
                    AppSegmented(
                        selection: $filter,
                        options: HouseFilter.allCases,
                        labels: Dictionary(uniqueKeysWithValues: HouseFilter.allCases.map { ($0, $0.label) })
                    )
                    .padding(.horizontal, 2)
                    .padding(.bottom, 6)

                    ForEach(store.housesForCurrentFarm) { house in
                        NavigationLink(value: house) {
                            houseCardView(house)
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(14)
            }
            .background(Color.appBackground)
            .navigationTitle("Houses")
            .navigationSubtitle(subtitle)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    NavigationLink(destination: CompareView()) {
                        Image(systemName: "chart.xyaxis.line")
                    }
                }
            }
            .navigationDestination(for: House.self) { house in
                HouseDetailView(house: house)
            }
            .task { await store.refreshCoreDataIfNeeded() }
            .refreshable { await store.reloadCoreData() }
        }
    }

    private var subtitle: String {
        "\(store.currentFarm.name) · \(store.housesForCurrentFarm.count) houses"
    }

    private func houseCardView(_ house: House) -> some View {
        HouseCardMini(
            houseName: house.name,
            subtitle: "\(house.birdCount.formatted()) birds · day \(house.flockDay)",
            state: house.state,
            pillText: house.pillText,
            stats: [
                ("Temp",   formatMetric(house.snapshot.tempC, "%.1f°")),
                ("RH",     formatMetric(house.snapshot.humidity, "%.0f%%")),
                ("CO₂",    formatMetric(house.snapshot.co2Ppm, "%.1fk")),
                (house.state == .critical ? "Static" : "NH₃",
                 house.state == .critical
                 ? formatMetric(house.snapshot.staticPressurePa, "%.0f Pa")
                 : formatMetric(house.snapshot.ammoniaPpm, "%.0f"))
            ]
        )
    }

    private func formatMetric(_ value: Double, _ format: String) -> String {
        guard value.isFinite else { return "—" }
        return String(format: format, value)
    }
}

// Back-compat shim for earlier iOS versions that lack `.navigationSubtitle`
extension View {
    func navigationSubtitle(_ text: String) -> some View {
        self.toolbar {
            ToolbarItem(placement: .principal) {
                VStack(spacing: 1) {
                    Text("Houses")
                        .font(.system(size: 17, weight: .semibold))
                    Text(text)
                        .font(.system(size: 11))
                        .foregroundStyle(.secondary)
                }
            }
        }
    }
}

#Preview {
    HousesView().environment(MockDataStore.preview)
}
