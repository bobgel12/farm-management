//
//  SensorHistoryView.swift
//  RotemFarm — Deep sensor detail with time-series chart, target band,
//  short-term forecast, and per-probe list.
//

import Charts
import SwiftUI

struct SensorHistoryView: View {
    @Environment(MockDataStore.self) private var store
    let house: House
    let kind: SensorKind

    enum Range: String, CaseIterable, Hashable {
        case hour = "1H", day = "24H", week = "7D", month = "30D"
        var points: Int {
            switch self { case .hour: 12; case .day: 48; case .week: 56; case .month: 120 }
        }
    }

    @State private var range: Range = .day

    var body: some View {
        let samples = store.sensorHistory(houseId: house.id, kind: kind, points: range.points)

        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                header(samples: samples)
                rangePicker
                chartCard(samples: samples)
                forecastCard
                probeList
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle(kind.title)
        .navigationBarTitleDisplayMode(.inline)
        .task(id: "\(house.id.uuidString)-\(kind.rawValue)-\(range.rawValue)") {
            await store.refreshSensorHistory(houseId: house.id, kind: kind, points: range.points)
        }
    }

    // MARK: Header

    private func header(samples: [SensorSample]) -> some View {
        let latest = samples.last?.value ?? 0
        let band = kind.targetBand
        let state: SensorState = {
            guard let band else { return .ok }
            if latest > band.high * 1.08 { return .critical }
            if latest > band.high || latest < band.low { return .warning }
            return .ok
        }()
        return HStack(alignment: .center) {
            VStack(alignment: .leading, spacing: 4) {
                Text("\(house.name) · Live").font(AppFont.caption).foregroundStyle(.secondary)
                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(String(format: "%.1f", latest))
                        .font(AppFont.bigNum)
                    Text(kind.unit)
                        .font(.system(size: 16, weight: .semibold, design: .rounded))
                        .foregroundStyle(.secondary)
                }
                if let band {
                    Text("Target: \(Self.formatBand(band, unit: kind.unit))")
                        .font(AppFont.caption)
                        .foregroundStyle(.secondary)
                }
            }
            Spacer()
            PillBadge(
                text: state.label,
                style: state == .ok ? .ok : (state == .warning ? .warning : .critical)
            )
        }
        .padding(14)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.hero))
    }

    // MARK: Range picker

    private var rangePicker: some View {
        HStack(spacing: 6) {
            ForEach(Range.allCases, id: \.self) { r in
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) { range = r }
                } label: {
                    Text(r.rawValue)
                        .font(.system(size: 12, weight: .semibold))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 6)
                        .background(range == r ? Color.farmGreen : Color(uiColor: .tertiarySystemFill),
                                    in: RoundedRectangle(cornerRadius: 8))
                        .foregroundStyle(range == r ? Color.white : .primary)
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: Chart card

    private func chartCard(samples: [SensorSample]) -> some View {
        CardSection {
            VStack(alignment: .leading, spacing: 8) {
                SectionHeader(title: "History — \(range.rawValue)", trailing: house.name)
                    .padding(.horizontal, -6)
                Chart {
                    if let band = kind.targetBand {
                        RectangleMark(
                            xStart: .value("start", samples.first?.timestamp ?? Date()),
                            xEnd: .value("end", samples.last?.timestamp ?? Date()),
                            yStart: .value("lo", band.low),
                            yEnd: .value("hi", band.high)
                        )
                        .foregroundStyle(Color.farmGreen.opacity(0.12))
                    }
                    ForEach(samples) { s in
                        AreaMark(x: .value("t", s.timestamp), y: .value("v", s.value))
                            .foregroundStyle(LinearGradient(
                                colors: [Color.farmGreen.opacity(0.35), .clear],
                                startPoint: .top, endPoint: .bottom))
                        LineMark(x: .value("t", s.timestamp), y: .value("v", s.value))
                            .foregroundStyle(Color.farmGreen)
                            .lineStyle(StrokeStyle(lineWidth: 2, lineCap: .round))
                    }
                }
                .frame(height: 200)
                .chartYAxis { AxisMarks(position: .leading) }
            }
        }
    }

    // MARK: Forecast card

    private var forecastCard: some View {
        AICard(
            label: "Short-term forecast",
            title: forecastTitle,
            message: forecastBody,
            severity: .ai,
            severityText: nil
        )
    }

    private var forecastTitle: String {
        switch kind {
        case .temperature:    "Holding 28.3 °C next 45 min"
        case .humidity:       "RH climbs to 73% by 15:10"
        case .co2:            "Peak 2.6k ppm around 11:45"
        case .ammonia:        "NH₃ stable at 13 ppm"
        case .staticPressure: "Static pressure climbing toward 44 Pa"
        case .airflow:        "Airflow will dip to 55% at stage change"
        }
    }

    private var forecastBody: String {
        switch kind {
        case .temperature:    "Outside is steady at 24 °C and ventilation is in stage 3. No action needed for the next hour."
        case .humidity:       "Wet litter at day 22 + tunnel stage 3 is holding moisture. Adding one more 54\" fan drops RH ~7% in 25 min."
        case .co2:            "Morning stir will push CO₂ up slightly. Still well under the 3.5k alarm — no action needed."
        case .ammonia:        "Litter moisture is within target. Ammonia has not trended up in the last 6 h."
        case .staticPressure: "Likely restricted inlets. Inspect curtain seals and inlet doors on the south wall."
        case .airflow:        "Stage transition at 12:15 may temporarily drop airflow below 60%. Pre-stage fan 9 to smooth."
        }
    }

    // MARK: Per-probe list

    private var probeList: some View {
        CardSection {
            VStack(spacing: 0) {
                ForEach(0..<4, id: \.self) { i in
                    ValueRow(
                        systemImage: kind.systemImage,
                        iconColor: .farmGreen,
                        title: "Probe \(i + 1) · \(probeLocation(i))",
                        value: probeReading(i),
                        showsChevron: false
                    )
                    if i < 3 {
                        Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                    }
                }
            }
        }
    }

    private func probeLocation(_ i: Int) -> String {
        ["North", "Centre", "South", "Inlet"][i % 4]
    }

    private func probeReading(_ i: Int) -> String {
        let base: Double = {
            switch kind {
            case .temperature:    return 28.0
            case .humidity:       return 68
            case .co2:            return 2.2
            case .ammonia:        return 13
            case .staticPressure: return 28
            case .airflow:        return 60
            }
        }()
        let offset = [0.1, -0.2, 0.3, -0.1][i]
        return String(format: "%.1f %@", base + offset * base * 0.05, kind.unit)
    }

    private static func formatBand(_ band: (low: Double, high: Double), unit: String) -> String {
        "\(String(format: "%.1f", band.low))–\(String(format: "%.1f", band.high)) \(unit)"
    }
}

#Preview {
    NavigationStack {
        SensorHistoryView(
            house: MockDataStore.preview.houses[2],
            kind: .humidity
        )
    }
    .environment(MockDataStore.preview)
}
