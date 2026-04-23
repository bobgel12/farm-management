import Foundation
import FarmManagementCore

struct HouseDetailScreenData {
    let house: HouseDetail
    let stats: HouseStats?
    let kpis: HouseMonitoringKpisResponse?
    let wind: WindContext?
    let latestWaterBreakdown: WaterHistoryEntry?
    let activeAlarmsCount: Int
}

@MainActor
final class HouseDetailViewModel: ObservableObject {
    @Published var state: LoadableState<HouseDetailScreenData> = .idle

    private let houseID: Int
    private let service: HouseService

    init(houseID: Int, service: HouseService) {
        self.houseID = houseID
        self.service = service
    }

    func load() async {
        state = .loading
        do {
            async let baseDetail = service.fetchHouseDetail(id: houseID)
            async let details = service.fetchHouseDetails(id: houseID)

            let house = try await baseDetail
            let detailed = try await details

            let kpis = try? await service.fetchHouseMonitoringKpis(id: houseID)
            let waterHistory = try? await service.fetchHouseWaterHistory(id: houseID)

            let screen = HouseDetailScreenData(
                house: house,
                stats: detailed.stats,
                kpis: kpis,
                wind: detailed.monitoring?.sensorData?.wind,
                latestWaterBreakdown: waterHistory?.waterHistory.first,
                activeAlarmsCount: detailed.alarms.count
            )
            state = .loaded(screen)
        } catch {
            state = .failed((error as? LocalizedError)?.errorDescription ?? "Failed to load house details")
        }
    }
}
