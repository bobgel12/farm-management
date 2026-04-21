//
//  TipsHubView.swift
//  RotemFarm — AI Tips hub: For You / Today / By topic + daily checklist.
//

import SwiftUI

struct TipsHubView: View {
    @Environment(MockDataStore.self) private var store
    @Environment(\.dismiss) private var dismiss

    enum Filter: String, CaseIterable, Hashable {
        case forYou, today, byTopic
        var label: String {
            switch self {
            case .forYou:  "For You"
            case .today:   "Today"
            case .byTopic: "By topic"
            }
        }
    }

    @State private var filter: Filter = .forYou

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    AppSegmented(
                        selection: $filter,
                        options: Filter.allCases,
                        labels: Dictionary(uniqueKeysWithValues: Filter.allCases.map { ($0, $0.label) })
                    )
                    .padding(.bottom, 4)

                    switch filter {
                    case .forYou:  forYou
                    case .today:   today
                    case .byTopic: byTopic
                    }

                    SectionHeader(title: "Daily best practices")
                    checklist
                }
                .padding(14)
            }
            .background(Color.appBackground)
            .navigationTitle("AI Tips")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    // MARK: For You

    private var forYou: some View {
        VStack(spacing: 10) {
            ForEach(store.tips) { tip in
                AICard(
                    label: tip.category.title,
                    title: tip.title,
                    message: tip.body,
                    severity: tip.severity == .critical ? .critical : .warning,
                    severityText: tip.scope,
                    primaryAction: (tip.primaryAction, { store.applyTip(tip.id) }),
                    secondaryAction: (tip.secondaryAction, { store.dismissTip(tip.id) })
                )
            }
            if store.tips.isEmpty {
                emptyState
            }
        }
    }

    // MARK: Today

    private var today: some View {
        VStack(spacing: 10) {
            timelineCard(time: "05:30", title: "Pre-dawn check",
                         body: "Water consumption normal. Fans idle stage 1. No overnight incidents.",
                         state: .ok)
            timelineCard(time: "08:12", title: "CO₂ spiked to 3.1k ppm · resolved",
                         body: "Stage stepped up to 3 for 18 min. Current 2.2k ppm.",
                         state: .warning)
            timelineCard(time: "10:40", title: "AI tip applied: dry litter in H3",
                         body: "Fan 9 added · RH 71% → 66% in 22 min.",
                         state: .ok)
        }
    }

    private func timelineCard(time: String, title: String, body: String, state: SensorState) -> some View {
        HStack(alignment: .top, spacing: 10) {
            VStack(spacing: 4) {
                Circle().fill(state.tint).frame(width: 10, height: 10)
                Rectangle().fill(Color.appSeparator).frame(width: 2, height: 60)
            }
            .padding(.top, 2)
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(time).font(AppFont.captionBold).foregroundStyle(.secondary)
                    Spacer()
                    PillBadge(text: state.label,
                              style: state == .ok ? .ok : (state == .warning ? .warning : .critical))
                }
                Text(title).font(AppFont.bodyBold)
                Text(body).font(AppFont.caption).foregroundStyle(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
            .padding(12)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
        }
    }

    // MARK: By topic

    private var byTopic: some View {
        VStack(spacing: 10) {
            ForEach(TipCategory.allCases, id: \.self) { cat in
                HStack(spacing: 10) {
                    RoundedRectangle(cornerRadius: 10)
                        .fill(cat.tint.opacity(0.15))
                        .frame(width: 40, height: 40)
                        .overlay(
                            Image(systemName: icon(for: cat))
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundStyle(cat.tint)
                        )
                    VStack(alignment: .leading, spacing: 2) {
                        Text(cat.title).font(AppFont.bodyBold)
                        Text("\(store.tips.filter { $0.category == cat }.count) active · \(exampleDesc(for: cat))")
                            .font(AppFont.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    Image(systemName: "chevron.right")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(.tertiary)
                }
                .padding(12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
            }
        }
    }

    private func icon(for cat: TipCategory) -> String {
        switch cat {
        case .air:          "wind"
        case .heat:         "thermometer.sun.fill"
        case .feed:         "shippingbox.fill"
        case .biosecurity:  "shield.lefthalf.filled"
        }
    }

    private func exampleDesc(for cat: TipCategory) -> String {
        switch cat {
        case .air:          "ventilation & RH"
        case .heat:         "temp setpoints"
        case .feed:         "rations & timing"
        case .biosecurity:  "litter & pests"
        }
    }

    // MARK: Checklist

    private var checklist: some View {
        CardSection {
            VStack(spacing: 0) {
                checkRow(title: "Walk every house at sunrise", done: true)
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                checkRow(title: "Record mortality by house", done: true)
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                checkRow(title: "Check water-to-feed ratio trend", done: true)
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                checkRow(title: "Inspect litter moisture in H3", done: false)
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                checkRow(title: "Confirm backup generator fuel", done: false)
            }
        }
    }

    private func checkRow(title: String, done: Bool) -> some View {
        HStack(spacing: 10) {
            Image(systemName: done ? "checkmark.circle.fill" : "circle")
                .font(.system(size: 18, weight: .semibold))
                .foregroundStyle(done ? Color.farmGreen : .secondary)
            Text(title)
                .font(AppFont.body)
                .foregroundStyle(done ? .secondary : .primary)
                .strikethrough(done)
            Spacer()
        }
    }

    private var emptyState: some View {
        VStack(spacing: 6) {
            Image(systemName: "sparkles")
                .font(.system(size: 28))
                .foregroundStyle(Color.aiEnd)
            Text("All tips applied").font(AppFont.bodyBold)
            Text("Your farm is on target — check back later.")
                .font(AppFont.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding(30)
        .background(BrandGradient.aiSoft, in: RoundedRectangle(cornerRadius: AppRadius.card))
    }
}

#Preview {
    TipsHubView().environment(MockDataStore.preview)
}
