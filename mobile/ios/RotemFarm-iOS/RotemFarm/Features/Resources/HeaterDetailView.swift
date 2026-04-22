//
//  HeaterDetailView.swift
//  RotemFarm — Heater runtime + per-heater status + efficiency tip.
//

import Charts
import SwiftUI

struct HeaterDetailView: View {
    @Environment(MockDataStore.self) private var store
    let house: House
    @State private var daily: [DailyResourcePoint] = []
    @State private var runtime24h: Double?

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                header(daily: daily)

                SectionHeader(title: "Runtime · 14 days", trailing: "hours / day")
                chartCard(daily: daily)
                CardSection {
                    Text("Per-heater runtime breakdown is not currently provided by backend APIs.")
                        .font(AppFont.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle("Heater")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await store.refreshRotemDataForCurrentFarm()
            daily = await store.fetchHeaterHistory(houseId: house.id)
            runtime24h = await store.fetchMonitoringKpis(houseId: house.id)?.heaterHours24h
        }
    }

    private func header(daily: [DailyResourcePoint]) -> some View {
        let today = runtime24h ?? (daily.last?.value ?? 0)
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
                Text("Live runtime from backend")
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
