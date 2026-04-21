//
//  FlockDetailView.swift
//  RotemFarm — Flock detail and growth curve.
//

import Charts
import SwiftUI

struct FlockDetailView: View {
    let flock: Flock

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                hero

                SectionHeader(title: "Growth curve", trailing: "kg / day")
                growthCard

                SectionHeader(title: "KPI snapshot")
                kpiGrid

                SectionHeader(title: "Recent daily logs")
                logsCard
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle(flock.name)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var hero: some View {
        ZStack(alignment: .topLeading) {
            BrandGradient.hero
                .clipShape(RoundedRectangle(cornerRadius: AppRadius.hero))
            VStack(alignment: .leading, spacing: 6) {
                Text("\(flock.breed) · \(flock.birdsRemaining.formatted()) birds")
                    .font(AppFont.caption)
                    .foregroundStyle(Color.white.opacity(0.85))
                Text("Day \(flock.currentDay) of \(flock.totalDays)")
                    .font(AppFont.titleMedium)
                    .foregroundStyle(.white)
                ProgressView(value: Double(flock.currentDay), total: Double(flock.totalDays))
                    .tint(.white)
            }
            .padding(16)
        }
    }

    private var growthCard: some View {
        CardSection {
            Chart {
                ForEach(Array(flock.targetWeightCurve.enumerated()), id: \.offset) { day, value in
                    LineMark(x: .value("day", day), y: .value("kg", value))
                        .foregroundStyle(Color.secondary)
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [4, 3]))
                }
                ForEach(Array(flock.actualWeightCurve.prefix(flock.currentDay + 1).enumerated()), id: \.offset) { day, value in
                    LineMark(x: .value("day", day), y: .value("kg", value))
                        .foregroundStyle(Color.farmGreen)
                        .lineStyle(StrokeStyle(lineWidth: 2.5, lineCap: .round))
                    AreaMark(x: .value("day", day), y: .value("kg", value))
                        .foregroundStyle(LinearGradient(
                            colors: [Color.farmGreen.opacity(0.28), .clear],
                            startPoint: .top,
                            endPoint: .bottom
                        ))
                }
            }
            .frame(height: 210)
            .chartYAxis { AxisMarks(position: .leading) }
        }
    }

    private var kpiGrid: some View {
        LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: 2), spacing: 8) {
            KPICard(label: "Avg weight", value: String(format: "%.2f kg", flock.avgWeightKg))
            KPICard(label: "Target", value: String(format: "%.2f kg", flock.targetWeightKg))
            KPICard(label: "FCR", value: String(format: "%.2f", flock.fcr))
            KPICard(label: "Livability", value: String(format: "%.1f%%", flock.livabilityPct))
            KPICard(label: "Daily gain", value: "\(Int(flock.dailyGainG)) g")
            KPICard(label: "EPEF", value: "\(flock.epef)")
        }
    }

    private var logsCard: some View {
        CardSection {
            if flock.log.isEmpty {
                Text("No logs yet.")
                    .font(AppFont.body)
                    .foregroundStyle(.secondary)
            } else {
                VStack(spacing: 0) {
                    ForEach(Array(flock.log.enumerated()), id: \.element.id) { idx, entry in
                        VStack(alignment: .leading, spacing: 4) {
                            HStack {
                                Text("Day \(entry.day)").font(AppFont.bodyBold)
                                Spacer()
                                Text(entry.date.formatted(date: .abbreviated, time: .omitted))
                                    .font(AppFont.caption)
                                    .foregroundStyle(.secondary)
                            }
                            Text("Deaths: \(entry.deaths) · Avg weight: \(String(format: "%.2f", entry.avgWeightKg)) kg")
                                .font(AppFont.caption)
                                .foregroundStyle(.secondary)
                            if let note = entry.note, !note.isEmpty {
                                Text(note)
                                    .font(AppFont.caption)
                                    .foregroundStyle(.primary)
                            }
                        }
                        .padding(.vertical, 6)
                        if idx < flock.log.count - 1 {
                            Divider().overlay(Color.appSeparator).padding(.vertical, 4)
                        }
                    }
                }
            }
        }
    }
}

#Preview {
    NavigationStack {
        FlockDetailView(flock: MockDataStore.preview.flocks[0])
    }
}
