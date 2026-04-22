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
                    Chart {
                        ForEach(series) { line in
                            ForEach(line.points) { point in
                                LineMark(
                                    x: .value("day", point.day),
                                    y: .value("value", point.value)
                                )
                                .foregroundStyle(line.color)
                                .lineStyle(StrokeStyle(lineWidth: 2, lineCap: .round))
                                .interpolationMethod(.catmullRom)
                            }
                        }
                    }
                    .frame(height: 220)
                    .chartYAxis { AxisMarks(position: .leading) }
                }

                SectionHeader(title: "Today delta")
                LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: 2), spacing: 8) {
                    ForEach(series) { houseSeries in
                        KPIBox(
                            houseName: houseSeries.houseName,
                            delta: houseSeries.todayDelta,
                            state: houseSeries.todayDeltaState,
                            points: houseSeries.points
                        )
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
        await store.refreshRotemDataForCurrentFarm()
        let houses = store.housesForCurrentFarm
        let colors: [Color] = [.farmGreen, .stateInfo, .stateWarning, .aiEnd, .stateOK, Color(red: 166/255, green: 90/255, blue: 40/255)]
        var loaded: [CompareSeries] = []

        for (idx, house) in houses.enumerated() {
            let points: [DailyResourcePoint]
            switch metric {
            case .water:
                points = dailyPoints(history: await store.fetchMonitoringHistory(
                    houseId: house.id,
                    limit: 500,
                    startDate: Calendar.current.date(byAdding: .day, value: -7, to: Date()),
                    endDate: Date()
                ), metric: .water)
            case .feed:
                points = dailyPoints(history: await store.fetchMonitoringHistory(
                    houseId: house.id,
                    limit: 500,
                    startDate: Calendar.current.date(byAdding: .day, value: -7, to: Date()),
                    endDate: Date()
                ), metric: .feed)
            case .heater:
                points = Array((await store.fetchHeaterHistory(houseId: house.id)).suffix(7))
            }

            let today = points.last?.value ?? 0
            let yesterday = points.dropLast().last?.value ?? 0
            let pct = yesterday > 0 ? ((today - yesterday) / yesterday * 100) : 0
            let state: SensorState = abs(pct) > 12 ? .critical : (abs(pct) > 5 ? .warning : .ok)

            loaded.append(
                CompareSeries(
                    houseName: house.name,
                    color: colors[idx % colors.count],
                    points: points,
                    todayDelta: (pct >= 0 ? "+" : "") + String(format: "%.0f%%", pct),
                    todayDeltaState: state
                )
            )
        }
        series = loaded
    }

    private func dailyPoints(history: [APIHouseMonitoringPoint], metric: CompareMetric) -> [DailyResourcePoint] {
        let grouped = Dictionary(grouping: history) { Calendar.current.startOfDay(for: $0.timestamp) }
        let sortedDays = grouped.keys.sorted().suffix(7)
        return sortedDays.enumerated().map { idx, day in
            let total: Double = {
                switch metric {
                case .water:
                    return grouped[day]?.compactMap(\.waterConsumption).reduce(0, +) ?? 0
                case .feed:
                    return grouped[day]?.compactMap(\.feedConsumption).reduce(0, +) ?? 0
                case .heater:
                    return 0
                }
            }()
            return DailyResourcePoint(day: idx + 1, date: day, value: total, target: nil, isAnomaly: false)
        }
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

#Preview {
    NavigationStack {
        CompareView()
            .environment(MockDataStore.preview)
    }
}
