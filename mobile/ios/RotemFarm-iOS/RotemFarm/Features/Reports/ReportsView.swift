//
//  ReportsView.swift
//  RotemFarm — Flock KPIs + energy & mortality charts.
//

import Charts
import SwiftUI

struct ReportsView: View {
    @Environment(MockDataStore.self) private var store

    enum Range: String, CaseIterable, Hashable {
        case flock = "This flock", week = "7D", month = "30D"
    }

    @State private var range: Range = .flock

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    flockHero

                    rangeSegmented

                    SectionHeader(title: "Performance KPIs")
                    kpiGrid

                    SectionHeader(title: "Growth curve", trailing: "kg / day")
                    growthCard

                    SectionHeader(title: "Energy use", trailing: "kWh / day")
                    energyCard

                    SectionHeader(title: "Mortality", trailing: "daily deaths")
                    mortalityCard

                    SectionHeader(title: "Historical flocks")
                    historicalList
                }
                .padding(14)
            }
            .background(Color.appBackground)
            .navigationTitle("Reports")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    NavigationLink(destination: FlocksView()) {
                        Image(systemName: "list.bullet.rectangle")
                    }
                }
            }
            .navigationDestination(for: Flock.self) { flock in
                FlockDetailView(flock: flock)
            }
        }
    }

    private var flock: Flock { store.activeFlock ?? store.flocks[0] }

    // MARK: Hero

    private var flockHero: some View {
        ZStack(alignment: .topLeading) {
            BrandGradient.hero
                .clipShape(RoundedRectangle(cornerRadius: AppRadius.hero))
            VStack(alignment: .leading, spacing: 6) {
                Text("\(flock.name) · \(flock.breed)")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(Color.white.opacity(0.8))
                    .tracking(0.5)
                Text("Day \(flock.currentDay) of \(flock.totalDays)")
                    .font(AppFont.titleLarge)
                    .foregroundStyle(.white)
                ProgressView(value: Double(flock.currentDay), total: Double(flock.totalDays))
                    .tint(.white)
                    .padding(.top, 4)
                HStack(spacing: 18) {
                    heroStat(String(format: "%.2f", flock.avgWeightKg),
                             "kg avg", target: String(format: "→ %.2f", flock.targetWeightKg))
                    heroStat(String(format: "%.2f", flock.fcr),
                             "FCR", target: String(format: "→ %.2f", flock.targetFcr))
                    heroStat(String(format: "%.1f%%", flock.livabilityPct), "livability", target: nil)
                }
                .padding(.top, 4)
            }
            .padding(16)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func heroStat(_ value: String, _ label: String, target: String?) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(value)
                .font(.system(size: 20, weight: .bold, design: .rounded))
                .foregroundStyle(.white)
            Text(label.uppercased())
                .font(.system(size: 9, weight: .semibold))
                .tracking(0.5)
                .foregroundStyle(Color.white.opacity(0.8))
            if let target {
                Text(target)
                    .font(.system(size: 9))
                    .foregroundStyle(Color.white.opacity(0.65))
            }
        }
    }

    // MARK: Range

    private var rangeSegmented: some View {
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

    // MARK: KPIs

    private var kpiGrid: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: 3),
                  spacing: 8) {
            KPICard(label: "Daily gain", value: "\(Int(flock.dailyGainG)) g",
                    delta: "+2 g vs target", deltaState: .ok)
            KPICard(label: "W:F ratio", value: String(format: "%.2f", flock.waterFeedRatio),
                    delta: "On target", deltaState: .ok)
            KPICard(label: "EPEF", value: "\(flock.epef)",
                    delta: "Top decile", deltaState: .ok)
            KPICard(label: "Birds left", value: flock.birdsRemaining.formatted(),
                    delta: "\(flock.birdsPlaced - flock.birdsRemaining) lost",
                    deltaState: .warning)
            KPICard(label: "Flock age", value: "\(flock.currentDay) d",
                    delta: "\(flock.totalDays - flock.currentDay) to catch",
                    deltaState: .ok)
            KPICard(label: "Livability", value: String(format: "%.1f%%", flock.livabilityPct),
                    delta: "Target 97%", deltaState: .ok)
        }
    }

    // MARK: Growth curve

    private var growthCard: some View {
        CardSection {
            Chart {
                ForEach(Array(flock.targetWeightCurve.enumerated()), id: \.offset) { day, v in
                    LineMark(x: .value("day", day), y: .value("kg", v))
                        .foregroundStyle(Color.secondary)
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [4, 3]))
                        .foregroundStyle(by: .value("series", "Target"))
                }
                ForEach(Array(flock.actualWeightCurve.prefix(flock.currentDay + 1).enumerated()),
                        id: \.offset) { day, v in
                    LineMark(x: .value("day", day), y: .value("kg", v))
                        .foregroundStyle(Color.farmGreen)
                        .lineStyle(StrokeStyle(lineWidth: 2.5, lineCap: .round))
                        .foregroundStyle(by: .value("series", "Actual"))
                    AreaMark(x: .value("day", day), y: .value("kg", v))
                        .foregroundStyle(LinearGradient(
                            colors: [Color.farmGreen.opacity(0.3), .clear],
                            startPoint: .top, endPoint: .bottom))
                        .foregroundStyle(by: .value("series", "Actual"))
                }
            }
            .chartForegroundStyleScale(["Target": Color.secondary, "Actual": Color.farmGreen])
            .frame(height: 180)
            .chartYAxis { AxisMarks(position: .leading) }
        }
    }

    // MARK: Energy

    private var energyCard: some View {
        let days = 14
        let data: [(day: Int, kwh: Double)] = (0..<days).map { i in
            (9 + i, 140 + Double(i) * 8 + Double.random(in: -12...12))
        }
        return CardSection {
            Chart {
                ForEach(Array(data.enumerated()), id: \.offset) { _, p in
                    BarMark(x: .value("day", "D\(p.day)"), y: .value("kWh", p.kwh))
                        .foregroundStyle(Color.stateInfo)
                        .cornerRadius(4)
                }
            }
            .frame(height: 160)
            .chartYAxis { AxisMarks(position: .leading) }
        }
    }

    // MARK: Mortality

    private var mortalityCard: some View {
        let days = 14
        let data: [(day: Int, deaths: Double)] = (0..<days).map { i in
            let base = max(5.0, 28 - Double(i) * 1.2)
            return (9 + i, base + Double.random(in: -4...4))
        }
        return CardSection {
            Chart {
                ForEach(Array(data.enumerated()), id: \.offset) { _, p in
                    LineMark(x: .value("day", p.day), y: .value("deaths", p.deaths))
                        .foregroundStyle(Color.stateCritical)
                        .lineStyle(StrokeStyle(lineWidth: 2, lineCap: .round))
                    AreaMark(x: .value("day", p.day), y: .value("deaths", p.deaths))
                        .foregroundStyle(LinearGradient(
                            colors: [Color.stateCritical.opacity(0.2), .clear],
                            startPoint: .top, endPoint: .bottom))
                }
            }
            .frame(height: 140)
            .chartYAxis { AxisMarks(position: .leading) }
        }
    }

    // MARK: Historical

    private var historicalList: some View {
        CardSection {
            VStack(spacing: 0) {
                ForEach(Array(store.flocks.filter { !$0.isActive }.enumerated()), id: \.element.id) { idx, f in
                    NavigationLink(value: f) {
                        HStack(spacing: 10) {
                            RoundedRectangle(cornerRadius: 9)
                                .fill(Color.farmSoft)
                                .frame(width: 34, height: 34)
                                .overlay(
                                    Image(systemName: "chart.line.uptrend.xyaxis")
                                        .font(.system(size: 14, weight: .semibold))
                                        .foregroundStyle(Color.farmGreen)
                                )
                            VStack(alignment: .leading, spacing: 2) {
                                Text(f.name).font(AppFont.bodyBold)
                                Text("\(f.breed) · \(f.birdsRemaining.formatted()) harvested · EPEF \(f.epef)")
                                    .font(AppFont.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Spacer()
                            PillBadge(text: f.statePillText, style: .ok)
                        }
                        .padding(.vertical, 6)
                    }
                    .buttonStyle(.plain)
                    if idx < store.flocks.filter({ !$0.isActive }).count - 1 {
                        Divider().overlay(Color.appSeparator).padding(.vertical, 4)
                    }
                }
            }
        }
    }
}

#Preview {
    ReportsView().environment(MockDataStore.preview)
}
