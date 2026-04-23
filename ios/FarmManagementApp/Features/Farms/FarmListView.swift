import SwiftUI
import FarmManagementCore

struct FarmListView: View {
    @StateObject private var viewModel = FarmListViewModel(farmService: AppContainer.shared.farmService)

    var body: some View {
        NavigationStack {
            Group {
                switch viewModel.state {
                case .idle, .loading:
                    ProgressView("Loading farms...")
                case .failed(let message):
                    ErrorStateView(
                        title: "Unable to load farms",
                        systemImage: "exclamationmark.circle",
                        message: message
                    )
                case .loaded:
                    List(viewModel.filteredFarms) { farm in
                        NavigationLink {
                            FarmDetailView(farmID: farm.id)
                        } label: {
                            VStack(alignment: .leading, spacing: 10) {
                                HStack {
                                    Text(farm.name).font(.headline)
                                    Spacer()
                                    if farm.isIntegrated == true {
                                        Label("Integrated", systemImage: "bolt.fill")
                                            .font(.caption)
                                            .foregroundStyle(.green)
                                    }
                                }
                                Text(farm.location ?? "No location")
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                                HStack(spacing: 12) {
                                    Label("\(farm.totalHouses ?? 0) houses", systemImage: "house")
                                    Label("\(farm.activeHouses ?? 0) active", systemImage: "checkmark.circle")
                                }
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            }
                            .padding(.vertical, 6)
                        }
                    }
                    .searchable(text: $viewModel.query, prompt: "Search farms")
                    .refreshable { await viewModel.load() }
                }
            }
            .navigationTitle("Farms")
            .navigationBarTitleDisplayMode(.large)
            .task {
                if case .idle = viewModel.state {
                    await viewModel.load()
                }
            }
        }
    }
}
