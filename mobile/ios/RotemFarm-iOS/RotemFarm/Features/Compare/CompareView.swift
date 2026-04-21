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

    private var series: [CompareSeries] {
        switch metric {
        case .water: store.compareWater()
        case .feed: store.compareFeed()
        case .heater: store.compareHeater()
        }
    }

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
                            state: houseSeries.todayDeltaState
                        )
                    }
                }
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle("Compare")
    }
}

private struct KPIBox: View {
    let houseName: String
    let delta: String
    let state: SensorState

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(houseName).font(AppFont.caption).foregroundStyle(.secondary)
            Text(delta)
                .font(.system(size: 24, weight: .bold, design: .rounded))
                .foregroundStyle(state.tint)
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
