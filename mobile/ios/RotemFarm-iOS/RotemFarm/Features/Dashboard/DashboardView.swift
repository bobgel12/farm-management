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
                    heroCard
                    sensorGrid
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
            .navigationTitle("Greenfield Farm")
            .toolbar {
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

    // MARK: Sensor grid

    private var sensorGrid: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text("Environment").font(AppFont.title)
                Spacer()
                PillBadge(text: "Live", style: .live)
            }
            .padding(.horizontal, 2)

            let snap = store.housesForCurrentFarm.first?.snapshot ?? HouseSnapshot(
                tempC: 0,
                humidity: 0,
                co2Ppm: 0,
                ammoniaPpm: 0,
                staticPressurePa: 0,
                airflowPct: 0,
                waterLphr: 0,
                feedCyclesDone: 0,
                feedCyclesPlanned: 0,
                tempFill: 0,
                humidityFill: 0,
                co2Fill: 0,
                ammoniaFill: 0,
                staticFill: 0,
                airflowFill: 0
            )
            LazyVGrid(columns: Array(repeating: GridItem(.flexible(), spacing: 8), count: 3),
                      spacing: 8) {
                SensorCard(title: "Temp",     value: String(format: "%.1f", snap.tempC),  unit: "°C",
                           state: .ok, systemImage: "thermometer.medium", fillFraction: snap.tempFill)
                SensorCard(title: "Humidity", value: String(format: "%.0f", snap.humidity), unit: "%",
                           state: .warning, systemImage: "drop.fill", fillFraction: snap.humidityFill)
                SensorCard(title: "CO₂",      value: String(format: "%.1f", snap.co2Ppm), unit: "k ppm",
                           state: .ok, systemImage: "cloud.fog.fill", fillFraction: snap.co2Fill)
                SensorCard(title: "NH₃",      value: String(format: "%.0f", snap.ammoniaPpm), unit: "ppm",
                           state: .ok, systemImage: "wind", fillFraction: snap.ammoniaFill)
                SensorCard(title: "Airflow",  value: String(format: "%.0f", snap.airflowPct), unit: "%",
                           state: .ok, systemImage: "fan.fill", fillFraction: snap.airflowFill)
                SensorCard(title: "Static",   value: String(format: "%.0f", snap.staticPressurePa), unit: "Pa",
                           state: .critical, systemImage: "gauge.medium", fillFraction: snap.staticFill)
            }
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
                ForEach(store.activeAlerts.prefix(2)) { alarm in
                    NavigationLink(destination: AlertDetailView(alarm: alarm)) {
                        AlertRow(
                            systemImage: alarm.severity.systemImage,
                            title: alarm.title,
                            meta: alarm.meta,
                            state: alarm.severity.state
                        )
                    }
                    .buttonStyle(.plain)
                    if alarm.id != store.activeAlerts.prefix(2).last?.id {
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
