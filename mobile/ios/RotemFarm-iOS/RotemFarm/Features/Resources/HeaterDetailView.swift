//
//  HeaterDetailView.swift
//  RotemFarm — Heater runtime + per-heater status + efficiency tip.
//

import Charts
import SwiftUI

struct HeaterDetailView: View {
    @Environment(MockDataStore.self) private var store
    let house: House

    var body: some View {
        let daily = store.heaterHistory(houseId: house.id, days: 14)

        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                header(daily: daily)

                SectionHeader(title: "Heaters")
                LazyVGrid(columns: [GridItem(.flexible(), spacing: 8), GridItem(.flexible(), spacing: 8)],
                          spacing: 8) {
                    heaterTile(name: "Heater 1", isOn: false, runtime: 32, state: .ok)
                    heaterTile(name: "Heater 2", isOn: false, runtime: 28, state: .ok)
                    heaterTile(name: "Heater 3", isOn: true,  runtime: 44, state: .warning)
                    heaterTile(name: "Heater 4", isOn: false, runtime: 12, state: .ok)
                }

                SectionHeader(title: "Runtime · 14 days", trailing: "hours / day")
                chartCard(daily: daily)

                AICard(
                    label: "Efficiency tip",
                    title: "Heater 3 is working 38% harder than its peers",
                    message: "Over the last 5 days, Heater 3 ran 41 min/day more than Heaters 1, 2, and 4 for the same target temp. Likely dirty coil or low fuel pressure. Schedule a service check.",
                    severity: .warning, severityText: "House 3",
                    primaryAction: ("Create work order", {}),
                    secondaryAction: ("Dismiss", {})
                )
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle("Heater")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func header(daily: [DailyResourcePoint]) -> some View {
        let today = daily.last?.value ?? 0
        return HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("\(house.name) · Day \(house.flockDay)")
                    .font(AppFont.caption).foregroundStyle(.secondary)
                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(String(format: "%.1f", today)).font(AppFont.bigNum)
                    Text("h today")
                        .font(.system(size: 14, weight: .semibold, design: .rounded))
                        .foregroundStyle(.secondary)
                }
                Text("1 of 4 heaters currently running")
                    .font(AppFont.caption).foregroundStyle(.secondary)
            }
            Spacer()
            Image(systemName: "flame.fill")
                .foregroundStyle(.white)
                .padding(8)
                .background(Color.stateWarning, in: RoundedRectangle(cornerRadius: 10))
        }
        .padding(14)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.hero))
    }

    private func heaterTile(name: String, isOn: Bool, runtime: Int, state: SensorState) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "flame.fill")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(isOn ? .white : Color.stateWarning)
                    .frame(width: 26, height: 26)
                    .background(isOn ? Color.stateWarning : Color.warnSoft,
                                in: RoundedRectangle(cornerRadius: 7))
                Spacer()
                PillBadge(text: isOn ? "On" : "Off",
                          style: isOn ? .warning : .neutral)
            }
            Text(name).font(AppFont.bodyBold)
            Text("\(runtime) min today")
                .font(AppFont.caption)
                .foregroundStyle(state == .ok ? .secondary : state.tint)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(11)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
    }

    private func chartCard(daily: [DailyResourcePoint]) -> some View {
        CardSection {
            Chart {
                ForEach(daily) { p in
                    BarMark(
                        x: .value("day", "D\(p.day)"),
                        y: .value("h", p.value)
                    )
                    .foregroundStyle(Color.stateWarning)
                    .cornerRadius(4)
                }
            }
            .frame(height: 180)
            .chartYAxis { AxisMarks(position: .leading) }
        }
    }
}

#Preview {
    NavigationStack {
        HeaterDetailView(house: MockDataStore.preview.houses[0])
    }
    .environment(MockDataStore.preview)
}
