import Foundation
import FarmManagementCore

@MainActor
final class FarmDetailViewModel: ObservableObject {
    @Published var state: LoadableState<FarmDetail> = .idle

    private let farmID: Int
    private let service: FarmService

    init(farmID: Int, service: FarmService) {
        self.farmID = farmID
        self.service = service
    }

    func load() async {
        state = .loading
        do {
            state = .loaded(try await service.fetchFarmDetail(id: farmID))
        } catch {
            state = .failed((error as? LocalizedError)?.errorDescription ?? "Failed to load farm details")
        }
    }
}
