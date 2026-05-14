import Foundation
import FarmManagementCore

@MainActor
final class FarmMonitoringViewModel: ObservableObject {
    @Published var state: LoadableState<FarmMonitoringResponse> = .idle
    @Published var lastUpdatedAt: Date?
    @Published var activeAlarmCounts: [Int: Int] = [:]

    private let farmID: Int
    private let service: FarmService
    private var pollTask: Task<Void, Never>?

    init(farmID: Int, service: FarmService) {
        self.farmID = farmID
        self.service = service
    }

    deinit {
        pollTask?.cancel()
    }

    func loadInitial() async {
        state = .loading
        await refresh()
    }

    func refresh() async {
        do {
            async let monitoringResponse = service.fetchFarmMonitoring(farmID: farmID)
            async let dashboardResponse = service.fetchFarmMonitoringDashboard(farmID: farmID)

            let response = try await monitoringResponse
            let dashboard = try await dashboardResponse

            state = .loaded(response)
            activeAlarmCounts = Dictionary(uniqueKeysWithValues: dashboard.houses.map { ($0.id, $0.activeAlarmsCount ?? 0) })
            lastUpdatedAt = Date()
        } catch {
            state = .failed((error as? LocalizedError)?.errorDescription ?? "Failed to load monitoring.")
        }
    }

    func startPolling() {
        guard pollTask == nil else { return }
        pollTask = Task { [weak self] in
            while Task.isCancelled == false {
                try? await Task.sleep(nanoseconds: 30_000_000_000)
                guard Task.isCancelled == false else { break }
                await self?.refresh()
            }
        }
    }

    func stopPolling() {
        pollTask?.cancel()
        pollTask = nil
    }
}
