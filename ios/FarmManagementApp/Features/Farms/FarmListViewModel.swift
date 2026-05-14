import Foundation
import FarmManagementCore

@MainActor
final class FarmListViewModel: ObservableObject {
    @Published var state: LoadableState<[FarmSummary]> = .idle
    @Published var query = ""

    private let farmService: FarmService

    init(farmService: FarmService) {
        self.farmService = farmService
    }

    var filteredFarms: [FarmSummary] {
        guard case .loaded(let farms) = state, query.isEmpty == false else {
            if case .loaded(let farms) = state { return farms }
            return []
        }
        return farms.filter { farm in
            farm.name.localizedCaseInsensitiveContains(query) ||
            (farm.location ?? "").localizedCaseInsensitiveContains(query)
        }
    }

    func load() async {
        state = .loading
        do {
            let farms = try await farmService.fetchFarms()
            state = .loaded(farms)
        } catch {
            state = .failed((error as? LocalizedError)?.errorDescription ?? "Failed to load farms")
        }
    }
}
