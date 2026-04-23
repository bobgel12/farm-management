import SwiftUI
import FarmManagementCore

struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel(farmService: AppContainer.shared.farmService)

    var body: some View {
        NavigationStack {
            Group {
                switch viewModel.state {
                case .idle, .loading:
                    ProgressView("Loading dashboard...")
                case .failed(let message):
                    ErrorStateView(
                        title: "Could not load dashboard",
                        systemImage: "exclamationmark.triangle",
                        message: message
                    )
                case .loaded(let farms):
                    ScrollView {
                        let active = farms.filter(\.isActive).count
                        let houses = farms.compactMap(\.totalHouses).reduce(0, +)
                        let integrated = farms.filter { $0.isIntegrated == true }.count

                        VStack(alignment: .leading, spacing: 14) {
                            Text("Overview")
                                .font(.title3.bold())
                            HStack(spacing: 12) {
                                statCard(title: "Active Farms", value: "\(active)", systemImage: "leaf.fill")
                                statCard(title: "Total Houses", value: "\(houses)", systemImage: "house.fill")
                            }
                            statCard(title: "Integrated Farms", value: "\(integrated)", systemImage: "bolt.horizontal.fill")
                        }
                        .padding()
                    }
                    .refreshable { await viewModel.load() }
                }
            }
            .navigationTitle("Dashboard")
            .navigationBarTitleDisplayMode(.large)
            .task {
                if case .idle = viewModel.state {
                    await viewModel.load()
                }
            }
        }
    }

    private func statCard(title: String, value: String, systemImage: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Label(title, systemImage: systemImage)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Text(value)
                .font(.system(size: 28, weight: .bold, design: .rounded))
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 16))
    }
}
