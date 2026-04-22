//
//  AlertsView.swift
//  RotemFarm — Alerts inbox + detail view.
//

import Charts
import SwiftUI

// MARK: - Inbox

struct AlertsView: View {
    @Environment(MockDataStore.self) private var store

    enum Filter: String, CaseIterable, Hashable {
        case all, active, acknowledged
        var label: String {
            switch self {
            case .all:           "All"
            case .active:        "Active"
            case .acknowledged:  "Acknowledged"
            }
        }
    }

    @State private var filter: Filter = .active

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(spacing: 10) {
                    AppSegmented(
                        selection: $filter,
                        options: Filter.allCases,
                        labels: Dictionary(uniqueKeysWithValues: Filter.allCases.map { ($0, $0.label) })
                    )
                    .padding(.horizontal, 2)
                    .padding(.bottom, 4)

                    summaryStrip

                    if filter != .acknowledged {
                        if !activeCritical.isEmpty {
                            SectionHeader(title: "Critical", trailing: "\(activeCritical.count)")
                            list(activeCritical)
                        }
                        if !activeWarning.isEmpty {
                            SectionHeader(title: "Warning", trailing: "\(activeWarning.count)")
                            list(activeWarning)
                        }
                        if !activeInfo.isEmpty {
                            SectionHeader(title: "Info", trailing: "\(activeInfo.count)")
                            list(activeInfo)
                        }
                    }
                    if filter != .active {
                        SectionHeader(title: "Acknowledged",
                                      trailing: "\(store.acknowledgedAlerts.count)")
                        list(store.acknowledgedAlerts)
                    }
                }
                .padding(14)
            }
            .background(Color.appBackground)
            .navigationTitle("Alerts")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    FarmSwitcherMenu()
                }
            }
            .navigationDestination(for: Alarm.self) { alarm in
                AlertDetailView(alarm: alarm)
            }
            .task { await store.refreshCoreDataIfNeeded() }
            .refreshable { await store.reloadCoreData() }
        }
    }

    private var activeCritical: [Alarm] { store.activeAlerts.filter { $0.severity == .critical } }
    private var activeWarning:  [Alarm] { store.activeAlerts.filter { $0.severity == .warning  } }
    private var activeInfo:     [Alarm] { store.activeAlerts.filter { $0.severity == .info     } }

    private var summaryStrip: some View {
        HStack(spacing: 8) {
            summaryTile(title: "Critical", value: activeCritical.count, state: .critical)
            summaryTile(title: "Warning",  value: activeWarning.count,  state: .warning)
            summaryTile(title: "Info",     value: activeInfo.count,     state: .ok)
        }
    }

    private func summaryTile(title: String, value: Int, state: SensorState) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(title.uppercased())
                .font(.system(size: 10, weight: .semibold))
                .tracking(0.4)
                .foregroundStyle(.secondary)
            Text("\(value)")
                .font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundStyle(state.tint)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(state.iconBackground, in: RoundedRectangle(cornerRadius: AppRadius.card))
    }

    private func list(_ alarms: [Alarm]) -> some View {
        CardSection {
            ForEach(Array(alarms.enumerated()), id: \.element.id) { idx, alarm in
                NavigationLink(value: alarm) {
                    AlertRow(
                        systemImage: alarm.severity.systemImage,
                        title: alarm.title,
                        meta: alarm.meta,
                        state: alarm.severity.state
                    )
                }
                .buttonStyle(.plain)
                if idx < alarms.count - 1 {
                    Divider().overlay(Color.appSeparator).padding(.vertical, 6)
                }
            }
        }
    }
}

// MARK: - Detail

struct AlertDetailView: View {
    @Environment(MockDataStore.self) private var store
    @Environment(\.dismiss) private var dismiss
    let alarm: Alarm

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                hero
                if !alarm.sparkline.isEmpty {
                    SectionHeader(title: "Reading · last 20 samples",
                                  trailing: alarm.threshold.map { "threshold \(Int($0))" } ?? nil)
                    chartCard
                }
                if let rec = alarm.recommendation {
                    AICard(
                        label: "AI Recommendation",
                        title: rec.title,
                        message: rec.body,
                        severity: alarm.severity == .critical ? .critical : .warning,
                        severityText: "\(Int(rec.confidence * 100))% confident",
                        primaryAction: (rec.primaryAction, {}),
                        secondaryAction: (rec.secondaryAction, {})
                    )
                }
                SectionHeader(title: "Context")
                context

                if !alarm.isAcknowledged {
                    actions
                }
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle(alarm.severity.label)
        .navigationBarTitleDisplayMode(.inline)
    }

    private var hero: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: alarm.severity.systemImage)
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundStyle(.white)
                    .frame(width: 34, height: 34)
                    .background(.white.opacity(0.18), in: RoundedRectangle(cornerRadius: 10))
                Spacer()
                PillBadge(text: alarm.severity.label.uppercased(), style: pillStyle)
            }
            Text(alarm.title).font(AppFont.titleMedium).foregroundStyle(.white)
            Text(alarm.meta).font(AppFont.caption).foregroundStyle(.white.opacity(0.85))
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(heroGradient, in: RoundedRectangle(cornerRadius: AppRadius.hero))
    }

    private var heroGradient: LinearGradient {
        switch alarm.severity {
        case .critical:     BrandGradient.critical
        case .warning:      LinearGradient(colors: [Color.stateWarning, Color.orange],
                                           startPoint: .topLeading, endPoint: .bottomTrailing)
        case .info:         LinearGradient(colors: [Color.stateInfo, Color.blue],
                                           startPoint: .topLeading, endPoint: .bottomTrailing)
        case .acknowledged: BrandGradient.hero
        }
    }

    private var pillStyle: PillBadge.Style {
        switch alarm.severity {
        case .critical:     .critical
        case .warning:      .warning
        case .info:         .info
        case .acknowledged: .ok
        }
    }

    private var chartCard: some View {
        CardSection {
            Chart {
                if let threshold = alarm.threshold {
                    RuleMark(y: .value("threshold", threshold))
                        .foregroundStyle(Color.stateCritical.opacity(0.7))
                        .lineStyle(StrokeStyle(lineWidth: 1, dash: [4, 3]))
                }
                ForEach(Array(alarm.sparkline.enumerated()), id: \.offset) { idx, v in
                    LineMark(x: .value("i", idx), y: .value("v", v))
                        .foregroundStyle(alarm.severity.state.tint)
                        .lineStyle(StrokeStyle(lineWidth: 2, lineCap: .round))
                    AreaMark(x: .value("i", idx), y: .value("v", v))
                        .foregroundStyle(LinearGradient(
                            colors: [alarm.severity.state.tint.opacity(0.3), .clear],
                            startPoint: .top, endPoint: .bottom))
                }
            }
            .frame(height: 160)
            .chartYAxis { AxisMarks(position: .leading) }
        }
    }

    private var context: some View {
        CardSection {
            VStack(spacing: 0) {
                ValueRow(systemImage: "house.fill", iconColor: .farmGreen,
                         title: "House", value: alarm.houseName, showsChevron: false)
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                ValueRow(systemImage: "clock.fill", iconColor: .secondary,
                         title: "Occurred",
                         value: alarm.occurredAt.formatted(date: .omitted, time: .shortened),
                         showsChevron: false)
                if let peak = alarm.peakValue {
                    Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                    ValueRow(systemImage: "arrow.up", iconColor: .stateCritical,
                             title: "Peak",
                             value: String(format: "%.0f", peak),
                             showsChevron: false)
                }
                if let t = alarm.threshold {
                    Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                    ValueRow(systemImage: "gauge.medium", iconColor: .stateWarning,
                             title: "Threshold",
                             value: String(format: "%.0f", t),
                             showsChevron: false)
                }
            }
        }
    }

    private var actions: some View {
        VStack(spacing: 8) {
            Button {
                store.acknowledgeAlarm(alarm.id)
                dismiss()
            } label: {
                Label("Acknowledge", systemImage: "checkmark.circle.fill")
            }
            .buttonStyle(PrimaryButtonStyle())

            Button {
                store.snoozeAlarm(alarm.id, hours: 1)
                dismiss()
            } label: {
                Label("Snooze 30 min", systemImage: "clock.badge")
            }
            .buttonStyle(SecondaryButtonStyle())

            Button {
                store.resolveAlarm(alarm.id)
                dismiss()
            } label: {
                Label("Resolve", systemImage: "checkmark.seal.fill")
            }
            .buttonStyle(SecondaryButtonStyle())
        }
        .padding(.top, 4)
    }
}

#Preview {
    AlertsView().environment(MockDataStore.preview)
}
