//
//  CompareView.swift
//  RotemFarm — Cross-house comparison screen.
//

import Charts
import SwiftUI

enum CompareMetric: String, CaseIterable, Hashable {
    case water = "Water"
    case feed = "Feed"
    case heater = "Heater"

    var yAxisTitle: String {
        switch self {
        case .water: "L/day"
        case .feed: "kg/day"
        case .heater: "h/day"
        }
    }
}

struct CompareView: View {
    @Environment(MockDataStore.self) private var store
    @State private var metric: CompareMetric = .water
    @State private var series: [CompareSeries] = []
    @State private var expectedHouseNames: [String] = []
    @State private var loadingHouseNames: Set<String> = []
    @State private var isLoading = false
    @State private var errorText: String?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                AppSegmented(
                    selection: $metric,
                    options: CompareMetric.allCases,
                    labels: Dictionary(uniqueKeysWithValues: CompareMetric.allCases.map { ($0, $0.rawValue) })
                )

                SectionHeader(title: "Cross-house trend", trailing: metric.yAxisTitle)
                CardSection {
                    if isLoading {
                        ProgressView("Loading comparison data...")
                            .frame(maxWidth: .infinity, minHeight: 220)
                    } else if let errorText {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Could not load comparison data.")
                                .font(AppFont.bodyBold)
                            Text(errorText)
                                .font(AppFont.caption)
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity, minHeight: 220, alignment: .topLeading)
                    } else if series.isEmpty || series.allSatisfy({ $0.points.isEmpty }) {
                        Text("No comparison history available for this farm yet.")
                            .font(AppFont.caption)
                            .foregroundStyle(.secondary)
                            .frame(maxWidth: .infinity, minHeight: 220, alignment: .center)
                    } else {
                        Chart {
                            ForEach(series) { line in
                                ForEach(line.points) { point in
                                    LineMark(
                                        x: .value("day", point.day),
                                        y: .value("value", point.value)
                                    )
                                    .foregroundStyle(line.color)
                                    .lineStyle(StrokeStyle(lineWidth: 2, lineCap: .round))
                                    .interpolationMethod(.linear)

                                    // Render points so one-day series remains visible.
                                    PointMark(
                                        x: .value("day", point.day),
                                        y: .value("value", point.value)
                                    )
                                    .foregroundStyle(line.color)
                                }
                            }
                        }
                        .frame(height: 220)
                        .chartYAxis { AxisMarks(position: .leading) }
                        .overlay(alignment: .topTrailing) {
                            if !loadingHouseNames.isEmpty {
                                Text("Loading \(loadingHouseNames.count) house(s)…")
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }

                SectionHeader(title: "Today delta")
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: 2), spacing: 8) {
                    ForEach(expectedHouseNames, id: \.self) { houseName in
                        if let houseSeries = series.first(where: { $0.houseName == houseName }) {
                            KPIBox(
                                houseName: houseSeries.houseName,
                                delta: houseSeries.todayDelta,
                                state: houseSeries.todayDeltaState,
                                points: houseSeries.points
                            )
                        } else {
                            KPIBoxLoading(houseName: houseName)
                        }
                    }
                }
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle("Compare")
        .task { await loadSeries() }
        .task(id: metric) { await loadSeries() }
        .task(id: store.currentFarmId) { await loadSeries() }
    }

    private func loadSeries() async {
        isLoading = true
        errorText = nil
        series = []

        if store.housesForCurrentFarm.isEmpty {
            await store.reloadSelectedFarmData()
        }

        await store.refreshRotemDataForCurrentFarm()
        let houses = store.housesForCurrentFarm
        guard !houses.isEmpty else {
            series = []
            expectedHouseNames = []
            loadingHouseNames = []
            isLoading = false
            return
        }
        expectedHouseNames = houses.map(\.name).sorted()
        loadingHouseNames = Set(expectedHouseNames)
        let colors: [Color] = [.farmGreen, .stateInfo, .stateWarning, .aiEnd, .stateOK, Color(red: 166/255, green: 90/255, blue: 40/255)]
        await withTaskGroup(of: (Int, String, [DailyResourcePoint], Double, SensorState).self) { group in
            for (idx, house) in houses.enumerated() {
                group.addTask {
                    let points = await pointsForHouse(houseID: house.id, metric: metric)
                    let today = points.last?.value ?? 0
                    let yesterday = points.dropLast().last?.value ?? 0
                    let pct = yesterday > 0 ? ((today - yesterday) / yesterday * 100) : 0
                    let state: SensorState = abs(pct) > 12 ? .critical : (abs(pct) > 5 ? .warning : .ok)
                    return (idx, house.name, points, pct, state)
                }
            }

            for await (idx, houseName, points, pct, state) in group {
                series.append(
                    CompareSeries(
                        houseName: houseName,
                        color: colors[idx % colors.count],
                        points: points,
                        todayDelta: (pct >= 0 ? "+" : "") + String(format: "%.0f%%", pct),
                        todayDeltaState: state
                    )
                )
                loadingHouseNames.remove(houseName)
                // Keep stable order while still rendering incrementally.
                series.sort(by: { $0.houseName < $1.houseName })
            }
        }

        isLoading = false
        if series.isEmpty, let lastError = store.lastError, !lastError.isEmpty {
            errorText = lastError
        }
    }

    private func pointsForHouse(houseID: UUID, metric: CompareMetric) async -> [DailyResourcePoint] {
        switch metric {
        case .water, .feed:
            return dailyPoints(
                history: await store.fetchMonitoringHistory(
                    houseId: houseID,
                    limit: 500,
                    startDate: Calendar.current.date(byAdding: .day, value: -7, to: Date()),
                    endDate: Date()
                ),
                metric: metric
            )
        case .heater:
            return Array((await store.fetchHeaterHistory(houseId: houseID)).suffix(7))
        }
    }

    private func dailyPoints(history: [APIHouseMonitoringPoint], metric: CompareMetric) -> [DailyResourcePoint] {
        let grouped = Dictionary(grouping: history) { Calendar.current.startOfDay(for: $0.timestamp) }
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        let days: [Date] = (0..<5).compactMap { offset in
            calendar.date(byAdding: .day, value: -(4 - offset), to: today)
        }
        return days.enumerated().map { idx, day in
            let total: Double = {
                switch metric {
                case .water:
                    return dailyConsumption(from: grouped[day] ?? [], keyPath: \.waterConsumption)
                case .feed:
                    return dailyConsumption(from: grouped[day] ?? [], keyPath: \.feedConsumption)
                case .heater:
                    return 0
                }
            }()
            return DailyResourcePoint(day: idx + 1, date: day, value: total, target: nil, isAnomaly: false)
        }
    }

    /// Rotem monitoring counters are cumulative; use in-day deltas, not sum of snapshots.
    private func dailyConsumption(
        from points: [APIHouseMonitoringPoint],
        keyPath: KeyPath<APIHouseMonitoringPoint, Double?>
    ) -> Double {
        let values = points
            .sorted(by: { $0.timestamp < $1.timestamp })
            .compactMap { $0[keyPath: keyPath] }

        guard !values.isEmpty else { return 0 }
        guard values.count > 1 else { return max(values[0], 0) }

        var total = 0.0
        var previous = values[0]
        for value in values.dropFirst() {
            // Counter reset/noise should not create negative consumption.
            total += max(value - previous, 0)
            previous = value
        }
        return total
    }
}

private struct KPIBox: View {
    let houseName: String
    let delta: String
    let state: SensorState
    let points: [DailyResourcePoint]

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(houseName).font(AppFont.caption).foregroundStyle(.secondary)
            Text(delta)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundStyle(state.tint)
            if !points.isEmpty {
                Divider().overlay(Color.appSeparator).padding(.vertical, 4)
                ForEach(points.suffix(3)) { point in
                    HStack {
                        Text(point.date.formatted(date: .abbreviated, time: .omitted))
                            .font(AppFont.caption)
                            .foregroundStyle(.secondary)
                        Spacer()
                        Text(String(format: "%.1f", point.value))
                            .font(AppFont.captionBold)
                    }
                }
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
    }
}

private struct KPIBoxLoading: View {
    let houseName: String

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(houseName).font(AppFont.caption).foregroundStyle(.secondary)
            ProgressView("Loading...")
                .font(AppFont.caption)
            Spacer(minLength: 0)
        }
        .frame(maxWidth: .infinity, minHeight: 110, alignment: .leading)
        .padding(12)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
    }
}

#Preview {
    NavigationStack {
        CompareView()
            .environment(MockDataStore.preview)
    }
}
