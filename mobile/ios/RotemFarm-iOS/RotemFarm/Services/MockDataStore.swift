//
//  MockDataStore.swift
//  RotemFarm — In-memory stub data (replaces the real API for now).
//
//  Shaped so that when the API lands, you can swap this for an `APIClient`
//  that exposes the same properties and mutators without touching views.
//

import Foundation
import Observation
import SwiftUI

@Observable
@MainActor
final class MockDataStore {
    private let apiClient: APIClient

    // MARK: Farm context
    var currentFarmId: UUID
    var farms: [Farm] = []

    // MARK: Roster
    var houses: [House] = []
    var flocks: [Flock] = []
    var alarms: [Alarm] = []
    var tips: [AITip] = []
    var team: [TeamMember] = []
    var controllers: [PairedController] = []

    var currentUser: AppUser = AppUser(
        id: UUID(),
        backendId: nil,
        name: "User",
        email: "",
        initials: "U",
        role: .owner,
        assignedHouseIds: []
    )
    var isLoading = false
    var lastError: String?
    private var hasLoadedLiveData = false
    private var liveSensorHistoryByHouse: [UUID: [SensorKind: [SensorSample]]] = [:]

    // MARK: Derived helpers

    var currentFarm: Farm { farms.first { $0.id == currentFarmId } ?? farms[0] }
    var housesForCurrentFarm: [House] { houses.filter { $0.farmId == currentFarmId } }
    var activeFlock: Flock? { flocks.first { $0.isActive && $0.farmId == currentFarmId } }
    var activeAlerts: [Alarm] { alarms.filter { !$0.isAcknowledged } }
    var criticalAlerts: [Alarm] { activeAlerts.filter { $0.severity == .critical } }
    var acknowledgedAlerts: [Alarm] { alarms.filter { $0.isAcknowledged } }

    // MARK: Actions (mutations) — no-op placeholders that update local state

    func acknowledgeAlarm(_ id: UUID) {
        guard let idx = alarms.firstIndex(where: { $0.id == id }) else { return }
        alarms[idx].isAcknowledged = true
        if let backendId = alarms[idx].backendId {
            Task {
                do {
                    try await apiClient.acknowledgeWaterAlert(id: backendId)
                } catch {
                    lastError = error.localizedDescription
                }
            }
        }
    }

    func applyTip(_ id: UUID) {
        tips.removeAll { $0.id == id }
    }

    func dismissTip(_ id: UUID) {
        tips.removeAll { $0.id == id }
    }

    func switchFarm(_ farmId: UUID) { currentFarmId = farmId }

    // MARK: Sample sensor series

    /// Returns ~48 samples of a sensor over the last 24 h for the given house.
    func sensorHistory(houseId: UUID, kind: SensorKind, points: Int = 48) -> [SensorSample] {
        if let liveSamples = liveSensorHistoryByHouse[houseId]?[kind], !liveSamples.isEmpty {
            if liveSamples.count <= points {
                return liveSamples
            }
            return Array(liveSamples.suffix(points))
        }
        var rng = SeededRNG(seed: UInt64(truncatingIfNeeded: houseId.hashValue &+ kind.hashValue))
        let now = Date()
        let center: Double
        let range: Double
        switch kind {
        case .temperature:    center = 28.0; range = 1.8
        case .humidity:       center = 66.0; range = 7.0
        case .co2:            center = 2.2;  range = 0.8
        case .ammonia:        center = 13.0; range = 5.0
        case .staticPressure: center = 28.0; range = 16.0
        case .airflow:        center = 60.0; range = 20.0
        }
        return (0..<points).map { i in
            let t = Double(i) / Double(points - 1)
            let wave = sin(t * 4 * .pi) * range * 0.25
            let drift = (t - 0.5) * range * 0.8
            let noise = Double.random(in: -range * 0.1 ... range * 0.1, using: &rng)
            return SensorSample(
                id: UUID(),
                timestamp: now.addingTimeInterval(-Double(points - i) * 60 * 30),
                value: center + wave + drift + noise
            )
        }
    }

    /// 14-day water consumption (L/day) for a given house.
    func waterHistory(houseId: UUID, days: Int = 14) -> [DailyResourcePoint] {
        let baseTarget: [Double] = (0..<days).map { Double($0) * 85 + 350 }
        let actual: [Double] = (0..<days).map { i in
            baseTarget[i] * Double.random(in: 0.9...1.05)
        }
        return (0..<days).map { i in
            let isLast = i == days - 1
            return DailyResourcePoint(
                day: 9 + i,
                date: Date().addingTimeInterval(-Double(days - 1 - i) * 86_400),
                value: isLast ? 1520 : actual[i],
                target: baseTarget[i],
                isAnomaly: isLast
            )
        }
    }

    func feedHistory(houseId: UUID, days: Int = 14) -> [DailyResourcePoint] {
        let target: [Double] = (0..<days).map { Double($0) * 170 + 400 }
        return (0..<days).map { i in
            DailyResourcePoint(
                day: 9 + i,
                date: Date().addingTimeInterval(-Double(days - 1 - i) * 86_400),
                value: target[i] * Double.random(in: 0.95...1.02),
                target: target[i],
                isAnomaly: i == days - 1
            )
        }
    }

    func heaterHistory(houseId: UUID, days: Int = 14) -> [DailyResourcePoint] {
        // Runtime tapers as birds age
        return (0..<days).map { i in
            let base = max(0.3, 15.0 - Double(i) * 1.0)
            return DailyResourcePoint(
                day: 9 + i,
                date: Date().addingTimeInterval(-Double(days - 1 - i) * 86_400),
                value: base * Double.random(in: 0.9...1.1)
            )
        }
    }

    func hourlyFlow(houseId: UUID) -> [HourlyPoint] {
        (0..<24).map { h in
            let peakWeight = exp(-pow(Double(h - 11), 2) / 28.0) * 60
            return HourlyPoint(hour: h, value: 20 + peakWeight + Double.random(in: -4...4))
        }
    }

    func compareWater() -> [CompareSeries] {
        let colors: [Color] = [.farmGreen, .stateInfo, .stateWarning, .aiEnd, .stateOK,
                               Color(red: 166/255, green: 90/255, blue: 40/255)]
        return housesForCurrentFarm.prefix(6).enumerated().map { (idx, house) in
            let hist = waterHistory(houseId: house.id, days: 7)
            let today = hist.last?.value ?? 0
            let yesterday = hist.dropLast().last?.value ?? 1
            let pct = (today - yesterday) / yesterday * 100
            let state: SensorState = pct > 10 ? .critical : (abs(pct) > 5 ? .warning : .ok)
            return CompareSeries(
                houseName: house.name,
                color: colors[idx % colors.count],
                points: hist,
                todayDelta: (pct >= 0 ? "+" : "") + String(format: "%.0f%%", pct),
                todayDeltaState: state
            )
        }
    }

    func compareFeed() -> [CompareSeries] {
        let colors: [Color] = [.farmGreen, .stateInfo, .stateWarning, .aiEnd, .stateOK,
                               Color(red: 166/255, green: 90/255, blue: 40/255)]
        return housesForCurrentFarm.prefix(6).enumerated().map { (idx, house) in
            let base = feedHistory(houseId: house.id, days: 7)
            let points = base.map { point in
                DailyResourcePoint(
                    day: point.day,
                    date: point.date,
                    value: point.value * Double.random(in: 0.96...1.06),
                    target: point.target,
                    isAnomaly: false
                )
            }
            let today = points.last?.value ?? 0
            let yesterday = points.dropLast().last?.value ?? 1
            let pct = (today - yesterday) / yesterday * 100
            let state: SensorState = pct > 10 ? .critical : (abs(pct) > 5 ? .warning : .ok)
            return CompareSeries(
                houseName: house.name,
                color: colors[idx % colors.count],
                points: points,
                todayDelta: (pct >= 0 ? "+" : "") + String(format: "%.0f%%", pct),
                todayDeltaState: state
            )
        }
    }

    func compareHeater() -> [CompareSeries] {
        let colors: [Color] = [.farmGreen, .stateInfo, .stateWarning, .aiEnd, .stateOK,
                               Color(red: 166/255, green: 90/255, blue: 40/255)]
        return housesForCurrentFarm.prefix(6).enumerated().map { (idx, house) in
            let points = heaterHistory(houseId: house.id, days: 7)
            let today = points.last?.value ?? 0
            let yesterday = points.dropLast().last?.value ?? 1
            let pct = (today - yesterday) / yesterday * 100
            let state: SensorState = pct > 12 ? .critical : (abs(pct) > 6 ? .warning : .ok)
            return CompareSeries(
                houseName: house.name,
                color: colors[idx % colors.count],
                points: points,
                todayDelta: (pct >= 0 ? "+" : "") + String(format: "%.0f%%", pct),
                todayDeltaState: state
            )
        }
    }

    // MARK: init with mock content ------------------------------------------------

    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
        // Build stable UUIDs so views keep identity across reloads
        let farmId = UUID()
        currentFarmId = farmId

        // Houses
        let houseRecipes: [(name: String, type: HouseType, state: SensorState, pill: String,
                            temp: Double, rh: Double, co2: Double, nh3: Double, staticP: Double)] = [
            ("House 1 · Tunnel",  .tunnel,  .ok,       "All OK",   28.4, 68, 2.1, 14, 28),
            ("House 2 · Tunnel",  .tunnel,  .ok,       "All OK",   28.1, 65, 2.0, 12, 26),
            ("House 3 · Tunnel",  .tunnel,  .warning,  "High RH",  28.9, 71, 2.4, 14, 28),
            ("House 4 · Curtain", .curtain, .critical, "Static P", 29.1, 69, 2.3, 15, 42),
            ("House 5 · Tunnel",  .tunnel,  .ok,       "All OK",   28.3, 66, 2.1, 13, 27),
            ("House 6 · Tunnel",  .tunnel,  .ok,       "All OK",   28.0, 64, 2.0, 12, 26)
        ]
        houses = houseRecipes.map { recipe in
            House(
                id: UUID(),
                backendId: nil,
                farmId: farmId,
                name: recipe.name,
                type: recipe.type,
                birdCount: 28_000,
                flockDay: 22,
                state: recipe.state,
                pillText: recipe.pill,
                snapshot: HouseSnapshot(
                    tempC: recipe.temp,
                    humidity: recipe.rh,
                    co2Ppm: recipe.co2,
                    ammoniaPpm: recipe.nh3,
                    staticPressurePa: recipe.staticP,
                    airflowPct: 62,
                    waterLphr: 132,
                    feedCyclesDone: 3,
                    feedCyclesPlanned: 4,
                    tempFill: (recipe.temp - 25) / 6,
                    humidityFill: recipe.rh / 90,
                    co2Fill: recipe.co2 / 5,
                    ammoniaFill: recipe.nh3 / 40,
                    staticFill: recipe.staticP / 45,
                    airflowFill: 0.62
                )
            )
        }

        // Farm
        farms = [
            Farm(id: farmId,
                 backendId: nil,
                 name: "Greenfield Farm",
                 houseIds: houses.map(\.id),
                 totalBirds: 168_400,
                 flockAgeDays: 22,
                 worstState: .critical,
                 alertSummary: "1 critical"),
            Farm(id: UUID(), backendId: nil, name: "Maple Ridge", houseIds: [], totalBirds: 92_000,
                 flockAgeDays: 35, worstState: .warning, alertSummary: "2 alerts"),
            Farm(id: UUID(), backendId: nil, name: "Cedar Point", houseIds: [], totalBirds: 48_000,
                 flockAgeDays: 8, worstState: .ok, alertSummary: "Healthy")
        ]

        // Flock
        let placed = Calendar.current.date(byAdding: .day, value: -22, to: Date())!
        let catch_ = Calendar.current.date(byAdding: .day, value: 20, to: Date())!
        // Cobb 500-like target weight (kg) by day
        let targetWeight: [Double] = (0...42).map { d in
            let day = Double(d)
            return 0.04 + 0.065 * day + 0.0015 * day * day
        }
        let actualWeight: [Double] = (0...22).map { d in
            targetWeight[d] * Double.random(in: 0.92...1.02)
        } + Array(repeating: 0, count: 20)

        flocks = [
            Flock(id: UUID(), farmId: farmId, name: "Flock 24-A", breed: "Cobb 500",
                  placedOn: placed, targetCatchOn: catch_,
                  currentDay: 22, totalDays: 42,
                  birdsPlaced: 170_000, birdsRemaining: 168_400,
                  avgWeightKg: 1.04, targetWeightKg: 1.06,
                  fcr: 1.42, targetFcr: 1.45,
                  livabilityPct: 98.6,
                  dailyGainG: 62,
                  waterFeedRatio: 1.81,
                  epef: 412,
                  state: .ok, statePillText: "On target",
                  isActive: true,
                  actualWeightCurve: actualWeight,
                  targetWeightCurve: targetWeight,
                  log: (0..<5).map { i in
                      FlockLogEntry(id: UUID(), day: 22 - i,
                                    date: Calendar.current.date(byAdding: .day, value: -i, to: Date())!,
                                    deaths: [14, 11, 16, 12, 9][i],
                                    avgWeightKg: 1.04 - Double(i) * 0.06,
                                    note: i == 0 ? "Humidity trending high in H3" : nil)
                  }),
            Flock(id: UUID(), farmId: farmId, name: "Flock 23-F", breed: "Cobb 500",
                  placedOn: placed, targetCatchOn: catch_,
                  currentDay: 42, totalDays: 42,
                  birdsPlaced: 170_000, birdsRemaining: 167_100,
                  avgWeightKg: 2.68, targetWeightKg: 2.72,
                  fcr: 1.51, targetFcr: 1.55,
                  livabilityPct: 98.3,
                  dailyGainG: 64, waterFeedRatio: 1.82, epef: 398,
                  state: .ok, statePillText: "Completed",
                  isActive: false,
                  actualWeightCurve: targetWeight,
                  targetWeightCurve: targetWeight,
                  log: [])
        ]

        // Alarms
        let h3 = houses[2].name
        let h4 = houses[3].name
        let h2 = houses[1].name
        alarms = [
            Alarm(id: UUID(), backendId: nil, severity: .critical,
                  title: "Static pressure 42 Pa",
                  meta: "\(h4) · 6 min ago · over alarm threshold (35 Pa)",
                  houseName: h4,
                  occurredAt: Date().addingTimeInterval(-6 * 60),
                  sparkline: stride(from: 24.0, through: 42.0, by: 1).map { $0 + Double.random(in: -1...1) },
                  threshold: 35, peakValue: 42,
                  recommendation: AIRecommendation(
                      title: "Inspect inlets — likely partially blocked",
                      body: "Static pressure climbing while fans are at full output usually means restricted air intake. Check curtain seals and inlet doors on the south wall first.",
                      confidence: 0.87,
                      primaryAction: "I'm on it",
                      secondaryAction: "Open SOP"),
                  isAcknowledged: false),
            Alarm(id: UUID(), backendId: nil, severity: .warning,
                  title: "Humidity 71% · trending up",
                  meta: "\(h3) · sustained 2 h above 65% target",
                  houseName: h3,
                  occurredAt: Date().addingTimeInterval(-2 * 60 * 60),
                  sparkline: (0..<12).map { 63 + Double($0) * 0.7 },
                  threshold: 65, peakValue: 71,
                  recommendation: AIRecommendation(
                      title: "Open Fan 9 to dry out the litter",
                      body: "Adding one more 54\" fan (≈+12% airflow) brings RH from 71% → 64% in ~25 min without dropping inside temp below the brood band.",
                      confidence: 0.82,
                      primaryAction: "Apply 30 min",
                      secondaryAction: "Why?"),
                  isAcknowledged: false),
            Alarm(id: UUID(), backendId: nil, severity: .warning,
                  title: "Feed line auger #2 stalled",
                  meta: "\(h2) · auto-recovered after 4 min",
                  houseName: h2,
                  occurredAt: Date().addingTimeInterval(-30 * 60),
                  sparkline: [0, 0, 5, 10, 0, 0, 10, 12, 8, 10],
                  threshold: nil, peakValue: nil,
                  recommendation: nil, isAcknowledged: false),
            Alarm(id: UUID(), backendId: nil, severity: .info,
                  title: "Water meter reset detected",
                  meta: "\(houses[0].name) · 02:14 · counter rolled over",
                  houseName: houses[0].name,
                  occurredAt: Date().addingTimeInterval(-8 * 60 * 60),
                  sparkline: [], threshold: nil, peakValue: nil,
                  recommendation: nil, isAcknowledged: false),
            Alarm(id: UUID(), backendId: nil, severity: .acknowledged,
                  title: "CO₂ peaked 3.1k ppm",
                  meta: "\(h3) · 04:12 · resolved in 18 min",
                  houseName: h3,
                  occurredAt: Date().addingTimeInterval(-5 * 60 * 60),
                  sparkline: [], threshold: nil, peakValue: nil,
                  recommendation: nil, isAcknowledged: true),
            Alarm(id: UUID(), backendId: nil, severity: .acknowledged,
                  title: "Controller offline · 47 s",
                  meta: "\(h2) gateway · reconnected",
                  houseName: h2,
                  occurredAt: Date().addingTimeInterval(-6 * 60 * 60),
                  sparkline: [], threshold: nil, peakValue: nil,
                  recommendation: nil, isAcknowledged: true)
        ]

        // AI tips
        tips = [
            AITip(id: UUID(), category: .air, scope: h3, severity: .warning,
                  title: "Open Fan 9 to dry out the litter",
                  body: "RH has been > 70% for 2 hours. Wet litter at day 22 raises ammonia within 24 h and hurts paw quality (downgrade risk).",
                  primaryAction: "Apply 30 min", secondaryAction: "Dismiss",
                  confidence: 0.87, createdAt: Date().addingTimeInterval(-20 * 60)),
            AITip(id: UUID(), category: .heat, scope: "Farm-wide", severity: .warning,
                  title: "Pre-cool houses before noon peak",
                  body: "Outside temp will hit 31°C at 14:00. Drop set-points by 0.5°C from 11:30 to 12:30 to bank cool air; ramp tunnel fans from stage 4→5 at 12:45.",
                  primaryAction: "Schedule", secondaryAction: "Edit",
                  confidence: 0.79, createdAt: Date().addingTimeInterval(-1 * 60 * 60)),
            AITip(id: UUID(), category: .feed, scope: "Flock 24-A", severity: .warning,
                  title: "You're 4% behind feed target",
                  body: "Current intake is 2.32 kg / bird vs Cobb 500 target of 2.42 kg. Add a fifth feeding window (22:30) to catch up before grow-out window closes.",
                  primaryAction: "Add window", secondaryAction: "Compare",
                  confidence: 0.74, createdAt: Date().addingTimeInterval(-3 * 60 * 60))
        ]

        // Team
        team = [
            TeamMember(id: UUID(), name: "Phuc Le", initials: "PL", role: .owner,
                       scope: "all houses", isYou: true),
            TeamMember(id: UUID(), name: "Maria Rivera", initials: "MR", role: .manager,
                       scope: "all houses · alerts on", isYou: false),
            TeamMember(id: UUID(), name: "Joe Tran", initials: "JT", role: .worker,
                       scope: "House 1–3", isYou: false),
            TeamMember(id: UUID(), name: "Sam Khan", initials: "SK", role: .worker,
                       scope: "House 4–6", isYou: false),
            TeamMember(id: UUID(), name: "Dr. Vega", initials: "DV", role: .vet,
                       scope: "read-only · all flocks", isYou: false)
        ]

        // Controllers
        controllers = houses.enumerated().map { (i, h) in
            PairedController(
                id: UUID(),
                model: i < 4 ? "Platinum Touch" : "Trio",
                serial: "RT-\(String(format: "%04d", 2204 + i))",
                houseName: h.name,
                lastSeen: Date().addingTimeInterval(-Double(i) * 30),
                state: h.state
            )
        }

        // User
        currentUser = AppUser(id: UUID(), backendId: nil, name: "Phuc Le", email: "bobgel12@gmail.com",
                              initials: "PL", role: .owner, assignedHouseIds: [])
    }

    func refreshCoreDataIfNeeded() async {
        if !hasLoadedLiveData {
            await reloadCoreData()
        }
    }

    func reloadCoreData() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let user = try await apiClient.fetchUser()
            currentUser = AppUser(
                id: Self.stableUUID(prefix: "user", intID: user.id),
                backendId: user.id,
                name: user.username,
                email: user.email,
                initials: Self.initials(from: user.username),
                role: user.isStaff ? .owner : .manager,
                assignedHouseIds: []
            )

            let apiFarms = try await apiClient.fetchFarms()
            guard let firstFarm = apiFarms.first else {
                lastError = "No farms available for this account."
                return
            }
            let mappedFarms: [Farm] = apiFarms.map { farm in
                Farm(
                    id: Self.stableUUID(prefix: "farm", intID: farm.id),
                    backendId: farm.id,
                    name: farm.name,
                    houseIds: [],
                    totalBirds: 0,
                    flockAgeDays: 0,
                    worstState: .ok,
                    alertSummary: "\(farm.activeHouses) active houses"
                )
            }
            farms = mappedFarms
            currentFarmId = Self.stableUUID(prefix: "farm", intID: firstFarm.id)

            let apiHouses = try await apiClient.fetchHouses(farmID: firstFarm.id)
            var mappedHouses: [House] = []
            var mappedAlarms: [Alarm] = []

            for apiHouse in apiHouses where apiHouse.isActive {
                let monitoring = try await apiClient.fetchLatestMonitoring(houseID: apiHouse.id)
                let houseID = Self.stableUUID(prefix: "house", intID: apiHouse.id)
                let snapshot = HouseSnapshot(
                    tempC: monitoring?.averageTemperature ?? 0,
                    humidity: monitoring?.humidity ?? 0,
                    co2Ppm: 0,
                    ammoniaPpm: 0,
                    staticPressurePa: monitoring?.staticPressure ?? 0,
                    airflowPct: monitoring?.airflowPercentage ?? 0,
                    waterLphr: monitoring?.waterConsumption ?? 0,
                    feedCyclesDone: 0,
                    feedCyclesPlanned: 0,
                    tempFill: Self.clamp01((monitoring?.averageTemperature ?? 0) / 35),
                    humidityFill: Self.clamp01((monitoring?.humidity ?? 0) / 100),
                    co2Fill: 0,
                    ammoniaFill: 0,
                    staticFill: Self.clamp01((monitoring?.staticPressure ?? 0) / 60),
                    airflowFill: Self.clamp01((monitoring?.airflowPercentage ?? 0) / 100)
                )
                let state = Self.stateForSnapshot(snapshot)
                mappedHouses.append(
                    House(
                        id: houseID,
                        backendId: apiHouse.id,
                        farmId: currentFarmId,
                        name: "House \(apiHouse.houseNumber)",
                        type: .tunnel,
                        birdCount: 0,
                        flockDay: apiHouse.currentDay,
                        state: state,
                        pillText: state == .ok ? "All OK" : (state == .warning ? "Check conditions" : "Needs attention"),
                        snapshot: snapshot
                    )
                )

                let alerts = try await apiClient.fetchWaterAlerts(houseID: apiHouse.id)
                let houseAlerts = alerts.map { alert in
                    Alarm(
                        id: Self.stableUUID(prefix: "alert", intID: alert.id),
                        backendId: alert.id,
                        severity: Self.mapSeverity(alert.severity, acknowledged: alert.isAcknowledged),
                        title: alert.message,
                        meta: "House \(alert.houseNumber ?? apiHouse.houseNumber)",
                        houseName: "House \(alert.houseNumber ?? apiHouse.houseNumber)",
                        occurredAt: alert.createdAt ?? Date(),
                        sparkline: [],
                        threshold: nil,
                        peakValue: alert.increasePercentage,
                        recommendation: nil,
                        isAcknowledged: alert.isAcknowledged
                    )
                }
                mappedAlarms.append(contentsOf: houseAlerts)
            }

            houses = mappedHouses
            alarms = mappedAlarms.sorted { $0.occurredAt > $1.occurredAt }
            if let idx = farms.firstIndex(where: { $0.id == currentFarmId }) {
                farms[idx].houseIds = houses.map(\.id)
            }
            do {
                let apiFlocks = try await apiClient.fetchFlocks(farmID: firstFarm.id)
                flocks = apiFlocks.map { apiFlock in
                    let metrics = Self.metricsFromStatus(apiFlock.status)
                    let totalDays = Self.totalDays(arrival: apiFlock.arrivalDate, expectedHarvest: apiFlock.expectedHarvestDate)
                    let currentDay = max(0, apiFlock.currentAgeDays)
                    let mortalityRate = apiFlock.mortalityRate ?? 0
                    let livability = max(0, 100 - mortalityRate)
                    let avgWeightKg = Self.estimateWeightKg(day: currentDay)
                    let targetWeightKg = Self.estimateWeightKg(day: currentDay + 1)
                    return Flock(
                        id: Self.stableUUID(prefix: "flock", intID: apiFlock.id),
                        farmId: currentFarmId,
                        name: "Flock \(apiFlock.batchNumber)",
                        breed: apiFlock.breedName,
                        placedOn: apiFlock.arrivalDate ?? Date(),
                        targetCatchOn: apiFlock.expectedHarvestDate ?? Date().addingTimeInterval(40 * 86_400),
                        currentDay: currentDay,
                        totalDays: totalDays,
                        birdsPlaced: apiFlock.initialChickenCount,
                        birdsRemaining: apiFlock.currentChickenCount,
                        avgWeightKg: avgWeightKg,
                        targetWeightKg: targetWeightKg,
                        fcr: metrics.fcr,
                        targetFcr: 1.45,
                        livabilityPct: livability,
                        dailyGainG: max(0, avgWeightKg) * 1000 / Double(max(currentDay, 1)),
                        waterFeedRatio: metrics.waterFeedRatio,
                        epef: Self.epef(day: currentDay, livability: livability, weightKg: avgWeightKg, fcr: metrics.fcr),
                        state: metrics.state,
                        statePillText: metrics.pill,
                        isActive: apiFlock.isActive,
                        actualWeightCurve: Self.actualWeightCurve(forDay: currentDay),
                        targetWeightCurve: Self.targetWeightCurve(totalDays: totalDays),
                        log: []
                    )
                }
            } catch {
                // Keep current mock flocks if live flock endpoints fail.
            }
            hasLoadedLiveData = true
            lastError = nil
        } catch {
            lastError = error.localizedDescription
        }
    }

    func resetToMockData() {
        hasLoadedLiveData = false
        liveSensorHistoryByHouse = [:]
    }

    func refreshSensorHistory(houseId: UUID, kind: SensorKind, points: Int) async {
        guard
            let house = houses.first(where: { $0.id == houseId }),
            let backendID = house.backendId
        else { return }
        do {
            let history = try await apiClient.fetchHouseMonitoringHistory(houseID: backendID, limit: max(points, 24))
            let mapped: [SensorSample] = history.compactMap { point in
                let value: Double?
                switch kind {
                case .temperature: value = point.averageTemperature
                case .humidity: value = point.humidity
                case .co2: value = nil
                case .ammonia: value = nil
                case .staticPressure: value = point.staticPressure
                case .airflow: value = point.airflowPercentage
                }
                guard let resolvedValue = value else { return nil }
                return SensorSample(
                    id: UUID(),
                    timestamp: point.timestamp,
                    value: resolvedValue,
                    probeName: nil
                )
            }
            if !mapped.isEmpty {
                var houseSamples = liveSensorHistoryByHouse[houseId] ?? [:]
                houseSamples[kind] = mapped.sorted(by: { $0.timestamp < $1.timestamp })
                liveSensorHistoryByHouse[houseId] = houseSamples
            }
        } catch {
            lastError = error.localizedDescription
        }
    }

    // MARK: Preview helper --------------------------------------------------------

    static var preview: MockDataStore {
        MockDataStore()
    }

    private static func stableUUID(prefix: String, intID: Int) -> UUID {
        let value = "\(prefix)-\(intID)".hashValue.magnitude % 999_999_999_999
        let string = String(format: "00000000-0000-0000-0000-%012llu", value)
        return UUID(uuidString: string) ?? UUID()
    }

    private static func initials(from name: String) -> String {
        let parts = name.split(separator: " ")
        let letters = parts.prefix(2).compactMap { $0.first }.map(String.init).joined()
        return letters.isEmpty ? "U" : letters.uppercased()
    }

    private static func clamp01(_ value: Double) -> Double {
        min(max(value, 0), 1)
    }

    private static func stateForSnapshot(_ snapshot: HouseSnapshot) -> SensorState {
        if snapshot.staticPressurePa > 35 || snapshot.humidity > 75 {
            return .critical
        }
        if snapshot.humidity > 65 || snapshot.tempC > 30 {
            return .warning
        }
        return .ok
    }

    private static func mapSeverity(_ value: String, acknowledged: Bool) -> AlertSeverity {
        if acknowledged { return .acknowledged }
        switch value.lowercased() {
        case "critical", "high":
            return .critical
        case "warning", "medium":
            return .warning
        default:
            return .info
        }
    }

    private static func totalDays(arrival: Date?, expectedHarvest: Date?) -> Int {
        guard let arrival, let expectedHarvest else { return 42 }
        let days = Calendar.current.dateComponents([.day], from: arrival, to: expectedHarvest).day ?? 42
        return max(days, 1)
    }

    private static func estimateWeightKg(day: Int) -> Double {
        let d = Double(max(day, 0))
        return max(0.04, 0.04 + 0.065 * d + 0.0015 * d * d)
    }

    private static func targetWeightCurve(totalDays: Int) -> [Double] {
        (0...max(totalDays, 1)).map { estimateWeightKg(day: $0) }
    }

    private static func actualWeightCurve(forDay day: Int) -> [Double] {
        let target = targetWeightCurve(totalDays: 42)
        let clampedDay = min(max(day, 0), target.count - 1)
        let curve = target.enumerated().map { idx, value in
            if idx <= clampedDay {
                return value * Double.random(in: 0.95...1.03)
            }
            return 0
        }
        return curve
    }

    private static func epef(day: Int, livability: Double, weightKg: Double, fcr: Double) -> Int {
        let denominator = max(Double(day) * max(fcr, 0.1), 1)
        let score = (livability * weightKg * 100) / denominator
        return Int(score.rounded())
    }

    private static func metricsFromStatus(_ status: String) -> (state: SensorState, pill: String, fcr: Double, waterFeedRatio: Double) {
        switch status.lowercased() {
        case "completed":
            return (.ok, "Completed", 1.50, 1.82)
        case "harvesting", "cancelled":
            return (.warning, status.capitalized, 1.55, 1.85)
        case "setup", "arrival":
            return (.warning, status.capitalized, 1.40, 1.78)
        default:
            return (.ok, "On target", 1.45, 1.80)
        }
    }
}

// Deterministic RNG so charts render stably in previews
private struct SeededRNG: RandomNumberGenerator {
    private var state: UInt64
    init(seed: UInt64) { state = seed == 0 ? 0xdeadbeef : seed }
    mutating func next() -> UInt64 {
        state &+= 0x9E3779B97F4A7C15
        var z = state
        z = (z ^ (z &>> 30)) &* 0xBF58476D1CE4E5B9
        z = (z ^ (z &>> 27)) &* 0x94D049BB133111EB
        return z ^ (z &>> 31)
    }
}
