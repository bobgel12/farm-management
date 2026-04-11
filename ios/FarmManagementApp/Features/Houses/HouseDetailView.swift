import SwiftUI
import FarmManagementCore

struct HouseDetailView: View {
    @StateObject private var viewModel: HouseDetailViewModel

    init(houseID: Int) {
        _viewModel = StateObject(
            wrappedValue: HouseDetailViewModel(
                houseID: houseID,
                service: AppContainer.shared.houseService
            )
        )
    }

    var body: some View {
        Group {
            switch viewModel.state {
            case .idle, .loading:
                ProgressView("Loading house detail...")
            case .failed(let message):
                ErrorStateView(
                    title: "Unable to load house",
                    systemImage: "exclamationmark.triangle",
                    message: message
                )
            case .loaded(let data):
                List {
                    Section("Overview") {
                        LabeledContent("House number", value: "\(data.house.houseNumber)")
                        LabeledContent("Status", value: data.house.status ?? "-")
                        LabeledContent("Age (days)", value: "\(data.house.ageDays ?? data.house.currentAgeDays ?? 0)")
                        LabeledContent("Days remaining", value: "\(data.house.daysRemaining ?? 0)")
                        LabeledContent("Active alarms", value: "\(data.activeAlarmsCount)")
                    }
                    Section("Batch") {
                        LabeledContent("Start date", value: data.house.batchStartDate ?? "-")
                        LabeledContent("Expected harvest", value: data.house.expectedHarvestDate ?? "-")
                        LabeledContent("Integrated", value: data.house.isIntegrated ? "Yes" : "No")
                    }
                    if let stats = data.stats {
                        Section("7-Day Trends") {
                            statRow("Temperature", stats.temperature)
                            statRow("Humidity", stats.humidity)
                            statRow("Pressure", stats.pressure)
                        }
                    }
                    if let kpis = data.kpis {
                        Section("Operational Deltas") {
                            LabeledContent("Water DoD", value: deltaText(kpis.waterDayOverDay))
                            LabeledContent("Feed DoD", value: deltaText(kpis.feedDayOverDay))
                            LabeledContent("Water:Feed ratio", value: ratioText(kpis.waterFeedRatio.today))
                        }
                        Section("Runtime Proxies (24h)") {
                            LabeledContent("Heater runtime", value: runtimeText(kpis.heaterRuntime.hours24h))
                            LabeledContent("Fan runtime", value: runtimeText(kpis.fanRuntime.hours24h))
                            LabeledContent("Heater cycles", value: "\(kpis.heaterRuntime.cycles24h ?? 0)")
                            LabeledContent("Ventilation effort", value: ratioText(kpis.ventilationEffortIndex))
                        }
                    }
                    if let wind = data.wind {
                        Section("Wind Context") {
                            LabeledContent("Wind speed", value: ratioText(wind.windSpeed))
                            LabeledContent("Wind direction", value: ratioText(wind.windDirection))
                            LabeledContent("Wind chill", value: ratioText(wind.windChillTemperature))
                        }
                    }
                    if let water = data.latestWaterBreakdown {
                        Section("Water Breakdown (latest)") {
                            LabeledContent("Growth day", value: "\(water.growthDay ?? 0)")
                            LabeledContent("Drink line 1", value: ratioText(water.dailyWater1))
                            LabeledContent("Drink line 2", value: ratioText(water.dailyWater2))
                            LabeledContent("Drink line 3", value: ratioText(water.dailyWater3))
                            LabeledContent("Drink line 4", value: ratioText(water.dailyWater4))
                            LabeledContent("Cooling", value: ratioText(water.cooling))
                            LabeledContent("Fogger", value: ratioText(water.fogger))
                        }
                    }
                }
            }
        }
        .navigationTitle("House Detail")
        .task {
            if case .idle = viewModel.state {
                await viewModel.load()
            }
        }
    }

    @ViewBuilder
    private func statRow(_ title: String, _ range: StatRange?) -> some View {
        LabeledContent(title, value: "avg \(ratioText(range?.avg)) / max \(ratioText(range?.max)) / min \(ratioText(range?.min))")
    }

    private func deltaText(_ metric: DeltaMetric) -> String {
        guard let delta = metric.delta, let deltaPct = metric.deltaPct else { return "N/A" }
        return String(format: "%+.1f (%+.1f%%)", delta, deltaPct)
    }

    private func runtimeText(_ hours: Double?) -> String {
        guard let hours else { return "N/A" }
        return String(format: "%.2f h", hours)
    }

    private func ratioText(_ value: Double?) -> String {
        guard let value else { return "N/A" }
        return String(format: "%.2f", value)
    }
}
