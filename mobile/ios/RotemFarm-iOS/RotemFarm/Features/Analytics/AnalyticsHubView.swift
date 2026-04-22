import SwiftUI

struct AnalyticsHubView: View {
    @Environment(MockDataStore.self) private var store

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    SectionHeader(title: "Business intelligence")
                    LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 8) {
                        ForEach(store.biKPIs) { kpi in
                            KPICard(label: kpi.label, value: kpi.value, delta: kpi.delta, deltaState: .ok)
                        }
                    }

                    SectionHeader(title: "Reporting")
                    CardSection {
                        VStack(spacing: 10) {
                            NavigationLink(destination: ReportsView()) {
                                ValueRow(systemImage: "chart.bar.doc.horizontal", iconColor: .stateInfo, title: "Performance reports", value: "\(store.generatedReports.count) generated")
                            }
                            NavigationLink(destination: CompareView()) {
                                ValueRow(systemImage: "chart.xyaxis.line", iconColor: .farmGreen, title: "Comparison dashboard", value: "Water, feed, heater")
                            }
                        }
                    }

                    SectionHeader(title: "Recent exports")
                    CardSection {
                        VStack(spacing: 8) {
                            ForEach(store.generatedReports) { report in
                                HStack {
                                    VStack(alignment: .leading, spacing: 2) {
                                        Text(report.title).font(AppFont.body)
                                        Text("\(report.scope) · \(report.generatedAt.formatted(date: .abbreviated, time: .shortened))")
                                            .font(AppFont.caption)
                                            .foregroundStyle(.secondary)
                                    }
                                    Spacer()
                                }
                            }
                        }
                    }
                }
                .padding(14)
            }
            .background(Color.appBackground)
            .navigationTitle("Analytics")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    FarmSwitcherMenu()
                }
            }
        }
    }
}

