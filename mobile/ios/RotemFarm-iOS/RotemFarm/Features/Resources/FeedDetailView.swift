//
//  FeedDetailView.swift
//  RotemFarm — Feed intake + silo levels + feeding windows.
//

import Charts
import SwiftUI

struct FeedDetailView: View {
    @Environment(MockDataStore.self) private var store
    let house: House

    var body: some View {
        let daily = store.feedHistory(houseId: house.id, days: 14)

        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                header(daily: daily)

                SectionHeader(title: "Silos")
                silos

                SectionHeader(title: "Last 14 days", trailing: "kg / day")
                chartCard(daily: daily)

                SectionHeader(title: "Today's feeding windows")
                windows
            }
            .padding(14)
        }
        .background(Color.appBackground)
        .navigationTitle("Feed")
        .navigationBarTitleDisplayMode(.inline)
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

    private var silos: some View {
        HStack(spacing: 8) {
            siloTile(name: "Silo A", ration: "Grower", tons: 6.8, pct: 0.62, days: 3.1)
            siloTile(name: "Silo B", ration: "Grower", tons: 2.1, pct: 0.19, days: 0.9)
        }
    }

    private func siloTile(name: String, ration: String, tons: Double, pct: Double, days: Double) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Text(name).font(AppFont.bodyBold)
                Spacer()
                Text(ration).font(AppFont.caption).foregroundStyle(.secondary)
            }
            HStack(alignment: .bottom, spacing: 4) {
                Text(String(format: "%.1f", tons))
                    .font(.system(size: 22, weight: .bold, design: .rounded))
                Text("t remaining")
                    .font(.system(size: 11))
                    .foregroundStyle(.secondary)
                    .padding(.bottom, 3)
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(Color(uiColor: .tertiarySystemFill))
                    Capsule().fill(pct < 0.25 ? Color.stateWarning : Color.farmGreen)
                        .frame(width: geo.size.width * pct)
                }
            }
            .frame(height: 6)
            Text(String(format: "%.1f days runway", days))
                .font(AppFont.caption)
                .foregroundStyle(pct < 0.25 ? Color.stateWarning : .secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(12)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
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

    private var windows: some View {
        CardSection {
            VStack(spacing: 0) {
                windowRow(time: "05:30", state: "Complete", tint: .farmGreen, icon: "checkmark.circle.fill")
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                windowRow(time: "10:00", state: "Complete", tint: .farmGreen, icon: "checkmark.circle.fill")
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                windowRow(time: "14:30", state: "Running · cycle 3/6", tint: .stateInfo,
                          icon: "arrow.triangle.2.circlepath")
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                windowRow(time: "18:30", state: "Scheduled", tint: .secondary, icon: "clock.fill")
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                windowRow(time: "22:30", state: "Suggested by AI", tint: .aiEnd, icon: "sparkles")
            }
        }
    }

    private func windowRow(time: String, state: String, tint: Color, icon: String) -> some View {
        HStack(spacing: 10) {
            Image(systemName: icon)
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(.white)
                .frame(width: 26, height: 26)
                .background(tint, in: RoundedRectangle(cornerRadius: 7))
            Text(time).font(AppFont.body)
            Spacer()
            Text(state).font(AppFont.caption).foregroundStyle(.secondary)
        }
    }
}

#Preview {
    NavigationStack {
        FeedDetailView(house: MockDataStore.preview.houses[2])
    }
    .environment(MockDataStore.preview)
}
