import SwiftUI
import FarmManagementCore

struct FarmMonitoringView: View {
    @StateObject private var viewModel: FarmMonitoringViewModel

    init(farmID: Int) {
        _viewModel = StateObject(
            wrappedValue: FarmMonitoringViewModel(
                farmID: farmID,
                service: AppContainer.shared.farmService
            )
        )
    }

    var body: some View {
        Group {
            switch viewModel.state {
            case .idle, .loading:
                ProgressView("Loading monitoring...")
            case .failed(let message):
                ErrorStateView(
                    title: "Unable to load monitoring",
                    systemImage: "exclamationmark.triangle",
                    message: message
                )
            case .loaded(let data):
                List {
                    Section("Overview") {
                        VStack(alignment: .leading, spacing: 6) {
                            Text(data.farmName).font(.headline)
                            HStack(spacing: 14) {
                                Label("\(data.housesCount) houses", systemImage: "house.fill")
                                Label("Updated \(formattedUpdateTime(viewModel.lastUpdatedAt))", systemImage: "clock")
                            }
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        }
                    }

                    Section("Houses") {
                        ForEach(data.houses) { house in
                            VStack(alignment: .leading, spacing: 6) {
                                HStack {
                                    Text("House \(house.houseNumber)")
                                        .font(.headline)
                                    Spacer()
                                    if house.status == "no_data" {
                                        Text("No Data")
                                            .font(.caption2.bold())
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .background(Color.gray.opacity(0.15), in: Capsule())
                                    } else {
                                        Text(house.alarmStatus ?? "normal")
                                            .font(.caption2.bold())
                                            .padding(.horizontal, 8)
                                            .padding(.vertical, 4)
                                            .background((house.alarmStatus == "critical" ? Color.red.opacity(0.15) : Color.green.opacity(0.15)), in: Capsule())
                                            .foregroundStyle((house.alarmStatus == "critical") ? .red : .green)
                                    }
                                }
                                HStack(spacing: 12) {
                                    Label(house.isConnected == true ? "Connected" : "Disconnected", systemImage: house.isConnected == true ? "checkmark.circle.fill" : "xmark.circle.fill")
                                    Label("Active alarms: \(viewModel.activeAlarmCounts[house.id] ?? 0)", systemImage: "bell.badge")
                                    Label("Freshness: \(freshnessText(for: house.timestamp))", systemImage: "clock.arrow.circlepath")
                                }
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                                HStack {
                                    metric("Temp", house.averageTemperature, unit: "F")
                                    metric("Humidity", house.humidity, unit: "%")
                                    metric("Pressure", house.staticPressure, unit: "")
                                    metric("Day", house.growthDay.map(Double.init), unit: "")
                                }
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            }
                            .padding(.vertical, 4)
                        }
                    }
                }
                .refreshable { await viewModel.refresh() }
            }
        }
        .navigationTitle("Realtime Monitoring")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            if case .idle = viewModel.state {
                await viewModel.loadInitial()
            }
            viewModel.startPolling()
        }
        .onDisappear {
            viewModel.stopPolling()
        }
    }

    private func metric(_ name: String, _ value: Double?, unit: String) -> some View {
        Text("\(name): \(formatted(value, unit: unit))")
    }

    private func formatted(_ value: Double?, unit: String) -> String {
        guard let value else { return "---" }
        if unit.isEmpty { return String(format: "%.0f", value) }
        return String(format: "%.1f%@", value, unit)
    }

    private func formattedUpdateTime(_ date: Date?) -> String {
        guard let date else { return "-" }
        let formatter = DateFormatter()
        formatter.timeStyle = .medium
        return formatter.string(from: date)
    }

    private func freshnessText(for timestamp: String?) -> String {
        guard let timestamp,
              let parsed = ISO8601DateFormatter().date(from: timestamp) else {
            return "Unknown"
        }
        let minutes = Int(Date().timeIntervalSince(parsed) / 60)
        if minutes < 2 { return "Live" }
        if minutes < 15 { return "\(minutes)m" }
        return "\(minutes)m (stale)"
    }
}
