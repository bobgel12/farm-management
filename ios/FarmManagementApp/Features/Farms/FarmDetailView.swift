import SwiftUI
import FarmManagementCore

struct FarmDetailView: View {
    @StateObject private var viewModel: FarmDetailViewModel

    init(farmID: Int) {
        _viewModel = StateObject(
            wrappedValue: FarmDetailViewModel(
                farmID: farmID,
                service: AppContainer.shared.farmService
            )
        )
    }

    var body: some View {
        Group {
            switch viewModel.state {
            case .idle, .loading:
                ProgressView("Loading farm detail...")
            case .failed(let message):
                ErrorStateView(
                    title: "Unable to load farm",
                    systemImage: "exclamationmark.triangle",
                    message: message
                )
            case .loaded(let farm):
                List {
                    Section("Summary") {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(farm.name)
                                .font(.title3.bold())
                            Text(farm.location ?? "-")
                                .foregroundStyle(.secondary)
                            HStack(spacing: 16) {
                                Label("\(farm.totalHouses ?? 0) houses", systemImage: "house.fill")
                                Label("\(farm.activeHouses ?? 0) active", systemImage: "checkmark.circle.fill")
                            }
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        }
                        .padding(.vertical, 4)
                    }
                    Section("Insights") {
                        NavigationLink {
                            FarmMonitoringView(farmID: farm.id)
                        } label: {
                            Label("Realtime Monitoring", systemImage: "waveform.path.ecg")
                        }
                        NavigationLink {
                            FarmComparisonView(farmID: farm.id)
                        } label: {
                            Label("House Comparison", systemImage: "chart.bar.xaxis")
                        }
                    }
                    Section("Houses") {
                        ForEach(farm.houses) { house in
                            NavigationLink {
                                HouseDetailView(houseID: house.id)
                            } label: {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("House \(house.houseNumber)")
                                    Text(house.status ?? "Unknown")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                            }
                        }
                    }
                }
            }
        }
        .navigationTitle("Farm Detail")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if case .idle = viewModel.state {
                await viewModel.load()
            }
        }
    }
}
