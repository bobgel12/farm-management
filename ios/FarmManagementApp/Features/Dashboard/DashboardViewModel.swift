import Foundation
import FarmManagementCore

@MainActor
final class DashboardViewModel: ObservableObject {
    @Published var state: LoadableState<[FarmSummary]> = .idle

    private let farmService: FarmService

    init(farmService: FarmService) {
        self.farmService = farmService
    }

    func load() async {
        state = .loading
        do {
            let farms = try await farmService.fetchFarms()
            state = .loaded(farms)
        } catch {
            state = .failed((error as? LocalizedError)?.errorDescription ?? "Failed to load dashboard")
        }
    }
}
