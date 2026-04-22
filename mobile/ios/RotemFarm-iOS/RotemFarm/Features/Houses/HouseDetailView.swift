//
//  HouseDetailView.swift
//  RotemFarm — Live monitor for a single house.
//

import Charts
import SwiftUI

struct HouseDetailView: View {
    @Environment(MockDataStore.self) private var store
    let house: House

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                headerLine

                heroTempCard

                LazyVGrid(columns: [GridItem(.flexible(), spacing: 8), GridItem(.flexible(), spacing: 8)],
                          spacing: 8) {
                    NavigationLink(value: SensorKind.humidity) {
                        SensorCard(title: "Humidity", value: String(format: "%.0f", house.snapshot.humidity),
                                   unit: "%", state: .warning, systemImage: "drop.fill",
                                   fillFraction: house.snapshot.humidityFill)
                    }.buttonStyle(.plain)
                    NavigationLink(value: SensorKind.co2) {
                        SensorCard(title: "CO₂", value: String(format: "%.1f", house.snapshot.co2Ppm),
                                   unit: "k ppm", state: .ok, systemImage: "cloud.fog.fill",
                                   fillFraction: house.snapshot.co2Fill)
                    }.buttonStyle(.plain)
                    NavigationLink(value: SensorKind.ammonia) {
                        SensorCard(title: "NH₃ Ammonia", value: String(format: "%.0f", house.snapshot.ammoniaPpm),
                                   unit: "ppm", state: .ok, systemImage: "wind",
                                   fillFraction: house.snapshot.ammoniaFill)
                    }.buttonStyle(.plain)
                    NavigationLink(value: SensorKind.staticPressure) {
                        SensorCard(title: "Static Pressure",
                                   value: String(format: "%.0f", house.snapshot.staticPressurePa),
                                   unit: "Pa", state: house.state == .critical ? .critical : .ok,
                                   systemImage: "gauge.medium",
                                   fillFraction: house.snapshot.staticFill)
                    }.buttonStyle(.plain)
                }

                SectionHeader(title: "Resources")
                resourcesStrip

                SectionHeader(title: "Equipment")
                equipmentList
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle(house.name)
        .navigationBarTitleDisplayMode(.inline)
        .navigationDestination(for: SensorKind.self) { kind in
            SensorHistoryView(house: house, kind: kind)
        }
    }

    // MARK: Header

    private var headerLine: some View {
        HStack {
            VStack(alignment: .leading, spacing: 2) {
                Text("\(house.type.rawValue) · Day \(house.flockDay) · \(house.birdCount.formatted()) birds")
                    .font(AppFont.caption)
                    .foregroundStyle(.secondary)
                Text("\(house.name) — Live").font(AppFont.title)
            }
            Spacer()
            PillBadge(text: "Live", style: .live)
        }
    }

    // MARK: Hero temperature card

    private var heroTempCard: some View {
        NavigationLink(value: SensorKind.temperature) {
            HeroMetricCard(
                label: "Inside Temperature",
                value: String(format: "%.1f", house.snapshot.tempC),
                unit: "°C",
                target: "Target: 26.5–28.0°C",
                delta: (text: "▲ 0.9°", state: .warning)
            ) {
                let samples = store.sensorHistory(houseId: house.id, kind: .temperature, points: 24)
                Chart(samples) { s in
                    AreaMark(x: .value("t", s.timestamp), y: .value("v", s.value))
                        .foregroundStyle(LinearGradient(
                            colors: [Color.farmGreen.opacity(0.4), .clear],
                            startPoint: .top, endPoint: .bottom))
                    LineMark(x: .value("t", s.timestamp), y: .value("v", s.value))
                        .foregroundStyle(Color.farmGreen)
                        .lineStyle(StrokeStyle(lineWidth: 2, lineCap: .round))
                }
                .chartXAxis(.hidden)
                .chartYAxis(.hidden)
                .frame(width: 120, height: 60)
            }
        }
        .buttonStyle(.plain)
    }

    // MARK: Resources strip

    private var resourcesStrip: some View {
        let waterRealtime = store.waterForOperationsList(houseId: house.id)
        let heaterRuntime = store.heaterHoursForOperationsList(houseId: house.id)
        return HStack(spacing: 8) {
            NavigationLink(destination: WaterDetailView(house: house)) {
                resourceTile(icon: "drop.fill", tint: .stateInfo,
                             label: "Water",
                             value: waterRealtime.map { String(format: "%.0f", $0) } ?? "-",
                             unit: store.isRealtimeLoadedForHouse(house.id) ? "L" : "loading...")
            }.buttonStyle(.plain)
            NavigationLink(destination: FeedDetailView(house: house)) {
                resourceTile(icon: "shippingbox.fill",
                             tint: Color(red: 166/255, green: 90/255, blue: 40/255),
                             label: "Feed", value: "\(house.snapshot.feedCyclesDone)", unit: "/ \(house.snapshot.feedCyclesPlanned) cycles")
            }.buttonStyle(.plain)
            NavigationLink(destination: HeaterDetailView(house: house)) {
                resourceTile(icon: "flame.fill", tint: .stateWarning,
                             label: "Heater",
                             value: heaterRuntime.map { String(format: "%.1f", $0) } ?? "-",
                             unit: store.isRealtimeLoadedForHouse(house.id) ? "h today" : "loading...")
            }.buttonStyle(.plain)
        }
    }

    private func resourceTile(icon: String, tint: Color, label: String, value: String, unit: String) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(.white)
                .frame(width: 26, height: 26)
                .background(tint, in: RoundedRectangle(cornerRadius: 7))
            Text(label.uppercased())
                .font(.system(size: 10, weight: .semibold))
                .tracking(0.4)
                .foregroundStyle(.secondary)
            HStack(alignment: .firstTextBaseline, spacing: 2) {
                Text(value).font(.system(size: 18, weight: .bold, design: .rounded))
                Text(unit).font(.system(size: 10)).foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
    }

    // MARK: Equipment list

    private var equipmentList: some View {
        CardSection {
            VStack(spacing: 0) {
                ValueRow(systemImage: "fan.fill", iconColor: .farmGreen,
                         title: "Tunnel fans", value: "8 / 10 on · 62%")
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                ValueRow(systemImage: "aqi.medium", iconColor: .aiEnd,
                         title: "Cool pads", value: "Auto · 40%")
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                ValueRow(systemImage: "flame.fill", iconColor: .stateWarning,
                         title: "Heaters", value: "Off")
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                ValueRow(systemImage: "drop.fill", iconColor: .stateInfo,
                         title: "Water flow", value: String(format: "%.0f L / hr", house.snapshot.waterLphr))
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                ValueRow(systemImage: "shippingbox.fill",
                         iconColor: Color(red: 166/255, green: 90/255, blue: 40/255),
                         title: "Feed augers", value: "Cycle \(house.snapshot.feedCyclesDone) of \(house.snapshot.feedCyclesPlanned)")
            }
        }
    }
}

#Preview {
    NavigationStack {
        HouseDetailView(house: MockDataStore.preview.houses[2])
    }
    .environment(MockDataStore.preview)
}
