//
//  FlocksView.swift
//  RotemFarm — Flock list screen.
//

import SwiftUI

enum FlockFilter: String, CaseIterable {
    case active = "Active"
    case history = "History"
    case all = "All"
}

struct FlocksView: View {
    @Environment(MockDataStore.self) private var store
    @State private var filter: FlockFilter = .active

    private var flocksForFarm: [Flock] {
        store.flocks.filter { $0.farmId == store.currentFarmId }
    }

    private var flocks: [Flock] {
        switch filter {
        case .active: flocksForFarm.filter(\.isActive)
        case .history: flocksForFarm.filter { !$0.isActive }
        case .all: flocksForFarm
        }
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                AppSegmented(
                    selection: $filter,
                    options: FlockFilter.allCases,
                    labels: Dictionary(uniqueKeysWithValues: FlockFilter.allCases.map { ($0, $0.rawValue) })
                )

                if flocks.isEmpty {
                    CardSection {
                        Text("No flocks in this section yet.")
                            .font(AppFont.body)
                            .foregroundStyle(.secondary)
                    }
                } else {
                    ForEach(flocks) { flock in
                        NavigationLink(value: flock) {
                            flockRow(flock)
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle("Flocks")
        .navigationDestination(for: Flock.self) { flock in
            FlockDetailView(flock: flock)
        }
        .task {
            await store.refreshCoreDataIfNeeded()
        }
    }

    private func flockRow(_ flock: Flock) -> some View {
        CardSection {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Text(flock.name).font(AppFont.bodyBold)
                    Spacer()
                    PillBadge(text: flock.statePillText, style: flock.state == .ok ? .ok : .warning)
                }
                Text("\(flock.breed) · Day \(flock.currentDay)/\(flock.totalDays)")
                    .font(AppFont.caption)
                    .foregroundStyle(.secondary)
                HStack(spacing: 8) {
                    KPICard(label: "Weight", value: String(format: "%.2f kg", flock.avgWeightKg))
                    KPICard(label: "FCR", value: String(format: "%.2f", flock.fcr))
                    KPICard(label: "Live", value: String(format: "%.1f%%", flock.livabilityPct))
                }
            }
        }
    }
}

#Preview {
    NavigationStack {
        FlocksView()
            .environment(MockDataStore.preview)
    }
}
