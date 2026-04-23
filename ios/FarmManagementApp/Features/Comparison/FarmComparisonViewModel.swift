import Foundation
import FarmManagementCore

enum ComparisonSortField: String, CaseIterable {
    case houseNumber
    case ageDays
    case averageTemperature
    case waterConsumption
    case feedConsumption
    case birdCount
    case livability
}

@MainActor
final class FarmComparisonViewModel: ObservableObject {
    @Published var state: LoadableState<[HouseComparisonItem]> = .idle
    @Published var sortField: ComparisonSortField = .houseNumber
    @Published var ascending = true

    private let farmID: Int
    private let service: FarmService

    init(farmID: Int, service: FarmService) {
        self.farmID = farmID
        self.service = service
    }

    func load() async {
        state = .loading
        do {
            let response = try await service.fetchFarmComparison(farmID: farmID)
            state = .loaded(sorted(response.houses))
        } catch {
            state = .failed((error as? LocalizedError)?.errorDescription ?? "Failed to load comparison.")
        }
    }

    func toggleSort(_ field: ComparisonSortField) {
        if sortField == field {
            ascending.toggle()
        } else {
            sortField = field
            ascending = true
        }
        if case .loaded(let houses) = state {
            state = .loaded(sorted(houses))
        }
    }

    private func sorted(_ houses: [HouseComparisonItem]) -> [HouseComparisonItem] {
        houses.sorted { lhs, rhs in
            let result: Bool
            switch sortField {
            case .houseNumber:
                result = lhs.houseNumber < rhs.houseNumber
            case .ageDays:
                result = (lhs.ageDays ?? -1) < (rhs.ageDays ?? -1)
            case .averageTemperature:
                result = (lhs.averageTemperature ?? -1) < (rhs.averageTemperature ?? -1)
            case .waterConsumption:
                result = (lhs.waterConsumption ?? -1) < (rhs.waterConsumption ?? -1)
            case .feedConsumption:
                result = (lhs.feedConsumption ?? -1) < (rhs.feedConsumption ?? -1)
            case .birdCount:
                result = (lhs.birdCount ?? -1) < (rhs.birdCount ?? -1)
            case .livability:
                result = (lhs.livability ?? -1) < (rhs.livability ?? -1)
            }
            return ascending ? result : !result
        }
    }
}
