//
//  FeedDetailView.swift
//  RotemFarm — Feed intake + silo levels + feeding windows.
//

import Charts
import SwiftUI

struct FeedDetailView: View {
    @Environment(MockDataStore.self) private var store
    let house: House
    @State private var daily: [DailyResourcePoint] = []

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                header(daily: daily)

                SectionHeader(title: "Last 14 days", trailing: "kg / day")
                chartCard(daily: daily)
                CardSection {
                    Text("Live silo and feeding-window telemetry is not exposed by current backend endpoints.")
                        .font(AppFont.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle("Feed")
        .navigationBarTitleDisplayMode(.inline)
        .task {
            await store.refreshRotemDataForCurrentFarm()
            daily = await store.fetchFeedHistory(houseId: house.id)
        }
    }

    private func header(daily: [DailyResourcePoint]) -> some View {
        let today = daily.last?.value ?? 0
        let target = daily.last?.target ?? 0
        let pct = target > 0 ? (today - target) / target * 100 : 0
        let state: SensorState = pct < -5 ? .warning : .ok
        return HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("\(house.name) · Day \(house.flockDay)")
                    .font(AppFont.caption).foregroundStyle(.secondary)
                HStack(alignment: .firstTextBaseline, spacing: 4) {
                    Text(Int(today).formatted()).font(AppFont.bigNum)
                    Text("kg today")
                        .font(.system(size: 14, weight: .semibold, design: .rounded))
                        .foregroundStyle(.secondary)
                }
                Text("Target \(Int(target).formatted()) kg · \(pct >= 0 ? "+" : "")\(String(format: "%.0f%%", pct))")
                    .font(AppFont.caption)
                    .foregroundStyle(state.tint)
            }
            Spacer()
            Image(systemName: "shippingbox.fill")
                .foregroundStyle(.white)
                .padding(8)
                .background(Color(red: 166/255, green: 90/255, blue: 40/255),
                            in: RoundedRectangle(cornerRadius: 10))
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
                        y: .value("kg", p.value)
                    )
                    .foregroundStyle(p.isAnomaly ? Color.stateWarning
                                     : Color(red: 166/255, green: 90/255, blue: 40/255))
                    .cornerRadius(4)
                    if let t = p.target {
                        RuleMark(y: .value("target", t))
                            .foregroundStyle(Color.secondary.opacity(0.6))
                            .lineStyle(StrokeStyle(lineWidth: 1, dash: [3, 3]))
                    }
                }
            }
            .frame(height: 200)
            .chartYAxis { AxisMarks(position: .leading) }
        }
    }

}

#Preview {
    NavigationStack {
        FeedDetailView(house: MockDataStore.preview.houses[2])
    }
    .environment(MockDataStore.preview)
}
