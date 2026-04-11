import SwiftUI
import FarmManagementCore

struct FarmComparisonView: View {
    @StateObject private var viewModel: FarmComparisonViewModel
    @State private var selectedTab = 0

    init(farmID: Int) {
        _viewModel = StateObject(
            wrappedValue: FarmComparisonViewModel(
                farmID: farmID,
                service: AppContainer.shared.farmService
            )
        )
    }

    var body: some View {
        Group {
            switch viewModel.state {
            case .idle, .loading:
                ProgressView("Loading comparison...")
            case .failed(let message):
                ErrorStateView(
                    title: "Unable to load comparison",
                    systemImage: "exclamationmark.triangle",
                    message: message
                )
            case .loaded(let houses):
                List {
                    Section("Controls") {
                        Picker("Metrics", selection: $selectedTab) {
                            Text("Climate").tag(0)
                            Text("Consumption").tag(1)
                            Text("Environment").tag(2)
                        }
                        .pickerStyle(.segmented)

                        Menu {
                            ForEach(ComparisonSortField.allCases, id: \.self) { field in
                                Button(field.rawValue) {
                                    viewModel.toggleSort(field)
                                }
                            }
                        } label: {
                            Label("Sort: \(viewModel.sortField.rawValue)", systemImage: "arrow.up.arrow.down")
                        }
                    }

                    Section("Houses") {
                        ForEach(houses) { house in
                            VStack(alignment: .leading, spacing: 6) {
                                HStack {
                                    Text("House \(house.houseNumber)")
                                        .font(.headline)
                                    Spacer()
                                    Text(house.alarmStatus)
                                        .font(.caption2.bold())
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background((house.alarmStatus == "critical" ? Color.red.opacity(0.15) : Color.green.opacity(0.15)), in: Capsule())
                                        .foregroundStyle(house.alarmStatus == "critical" ? .red : .green)
                                }
                                HStack(spacing: 12) {
                                    Label("Freshness: \(freshnessText(house.lastUpdateTime))", systemImage: "clock")
                                    Label(house.hasAlarms ? "Has alarms" : "No alarms", systemImage: house.hasAlarms ? "bell.badge.fill" : "bell")
                                }
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                                metricRow(for: house)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
                .refreshable { await viewModel.load() }
            }
        }
        .navigationTitle("House Comparison")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if case .idle = viewModel.state {
                await viewModel.load()
            }
        }
    }

    @ViewBuilder
    private func metricRow(for house: HouseComparisonItem) -> some View {
        switch selectedTab {
        case 0:
            HStack(spacing: 12) {
                Text("Temp: \(num(house.averageTemperature, suffix: "F"))")
                Text("Humidity: \(num(house.insideHumidity, suffix: "%"))")
                Text("Pressure: \(num(house.staticPressure))")
                Text("ΔTarget: \(deltaToTarget(house))")
                Text("Spread: \(insideOutsideSpread(house))")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        case 1:
            HStack {
                Text("Water: \(num(house.waterConsumption, suffix: "L"))")
                Text("Feed: \(num(house.feedConsumption, suffix: "lb"))")
                Text("W/Bird: \(num(house.waterPerBird, suffix: "L"))")
                Text("F/Bird: \(num(house.feedPerBird, suffix: "lb"))")
                Text("W:F \(num(house.waterFeedRatio))")
                Text("Birds: \(house.birdCount.map(String.init) ?? "---")")
                Text("Livability: \(num(house.livability, suffix: "%"))")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        default:
            HStack {
                Text("Day: \(house.ageDays.map(String.init) ?? "---")")
                Text("Connected: \(house.isConnected ? "Yes" : "No")")
                Text("Airflow%: \(num(house.airflowPercentage, suffix: "%"))")
                Text("Heater: \(house.heaterOn == true ? "On" : "Off")")
                Text("Fans: \(house.fanOn == true ? "On" : "Off")")
                Text("Wind: \(num(house.windSpeed))")
                Text("Status: \(house.status)")
            }
            .font(.caption)
            .foregroundStyle(.secondary)
        }
    }

    private func num(_ value: Double?, suffix: String = "") -> String {
        guard let value else { return "---" }
        return String(format: "%.1f%@", value, suffix)
    }

    private func deltaToTarget(_ house: HouseComparisonItem) -> String {
        guard let avg = house.averageTemperature, let target = house.targetTemperature else { return "---" }
        let delta = avg - target
        return String(format: "%+.1fF", delta)
    }

    private func insideOutsideSpread(_ house: HouseComparisonItem) -> String {
        guard let inside = house.averageTemperature, let outside = house.outsideTemperature else { return "---" }
        let spread = inside - outside
        return String(format: "%+.1fF", spread)
    }

    private func freshnessText(_ timestamp: String?) -> String {
        guard let timestamp,
              let parsed = ISO8601DateFormatter().date(from: timestamp) else {
            return "Unknown"
        }
        let minutes = Int(Date().timeIntervalSince(parsed) / 60)
        if minutes < 2 { return "Live" }
        if minutes < 15 { return "\(minutes)m" }
        return "\(minutes)m stale"
    }
}
