//
//  DashboardView.swift
//  RotemFarm — Home tab: flock hero + sensor grid + AI tip.
//

import SwiftUI

struct DashboardView: View {
    @Environment(MockDataStore.self) private var store
    @State private var showTips = false
    @State private var showHouseDetail: House? = nil

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 14) {
                    allFarmsSection
                    heroCard
                    environmentByHouseGrid
                    alertsPeek
                    if let tip = store.tips.first {
                        AICard(
                            label: "AI Tip",
                            title: tip.title,
                            message: tip.body,
                            severity: .warning,
                            severityText: tip.scope,
                            primaryAction: ("Apply", { store.applyTip(tip.id) }),
                            secondaryAction: ("Why?", { showTips = true })
                        )
                    }
                    moreTipsLink
                }
                .padding(.horizontal, 14)
                .padding(.bottom, 24)
            }
            .background(Color.appBackground)
            .navigationTitle(store.currentFarm.name)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    FarmSwitcherMenu()
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showTips = true } label: {
                        Image(systemName: "sparkles")
                    }
                }
            }
            .sheet(isPresented: $showTips) { TipsHubView() }
            .navigationDestination(item: $showHouseDetail) { house in
                HouseDetailView(house: house)
            }
            .task { await store.refreshCoreDataIfNeeded() }
            .refreshable { await store.reloadCoreData() }
        }
    }

    // MARK: All farms (summary)

    private var allFarmsSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("All farms").font(AppFont.title)
                Spacer()
                if store.isLoading && store.farmHomeOverviewByFarmId.isEmpty && !store.farms.isEmpty {
                    ProgressView().scaleEffect(0.8)
                }
            }
            .padding(.horizontal, 2)

            CardSection {
                if store.farms.isEmpty {
                    Text("No farms linked to this account.")
                        .font(AppFont.caption)
                        .foregroundStyle(.secondary)
                } else {
                    ForEach(store.farms) { farm in
                        let overview = store.farmHomeOverviewByFarmId[farm.id]
                        HStack(alignment: .top, spacing: 8) {
                            VStack(alignment: .leading, spacing: 4) {
                                Text(farm.name).font(AppFont.bodyBold)
                                Text(farmOverviewLine(farm: farm, overview: overview))
                                    .font(.system(size: 11))
                                    .foregroundStyle(.secondary)
                                if let ac = overview?.houseRelatedAlertCount, ac > 0 {
                                    Text("\(ac) house alert\(ac == 1 ? "" : "s")")
                                        .font(.system(size: 11, weight: .medium))
                                        .foregroundStyle(Color.stateWarning)
                                }
                            }
                            Spacer()
                            if farm.id == store.currentFarmId {
                                PillBadge(text: "Current", style: .info)
                            }
                        }
                        if farm.id != store.farms.last?.id {
                            Divider().overlay(Color.appSeparator)
                        }
                    }
                }
            }
        }
    }

    private func farmOverviewLine(farm: Farm, overview: FarmHomeOverview?) -> String {
        let n = max(overview?.houseCount ?? 0, farm.activeHousesFromApi)
        if let avg = overview?.avgDayAge {
            return "\(n) houses · avg day \(avg)"
        }
        if n > 0 {
            return "\(n) houses"
        }
        return "Loading overview…"
    }

    // MARK: Hero flock card

    private var heroCard: some View {
        ZStack(alignment: .topLeading) {
            BrandGradient.hero
                .clipShape(RoundedRectangle(cornerRadius: AppRadius.hero))
                .overlay(
                    Circle()
                        .fill(Color.white.opacity(0.06))
                        .frame(width: 160, height: 160)
                        .offset(x: 140, y: -60)
                )

            VStack(alignment: .leading, spacing: 8) {
                let flock = store.activeFlock
                Text((flock?.name ?? "Flock") + " · Day \(flock?.currentDay ?? 0) of \(flock?.totalDays ?? 42)")
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(Color.white.opacity(0.85))
                    .tracking(0.5)
                Text("\(store.currentFarm.totalBirds.formatted()) birds across \(store.housesForCurrentFarm.count) houses")
                    .font(AppFont.title)
                    .foregroundStyle(.white)
                HStack(spacing: 20) {
                    heroStat(String(format: "%.2f kg", flock?.avgWeightKg ?? 0), "avg weight")
                    heroStat(String(format: "%.2f", flock?.fcr ?? 0), "FCR")
                    heroStat(String(format: "%.1f%%", flock?.livabilityPct ?? 0), "livability")
                }
                .padding(.top, 6)
            }
            .padding(16)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }

    private func heroStat(_ value: String, _ label: String) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(value)
                .font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundStyle(.white)
            Text(label.uppercased())
                .font(.system(size: 10, weight: .medium))
                .tracking(0.5)
                .foregroundStyle(Color.white.opacity(0.85))
        }
    }

    // MARK: Per-house environment

    private var environmentByHouseGrid: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Environment by house").font(AppFont.title)
                Spacer()
                PillBadge(text: "Live", style: .live)
            }
            .padding(.horizontal, 2)

            if store.housesForCurrentFarm.isEmpty {
                CardSection {
                    Text("No live house environment data for this farm yet.")
                        .font(AppFont.caption)
                        .foregroundStyle(.secondary)
                }
            } else {
                LazyVGrid(columns: [GridItem(.flexible(), spacing: 8), GridItem(.flexible(), spacing: 8)],
                          spacing: 8) {
                    ForEach(store.housesForCurrentFarm) { house in
                        Button {
                            showHouseDetail = house
                        } label: {
                            CardSection {
                                VStack(alignment: .leading, spacing: 8) {
                                    HStack(alignment: .top) {
                                        Text(house.name)
                                            .font(AppFont.bodyBold)
                                            .foregroundStyle(.primary)
                                        Spacer()
                                        PillBadge(
                                            text: house.pillText,
                                            style: house.state == .critical ? .critical : (house.state == .warning ? .warning : .ok)
                                        )
                                    }
                                    environmentMetricRow("Temp", String(format: "%.1f °C", house.snapshot.tempC))
                                    environmentMetricRow("Humidity", String(format: "%.0f %%", house.snapshot.humidity))
                                    environmentMetricRow("Airflow", String(format: "%.0f %%", house.snapshot.airflowPct))
                                    environmentMetricRow("Static", String(format: "%.0f Pa", house.snapshot.staticPressurePa))
                                }
                            }
                        }
                        .buttonStyle(.plain)
                    }
                }
            }
        }
    }

    private func environmentMetricRow(_ label: String, _ value: String) -> some View {
        HStack(spacing: 8) {
            Text(label)
                .font(AppFont.caption)
                .foregroundStyle(.secondary)
            Spacer(minLength: 0)
            Text(value)
                .font(AppFont.caption)
                .foregroundStyle(.primary)
        }
    }

    // MARK: Alerts peek

    private var alertsPeek: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Text("Active alerts").font(AppFont.title)
                Spacer()
                NavigationLink(destination: AlertsView()) {
                    Text("View all").font(AppFont.caption)
                }
            }
            .padding(.horizontal, 2)

            CardSection {
                ForEach(store.activeAlerts.prefix(5)) { alarm in
                    NavigationLink(destination: AlertDetailView(alarm: alarm)) {
                        AlertRow(
                            systemImage: alarm.severity.systemImage,
                            title: alarm.title,
                            meta: alarm.meta,
                            state: alarm.severity.state
                        )
                    }
                    .buttonStyle(.plain)
                    if alarm.id != store.activeAlerts.prefix(5).last?.id {
                        Divider().overlay(Color.appSeparator)
                    }
                }
            }
        }
    }

    private var moreTipsLink: some View {
        Button { showTips = true } label: {
            HStack {
                Image(systemName: "sparkles")
                Text("More AI tips")
                Spacer()
                Image(systemName: "chevron.right").font(.system(size: 12, weight: .semibold))
            }
            .font(AppFont.bodyBold)
            .foregroundStyle(Color.aiEnd)
            .padding(14)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(BrandGradient.aiSoft, in: RoundedRectangle(cornerRadius: AppRadius.card))
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    DashboardView()
        .environment(MockDataStore.preview)
        .environment(AuthService.previewSignedIn())
}
