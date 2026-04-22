//
//  WaterDetailView.swift
//  RotemFarm — Day-over-day water consumption for one house.
//

import Charts
import SwiftUI

struct WaterDetailView: View {
    @Environment(MockDataStore.self) private var store
    let house: House

    enum Mode: String, CaseIterable, Hashable { case bars = "Bars", line = "Line", hourly = "Hourly" }
    @State private var mode: Mode = .bars
    @State private var daily: [DailyResourcePoint] = []
    @State private var hourly: [HourlyPoint] = []
    @State private var waterFeedRatio: Double?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                header(daily: daily)
                modeSegmented
                chartCard(daily: daily, hourly: hourly)
                ratioCard
                kpiGrid(daily: daily)
                compareLink
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle("Water")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await loadWaterData()
        }
    }

    // MARK: Header

    private func header(daily: [DailyResourcePoint]) -> some View {
        let today = daily.last?.value ?? 0
        let target = daily.last?.target ?? 0
        let pct = target > 0 ? (today - target) / target * 100 : 0
        let state: SensorState = pct > 10 ? .critical : (abs(pct) > 5 ? .warning : .ok)

        return HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("\(house.name) · Day \(house.flockDay)")
                    .font(AppFont.caption).foregroundStyle(.secondary)
                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(Int(today).formatted()).font(AppFont.bigNum)
                    Text("L today")
                        .font(.system(size: 14, weight: .semibold, design: .rounded))
                        .foregroundStyle(.secondary)
                }
                Text("Target \(Int(target).formatted()) L · \(pct >= 0 ? "+" : "")\(String(format: "%.0f%%", pct))")
                    .font(AppFont.caption)
                    .foregroundStyle(state.tint)
            }
            Spacer()
            VStack(alignment: .trailing, spacing: 4) {
                PillBadge(text: state == .ok ? "On target" : (state == .warning ? "Elevated" : "Over"),
                          style: state == .ok ? .ok : (state == .warning ? .warning : .critical))
                Image(systemName: "drop.fill")
                    .foregroundStyle(.white)
                    .padding(8)
                    .background(Color.stateInfo, in: RoundedRectangle(cornerRadius: 10))
            }
        }
        .padding(14)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.hero))
    }

    // MARK: Mode picker

    private var modeSegmented: some View {
        HStack(spacing: 6) {
            ForEach(Mode.allCases, id: \.self) { m in
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) { mode = m }
                } label: {
                    Text(m.rawValue)
                        .font(.system(size: 12, weight: .semibold))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 6)
                        .background(mode == m ? Color.stateInfo : Color(uiColor: .tertiarySystemFill),
                                    in: RoundedRectangle(cornerRadius: 8))
                        .foregroundStyle(mode == m ? Color.white : .primary)
                }
                .buttonStyle(.plain)
            }
        }
    }

    // MARK: Chart card

    private func chartCard(daily: [DailyResourcePoint], hourly: [HourlyPoint]) -> some View {
        CardSection {
            VStack(alignment: .leading, spacing: 8) {
                SectionHeader(title: mode == .hourly ? "Today hour-by-hour" : "Last 14 days",
                              trailing: mode == .hourly ? "L / hr" : "L / day")
                    .padding(.horizontal, -6)
                Chart {
                    switch mode {
                    case .bars:
                        ForEach(daily) { p in
                            BarMark(
                                x: .value("day", "D\(p.day)"),
                                y: .value("L", p.value)
                            )
                            .foregroundStyle(p.isAnomaly ? Color.stateCritical : Color.stateInfo)
                            .cornerRadius(4)
                            if let t = p.target {
                                RuleMark(y: .value("target", t))
                                    .foregroundStyle(Color.secondary.opacity(0.6))
                                    .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))
                            }
                        }
                    case .line:
                        ForEach(daily) { p in
                            AreaMark(x: .value("day", p.day), y: .value("L", p.value))
                                .foregroundStyle(LinearGradient(
                                    colors: [Color.stateInfo.opacity(0.35), .clear],
                                    startPoint: .top, endPoint: .bottom))
                            LineMark(x: .value("day", p.day), y: .value("L", p.value))
                                .foregroundStyle(Color.stateInfo)
                                .lineStyle(StrokeStyle(lineWidth: 2, lineCap: .round))
                        }
                    case .hourly:
                        ForEach(hourly) { p in
                            LineMark(x: .value("h", p.hour), y: .value("L/hr", p.value))
                                .foregroundStyle(Color.stateInfo)
                                .lineStyle(StrokeStyle(lineWidth: 2, lineCap: .round))
                            AreaMark(x: .value("h", p.hour), y: .value("L/hr", p.value))
                                .foregroundStyle(LinearGradient(
                                    colors: [Color.stateInfo.opacity(0.35), .clear],
                                    startPoint: .top, endPoint: .bottom))
                        }
                    }
                }
                .frame(height: 200)
                .chartYAxis { AxisMarks(position: .leading) }
            }
        }
    }

    // MARK: Water-to-feed ratio

    private var ratioCard: some View {
        HStack(spacing: 10) {
            KPICard(label: "Water:Feed", value: waterFeedRatio.map { String(format: "%.2f", $0) } ?? "-", delta: "Live KPI", deltaState: .ok)
            KPICard(label: "Peak L/hr", value: "\(Int(hourly.map(\.value).max() ?? 0))", delta: "Today", deltaState: .ok)
            KPICard(label: "Samples", value: "\(daily.count)", delta: "Last 14 days", deltaState: .ok)
        }
    }

    // MARK: KPIs

    private func kpiGrid(daily: [DailyResourcePoint]) -> some View {
        let today = daily.last?.value ?? 0
        let yday = daily.dropLast().last?.value ?? 1
        let delta = (today - yday) / yday * 100
        return CardSection {
            VStack(spacing: 0) {
                ValueRow(systemImage: "calendar", iconColor: .stateInfo,
                         title: "Yesterday",
                         value: "\(Int(yday).formatted()) L")
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                ValueRow(systemImage: "arrow.up.right", iconColor: .stateWarning,
                         title: "Day-over-day",
                         value: (delta >= 0 ? "+" : "") + String(format: "%.0f%%", delta))
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                ValueRow(systemImage: "chart.line.uptrend.xyaxis", iconColor: .farmGreen,
                         title: "Flock-to-date",
                         value: "\(Int(daily.map(\.value).reduce(0, +)).formatted()) L")
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                ValueRow(systemImage: "drop.fill", iconColor: .stateInfo,
                         title: "Per bird today",
                         value: String(format: "%.0f mL", today / Double(house.birdCount) * 1000))
            }
        }
    }

    // MARK: Compare

    private var compareLink: some View {
        NavigationLink(destination: CompareView()) {
            HStack {
                Image(systemName: "square.grid.2x2.fill")
                Text("Compare with other houses")
                Spacer()
                Image(systemName: "chevron.right").font(.system(size: 12, weight: .semibold))
            }
            .font(AppFont.bodyBold)
            .foregroundStyle(Color.farmGreen)
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.farmSoft, in: RoundedRectangle(cornerRadius: AppRadius.card))
        }
        .buttonStyle(.plain)
    }
}

extension WaterDetailView {
    private func loadWaterData() async {
        await store.refreshRotemDataForCurrentFarm()
        let history = await store.fetchMonitoringHistory(
            houseId: house.id,
            limit: 500,
            startDate: Calendar.current.date(byAdding: .day, value: -14, to: Date()),
            endDate: Date()
        )
        daily = buildDailyWater(history: history)
        hourly = buildHourlyWater(history: history)
        waterFeedRatio = await store.fetchMonitoringKpis(houseId: house.id)?.waterFeedRatioToday
    }

    private func buildDailyWater(history: [APIHouseMonitoringPoint]) -> [DailyResourcePoint] {
        let grouped = Dictionary(grouping: history) { Calendar.current.startOfDay(for: $0.timestamp) }
        let sortedDays = grouped.keys.sorted().suffix(14)
        return sortedDays.enumerated().map { idx, day in
            let total = grouped[day]?.compactMap(\.waterConsumption).reduce(0, +) ?? 0
            return DailyResourcePoint(day: idx + 1, date: day, value: total, target: nil, isAnomaly: false)
        }
    }

    private func buildHourlyWater(history: [APIHouseMonitoringPoint]) -> [HourlyPoint] {
        let today = Calendar.current.startOfDay(for: Date())
        let todaysPoints = history.filter { Calendar.current.startOfDay(for: $0.timestamp) == today }
        let grouped = Dictionary(grouping: todaysPoints) { Calendar.current.component(.hour, from: $0.timestamp) }
        return (0..<24).map { hour in
            let value = grouped[hour]?.compactMap(\.waterConsumption).reduce(0, +) ?? 0
            return HourlyPoint(hour: hour, value: value)
        }
    }
}

// MARK: - Compare across houses

#Preview {
    NavigationStack {
        WaterDetailView(house: MockDataStore.preview.houses[2])
    }
    .environment(MockDataStore.preview)
}
