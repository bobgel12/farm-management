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
    private let verboseLogging: Bool

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
    var tasks: [FarmTask] = []
    var programs: [Program] = []
    var workers: [WorkerProfile] = []
    var organizations: [Organization] = []
    var organizationMembers: [OrganizationMember] = []
    var biKPIs: [BIKPI] = []
    var generatedReports: [ReportItem] = []
    var rotemHealth: [RotemFarmHealth] = []

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
    private var farmRotemIDs: [UUID: String] = [:]
    private var lastFarmScrapeAt: [UUID: Date] = [:]
    /// Per-farm snapshot for home: house count, avg growth day, house alarm count (from monitoring dashboard).
    var farmHomeOverviewByFarmId: [UUID: FarmHomeOverview] = [:]
    /// Latest KPI row (feed/water DOD, etc.) keyed by house UUID.
    var houseKpisByHouseId: [UUID: APIHouseMonitoringKpis] = [:]
    /// Heater hours shown on Operations: daily total from heater-history for flock day when available, else KPI 24h.
    var houseHeaterHoursForListByHouseId: [UUID: Double] = [:]
    /// Realtime water values resolved from per-house monitoring history fetch.
    var houseWaterRealtimeByHouseId: [UUID: Double] = [:]
    /// Realtime heater values resolved from per-house heater history fetch.
    var houseHeaterRealtimeByHouseId: [UUID: Double] = [:]
    /// Tracks houses whose realtime water/heater history has finished loading this cycle.
    var houseRealtimeLoadedIds: Set<UUID> = []
    /// Farm-level monitoring freshness metadata from backend cache envelope.
    var monitoringFreshnessByFarmId: [UUID: APIFreshnessMeta] = [:]

    // MARK: Derived helpers

    var currentFarm: Farm {
        farms.first(where: { $0.id == currentFarmId }) ?? Farm(
            id: currentFarmId,
            backendId: nil,
            name: "No farm selected",
            houseIds: [],
            totalBirds: 0,
            flockAgeDays: 0,
            worstState: .ok,
            alertSummary: "No alerts",
            activeHousesFromApi: 0
        )
    }
    var housesForCurrentFarm: [House] { houses.filter { $0.farmId == currentFarmId } }
    var activeFlock: Flock? { flocks.first { $0.isActive && $0.farmId == currentFarmId } }
    var activeAlerts: [Alarm] { alarms.filter { !$0.isAcknowledged } }
    var criticalAlerts: [Alarm] { activeAlerts.filter { $0.severity == .critical } }
    var acknowledgedAlerts: [Alarm] { alarms.filter { $0.isAcknowledged } }

    // MARK: Actions (mutations) — no-op placeholders that update local state

    func acknowledgeAlarm(_ id: UUID) {
        guard let idx = alarms.firstIndex(where: { $0.id == id }) else { return }
        alarms[idx].isAcknowledged = true
        log("Acknowledge alarm id=\(id.uuidString)")
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

    func snoozeAlarm(_ id: UUID, hours: Int = 1) {
        guard let idx = alarms.firstIndex(where: { $0.id == id }) else { return }
        log("Snooze alarm id=\(id.uuidString) hours=\(hours)")
        if let backendId = alarms[idx].backendId {
            Task {
                do {
                    try await apiClient.snoozeWaterAlert(id: backendId, hours: hours)
                } catch {
                    lastError = error.localizedDescription
                }
            }
        }
    }

    func resolveAlarm(_ id: UUID) {
        guard let idx = alarms.firstIndex(where: { $0.id == id }) else { return }
        alarms[idx].isAcknowledged = true
        log("Resolve alarm id=\(id.uuidString)")
        if let backendId = alarms[idx].backendId {
            Task {
                do {
                    try await apiClient.resolveWaterAlert(id: backendId)
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

    func switchFarm(_ farmId: UUID) {
        currentFarmId = farmId
        Task {
            await reloadSelectedFarmData()
        }
    }

    func updateTaskStatus(_ taskId: UUID, to status: TaskStatus) {
        guard let idx = tasks.firstIndex(where: { $0.id == taskId }) else { return }
        log("Update task id=\(taskId.uuidString) status=\(status.rawValue)")
        tasks[idx].status = status
        guard let backendId = tasks[idx].backendId else { return }
        Task {
            do {
                let payloadStatus: String
                switch status {
                case .done: payloadStatus = "done"
                case .inProgress: payloadStatus = "in_progress"
                case .blocked: payloadStatus = "blocked"
                case .pending: payloadStatus = "pending"
                }
                try await apiClient.updateTaskStatus(taskID: backendId, status: payloadStatus, notes: tasks[idx].notes)
            } catch {
                lastError = error.localizedDescription
            }
        }
    }

    func toggleProgram(_ programId: UUID) {
        guard let idx = programs.firstIndex(where: { $0.id == programId }) else { return }
        programs[idx].isActive.toggle()
        programs[idx].updatedAt = Date()
        log("Toggle program id=\(programId.uuidString) -> \(programs[idx].isActive)")
        guard let backendId = programs[idx].backendId else { return }
        let nextState = programs[idx].isActive
        Task {
            do {
                try await apiClient.updateProgram(programID: backendId, isActive: nextState)
            } catch {
                // Revert optimistic toggle if backend update fails.
                if let revertIdx = programs.firstIndex(where: { $0.id == programId }) {
                    programs[revertIdx].isActive.toggle()
                    programs[revertIdx].updatedAt = Date()
                }
                lastError = error.localizedDescription
            }
        }
    }

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

    // MARK: init with live-first content ------------------------------------------

    init(apiClient: APIClient = APIClient()) {
        self.apiClient = apiClient
        self.verboseLogging = (ProcessInfo.processInfo.environment["ROTEM_IOS_VERBOSE_LOGS"] ?? "").lowercased() == "true"
        currentFarmId = UUID()
        farms = []
        houses = []
        flocks = []
        alarms = []
        tips = []
        team = []
        controllers = []
        tasks = []
        programs = []
        workers = []
        organizations = []
        organizationMembers = []
        biKPIs = []
        generatedReports = []
        rotemHealth = []
        currentUser = AppUser(
            id: UUID(),
            backendId: nil,
            name: "User",
            email: "",
            initials: "U",
            role: .manager,
            assignedHouseIds: []
        )
    }

    func refreshCoreDataIfNeeded() async {
        if !hasLoadedLiveData {
            log("refreshCoreDataIfNeeded -> reloadCoreData()")
            await reloadCoreData()
        }
    }

    func reloadCoreData() async {
        log("reloadCoreData() start")
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
                farms = []
                houses = []
                flocks = []
                alarms = []
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
                    alertSummary: "\(farm.activeHouses) active houses",
                    activeHousesFromApi: farm.activeHouses
                )
            }
            farms = mappedFarms
            farmRotemIDs = Dictionary(uniqueKeysWithValues: apiFarms.map {
                (Self.stableUUID(prefix: "farm", intID: $0.id), $0.rotemFarmID ?? "")
            })
            let firstFarmID = Self.stableUUID(prefix: "farm", intID: firstFarm.id)
            if !farms.contains(where: { $0.id == currentFarmId }) {
                currentFarmId = firstFarmID
            }
            await reloadSelectedFarmData()
            await refreshFarmHomeOverviews()
            hasLoadedLiveData = true
            lastError = nil
            log("reloadCoreData() success farms=\(farms.count) houses=\(houses.count) alarms=\(alarms.count) flocks=\(flocks.count)")
        } catch {
            lastError = error.localizedDescription
            log("reloadCoreData() failed error=\(error.localizedDescription)")
        }
    }

    func reloadSelectedFarmData() async {
        guard let selectedFarm = farms.first(where: { $0.id == currentFarmId }),
              let selectedFarmBackendID = selectedFarm.backendId else {
            houses = []
            flocks = []
            alarms = []
            return
        }
        isLoading = true
        // Prevent stale water/heater values during farm reload.
        houseWaterRealtimeByHouseId = [:]
        houseHeaterRealtimeByHouseId = [:]
        houseRealtimeLoadedIds = []
        monitoringFreshnessByFarmId = [:]
        houseHeaterHoursForListByHouseId = [:]
        defer { isLoading = false }
        do {
            log("reloadSelectedFarmData() farmBackendID=\(selectedFarmBackendID)")
            let apiHouses = try await apiClient.fetchHouses(farmID: selectedFarmBackendID)
            var mappedHouses: [House] = []
            var mappedAlarms: [Alarm] = []

            for apiHouse in apiHouses where apiHouse.isActive {
                let monitoring = try? await apiClient.fetchLatestMonitoring(houseID: apiHouse.id)
                let houseID = Self.stableUUID(prefix: "house", intID: apiHouse.id)
                let fallbackSnapshot = houses.first(where: { $0.backendId == apiHouse.id })?.snapshot
                let resolvedTemp = monitoring?.averageTemperature ?? fallbackSnapshot?.tempC ?? 0
                let resolvedHumidity = monitoring?.humidity ?? fallbackSnapshot?.humidity ?? 0
                let resolvedStatic = monitoring?.staticPressure ?? fallbackSnapshot?.staticPressurePa ?? 0
                let resolvedAirflow = monitoring?.airflowPercentage ?? fallbackSnapshot?.airflowPct ?? 0
                let resolvedWater = monitoring?.waterConsumption ?? fallbackSnapshot?.waterLphr ?? 0
                let snapshot = HouseSnapshot(
                    tempC: resolvedTemp,
                    humidity: resolvedHumidity,
                    co2Ppm: fallbackSnapshot?.co2Ppm ?? 0,
                    ammoniaPpm: fallbackSnapshot?.ammoniaPpm ?? 0,
                    staticPressurePa: resolvedStatic,
                    airflowPct: resolvedAirflow,
                    waterLphr: resolvedWater,
                    feedCyclesDone: fallbackSnapshot?.feedCyclesDone ?? 0,
                    feedCyclesPlanned: fallbackSnapshot?.feedCyclesPlanned ?? 0,
                    tempFill: Self.clamp01(resolvedTemp / 35),
                    humidityFill: Self.clamp01(resolvedHumidity / 100),
                    co2Fill: fallbackSnapshot?.co2Fill ?? 0,
                    ammoniaFill: fallbackSnapshot?.ammoniaFill ?? 0,
                    staticFill: Self.clamp01(resolvedStatic / 60),
                    airflowFill: Self.clamp01(resolvedAirflow / 100)
                )
                let state = Self.stateForSnapshot(snapshot)
                mappedHouses.append(
                    House(
                        id: houseID,
                        backendId: apiHouse.id,
                        farmId: selectedFarm.id,
                        name: "House \(apiHouse.houseNumber)",
                        type: .tunnel,
                        birdCount: 0,
                        flockDay: apiHouse.currentDay,
                        state: state,
                        pillText: state == .ok ? "All OK" : (state == .warning ? "Check conditions" : "Needs attention"),
                        snapshot: snapshot
                    )
                )

                let alerts = (try? await apiClient.fetchWaterAlerts(houseID: apiHouse.id)) ?? []
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
            // Phase 2: after house-wide load, fetch per-house realtime water + heater histories.
            var kpiByHouse: [UUID: APIHouseMonitoringKpis] = [:]
            var waterRealtimeByHouse: [UUID: Double] = [:]
            var heaterRealtimeByHouse: [UUID: Double] = [:]
            var loadedRealtimeHouseIDs: Set<UUID> = []
            let kpiClient = apiClient
            await withTaskGroup(of: (UUID, APIHouseMonitoringKpis?, Double?, Double?).self) { group in
                for h in mappedHouses {
                    guard let bid = h.backendId else { continue }
                    let hid = h.id
                    group.addTask {
                        let k = try? await kpiClient.fetchHouseMonitoringKpis(houseID: bid)
                        let rotemWaterHistory = (try? await kpiClient.fetchRotemWaterHistory(
                            houseID: bid,
                            days: 5
                        )) ?? []
                        let waterRealtime = rotemWaterHistory.last?.consumptionAvg
                        let heaterHistory = (try? await kpiClient.fetchHouseHeaterHistory(houseID: bid)) ?? []
                        let heaterRealtime = heaterHistory.sorted(by: { $0.date < $1.date }).last?.value
                        return (hid, k, waterRealtime, heaterRealtime)
                    }
                }
                for await (hid, kpi, waterRealtime, heaterRealtime) in group {
                    if let kpi {
                        kpiByHouse[hid] = kpi
                    }
                    if let waterRealtime {
                        waterRealtimeByHouse[hid] = waterRealtime
                    }
                    if let heaterRealtime {
                        heaterRealtimeByHouse[hid] = heaterRealtime
                    }
                    loadedRealtimeHouseIDs.insert(hid)
                }
            }
            houseKpisByHouseId = kpiByHouse
            houseWaterRealtimeByHouseId = waterRealtimeByHouse
            houseHeaterRealtimeByHouseId = heaterRealtimeByHouse
            houseRealtimeLoadedIds = loadedRealtimeHouseIDs
            alarms = mappedAlarms.sorted { $0.occurredAt > $1.occurredAt }
            if let idx = farms.firstIndex(where: { $0.id == currentFarmId }) {
                farms[idx].houseIds = houses.map(\.id)
                farms[idx].alertSummary = alarms.isEmpty ? "No alerts" : "\(alarms.count) alerts"
                farms[idx].worstState = Self.farmState(from: mappedHouses)
            }
            do {
                let apiFlocks = try await apiClient.fetchFlocks(farmID: selectedFarmBackendID)
                var rows: [Flock] = []
                for apiFlock in apiFlocks {
                    let metrics = Self.metricsFromStatus(apiFlock.status)
                    let totalDays = Self.totalDays(arrival: apiFlock.arrivalDate, expectedHarvest: apiFlock.expectedHarvestDate)
                    let currentDay = max(0, apiFlock.currentAgeDays)
                    let mortalityRate = apiFlock.mortalityRate ?? 0
                    let livability = max(0, 100 - mortalityRate)
                    let performance = (try? await apiClient.fetchFlockPerformance(flockID: apiFlock.id)) ?? []
                    let sortedPerf = performance.sorted { (lhs, rhs) in
                        (lhs.flockAgeDays ?? 0) < (rhs.flockAgeDays ?? 0)
                    }
                    let actualWeightCurve = Self.actualWeightCurve(from: sortedPerf, totalDays: max(totalDays, 42))
                    let latestPerf = sortedPerf.last
                    let avgWeightKg = (latestPerf?.averageWeightGrams ?? Self.estimateWeightKg(day: currentDay) * 1000) / 1000
                    let targetWeightKg = Self.estimateWeightKg(day: currentDay + 1)
                    let fcr = latestPerf?.feedConversionRatio ?? metrics.fcr
                    let dailyGain = Self.estimateDailyGain(from: sortedPerf, fallbackDay: currentDay, fallbackWeightKg: avgWeightKg)
                    let logEntries = Self.buildFlockLogs(from: sortedPerf)
                    rows.append(
                        Flock(
                            id: Self.stableUUID(prefix: "flock", intID: apiFlock.id),
                            farmId: selectedFarm.id,
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
                            fcr: fcr,
                            targetFcr: 1.45,
                            livabilityPct: livability,
                            dailyGainG: dailyGain,
                            waterFeedRatio: metrics.waterFeedRatio,
                            epef: Self.epef(day: max(currentDay, 1), livability: livability, weightKg: avgWeightKg, fcr: fcr),
                            state: metrics.state,
                            statePillText: metrics.pill,
                            isActive: apiFlock.isActive,
                            actualWeightCurve: actualWeightCurve,
                            targetWeightCurve: Self.targetWeightCurve(totalDays: max(totalDays, 42)),
                            log: logEntries
                        )
                    )
                }
                flocks = rows.sorted { $0.placedOn > $1.placedOn }
            } catch {
                flocks = []
            }
            // Load task center, program library, and workers from live APIs.
            var loadedTasks: [FarmTask] = []
            for house in mappedHouses {
                guard let houseBackendID = house.backendId else { continue }
                let apiTasks = (try? await apiClient.fetchTasks(houseID: houseBackendID)) ?? []
                loadedTasks.append(contentsOf: apiTasks.map { task in
                    let status: TaskStatus = task.isCompleted ? .done : .pending
                    let dueAt = Calendar.current.date(
                        byAdding: .day,
                        value: max(task.dayOffset - house.flockDay, 0),
                        to: Date()
                    ) ?? Date()
                    return FarmTask(
                        id: Self.stableUUID(prefix: "task", intID: task.id),
                        backendId: task.id,
                        title: task.taskName,
                        houseId: house.id,
                        assigneeName: task.completedBy.isEmpty ? "Unassigned" : task.completedBy,
                        dueAt: dueAt,
                        status: status,
                        notes: task.notes.isEmpty ? task.description : task.notes
                    )
                })
            }
            tasks = loadedTasks.sorted(by: { $0.dueAt < $1.dueAt })

            let apiPrograms = (try? await apiClient.fetchPrograms()) ?? []
            programs = apiPrograms.map { item in
                Program(
                    id: Self.stableUUID(prefix: "program", intID: item.id),
                    backendId: item.id,
                    name: item.name,
                    category: "Duration \(item.durationDays)d",
                    isActive: item.isActive,
                    assignedHouseIds: mappedHouses.map(\.id),
                    updatedAt: Date()
                )
            }

            let apiWorkers = (try? await apiClient.fetchWorkers(farmID: selectedFarmBackendID)) ?? []
            workers = apiWorkers.filter(\.isActive).map { item in
                WorkerProfile(
                    id: Self.stableUUID(prefix: "worker", intID: item.id),
                    backendId: item.id,
                    name: item.name,
                    role: Self.mapWorkerRole(item.role),
                    phone: item.phone,
                    farmName: selectedFarm.name,
                    assignedHouseIds: []
                )
            }
            organizations = []
            organizationMembers = []
            biKPIs = []
            generatedReports = []
            if let integration = try? await apiClient.fetchFarmIntegrationStatus(farmID: selectedFarmBackendID) {
                rotemHealth = [
                    RotemFarmHealth(
                        id: UUID(),
                        farmName: selectedFarm.name,
                        devicesOnline: integration.integrationStatus == "active" ? mappedHouses.count : 0,
                        devicesTotal: mappedHouses.count,
                        criticalCount: integration.integrationStatus == "error" ? 1 : 0,
                        warningCount: integration.integrationType == "none" ? 1 : 0
                    )
                ]
            } else {
                rotemHealth = []
            }
            tips = []
            controllers = houses.map { h in
                PairedController(
                    id: UUID(),
                    model: "Rotem",
                    serial: h.backendId.map { "RT-\($0)" } ?? "RT-N/A",
                    houseName: h.name,
                    lastSeen: Date(),
                    state: h.state
                )
            }
            lastError = nil
            log("reloadSelectedFarmData() success houses=\(houses.count) alarms=\(alarms.count) flocks=\(flocks.count) tasks=\(tasks.count) programs=\(programs.count) workers=\(workers.count)")
        } catch {
            lastError = error.localizedDescription
            log("reloadSelectedFarmData() failed error=\(error.localizedDescription)")
        }
    }

    func resetSessionData() {
        hasLoadedLiveData = false
        liveSensorHistoryByHouse = [:]
        farmHomeOverviewByFarmId = [:]
        houseKpisByHouseId = [:]
        houseHeaterHoursForListByHouseId = [:]
        houseWaterRealtimeByHouseId = [:]
        houseHeaterRealtimeByHouseId = [:]
        houseRealtimeLoadedIds = []
        farms = []
        houses = []
        flocks = []
        alarms = []
        tips = []
        tasks = []
        programs = []
        workers = []
        organizations = []
        organizationMembers = []
        biKPIs = []
        generatedReports = []
        rotemHealth = []
    }

    func refreshSensorHistory(houseId: UUID, kind: SensorKind, points: Int) async {
        guard
            let house = houses.first(where: { $0.id == houseId }),
            let backendID = house.backendId
        else { return }
        do {
            log("refreshSensorHistory() house=\(houseId.uuidString) kind=\(kind.rawValue) points=\(points)")
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
                log("refreshSensorHistory() loaded samples=\(mapped.count)")
            }
        } catch {
            lastError = error.localizedDescription
            log("refreshSensorHistory() failed error=\(error.localizedDescription)")
        }
    }

    func fetchMonitoringHistory(
        houseId: UUID,
        limit: Int = 200,
        startDate: Date? = nil,
        endDate: Date? = nil
    ) async -> [APIHouseMonitoringPoint] {
        guard let backendID = houses.first(where: { $0.id == houseId })?.backendId else { return [] }
        do {
            return try await apiClient.fetchHouseMonitoringHistory(
                houseID: backendID,
                limit: limit,
                startDate: startDate,
                endDate: endDate
            )
        } catch {
            lastError = error.localizedDescription
            return []
        }
    }

    func fetchMonitoringKpis(houseId: UUID) async -> APIHouseMonitoringKpis? {
        guard let backendID = houses.first(where: { $0.id == houseId })?.backendId else { return nil }
        do {
            return try await apiClient.fetchHouseMonitoringKpis(houseID: backendID)
        } catch {
            lastError = error.localizedDescription
            return nil
        }
    }

    func fetchHeaterHistory(houseId: UUID) async -> [DailyResourcePoint] {
        guard let backendID = houses.first(where: { $0.id == houseId })?.backendId else { return [] }
        do {
            return try await apiClient.fetchHouseHeaterHistory(houseID: backendID)
        } catch {
            lastError = error.localizedDescription
            return []
        }
    }

    func fetchFarmHouseMeta(farmBackendID: Int) async -> [APIFarmHouseMeta] {
        do {
            return try await apiClient.fetchFarmHouseMeta(farmID: farmBackendID)
        } catch {
            lastError = error.localizedDescription
            return []
        }
    }

    func fetchFarmMonitoringDashboard(farmBackendID: Int) async -> [APIFarmHouseMonitoringCard] {
        do {
            let result = try await apiClient.fetchFarmMonitoringDashboard(farmID: farmBackendID)
            if let farmUUID = farms.first(where: { $0.backendId == farmBackendID })?.id,
               let freshness = result.freshness {
                monitoringFreshnessByFarmId[farmUUID] = freshness
            }
            return result.houses
        } catch {
            lastError = error.localizedDescription
            return []
        }
    }

    func refreshMonitoringNowForCurrentFarm() async {
        guard let farmBackendID = farms.first(where: { $0.id == currentFarmId })?.backendId else { return }
        do {
            if let freshness = try await apiClient.refreshFarmMonitoringNow(farmID: farmBackendID) {
                monitoringFreshnessByFarmId[currentFarmId] = freshness
            }
            await reloadSelectedFarmData()
            await refreshFarmHomeOverviews()
        } catch {
            lastError = error.localizedDescription
        }
    }

    func fetchProgramTasks(programId: UUID, day: Int? = nil) async -> [APIProgramTask] {
        guard let backendProgramID = programs.first(where: { $0.id == programId })?.backendId else { return [] }
        do {
            return try await apiClient.fetchProgramTasks(programID: backendProgramID, day: day)
        } catch {
            lastError = error.localizedDescription
            return []
        }
    }

    func assignProgram(programId: UUID, houseIDs: [UUID]) async {
        guard
            let backendProgramID = programs.first(where: { $0.id == programId })?.backendId,
            let farmBackendID = farms.first(where: { $0.id == currentFarmId })?.backendId
        else { return }
        let mappedHouseIDs = houseIDs.compactMap { houseID in
            houses.first(where: { $0.id == houseID })?.backendId
        }
        do {
            try await apiClient.assignProgram(
                programID: backendProgramID,
                farmIDs: [farmBackendID],
                houseIDs: mappedHouseIDs
            )
            await reloadSelectedFarmData()
        } catch {
            lastError = error.localizedDescription
        }
    }

    func fetchCurrentFarmIntegrationStatus() async -> APIFarmIntegrationStatus? {
        guard let farmBackendID = farms.first(where: { $0.id == currentFarmId })?.backendId else { return nil }
        do {
            return try await apiClient.fetchFarmIntegrationStatus(farmID: farmBackendID)
        } catch {
            lastError = error.localizedDescription
            return nil
        }
    }

    func updateCurrentFarmIntegration(type: String, username: String?, password: String?) async {
        guard let farmBackendID = farms.first(where: { $0.id == currentFarmId })?.backendId else { return }
        do {
            try await apiClient.updateFarmIntegration(
                farmID: farmBackendID,
                integrationType: type,
                username: username,
                password: password
            )
            await reloadSelectedFarmData()
        } catch {
            lastError = error.localizedDescription
        }
    }

    func houseKpi(for houseId: UUID) -> APIHouseMonitoringKpis? {
        houseKpisByHouseId[houseId]
    }

    func heaterHoursForOperationsList(houseId: UUID) -> Double? {
        houseHeaterRealtimeByHouseId[houseId]
    }

    func waterForOperationsList(houseId: UUID) -> Double? {
        houseWaterRealtimeByHouseId[houseId]
    }

    func isRealtimeLoadedForHouse(_ houseId: UUID) -> Bool {
        houseRealtimeLoadedIds.contains(houseId)
    }

    /// Loads per-farm house counts, average growth day, and house alarm totals for the home screen.
    func refreshFarmHomeOverviews() async {
        guard !farms.isEmpty else {
            farmHomeOverviewByFarmId = [:]
            return
        }
        let client = apiClient
        var next: [UUID: FarmHomeOverview] = [:]
        await withTaskGroup(of: (UUID, FarmHomeOverview?).self) { group in
            for farm in farms {
                guard let bid = farm.backendId else { continue }
                let farmUUID = farm.id
                let fallbackCount = farm.activeHousesFromApi
                group.addTask {
                    do {
                        let result = try await client.fetchFarmMonitoringDashboard(farmID: bid)
                        let days = result.houses.compactMap { card -> Int? in
                            if let g = card.growthDay { return g }
                            return card.houseCurrentDay
                        }
                        let avg: Int? = {
                            guard !days.isEmpty else { return nil }
                            return days.reduce(0, +) / days.count
                        }()
                        let count = result.totalHouses > 0 ? result.totalHouses : result.houses.count
                        let overview = FarmHomeOverview(
                            houseCount: max(count, fallbackCount),
                            avgDayAge: avg,
                            houseRelatedAlertCount: result.alertsSummaryTotalActive
                        )
                        return (farmUUID, overview)
                    } catch {
                        let overview = FarmHomeOverview(
                            houseCount: fallbackCount,
                            avgDayAge: nil,
                            houseRelatedAlertCount: 0
                        )
                        return (farmUUID, overview)
                    }
                }
            }
            for await (fid, overview) in group {
                if let overview {
                    next[fid] = overview
                }
            }
        }
        farmHomeOverviewByFarmId = next
    }

    func refreshRotemDataForCurrentFarm(force: Bool = false) async {
        guard let rotemFarmID = farmRotemIDs[currentFarmId], !rotemFarmID.isEmpty else { return }
        if !force, let last = lastFarmScrapeAt[currentFarmId], Date().timeIntervalSince(last) < 45 {
            return
        }
        do {
            try await apiClient.triggerFarmScrape(rotemFarmID: rotemFarmID)
            lastFarmScrapeAt[currentFarmId] = Date()
        } catch {
            // Keep UI usable even when scrape trigger fails.
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

    private static func farmState(from houses: [House]) -> SensorState {
        if houses.contains(where: { $0.state == .critical }) { return .critical }
        if houses.contains(where: { $0.state == .warning }) { return .warning }
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

    private static func actualWeightCurve(from performance: [APIFlockPerformance], totalDays: Int) -> [Double] {
        if performance.isEmpty {
            return actualWeightCurve(forDay: max(0, totalDays / 2))
        }
        var points = Array(repeating: 0.0, count: max(totalDays, 1) + 1)
        for row in performance {
            guard let age = row.flockAgeDays, age >= 0, age < points.count else { continue }
            if let grams = row.averageWeightGrams {
                points[age] = grams / 1000
            }
        }
        // Fill missing gaps by carrying forward nearest known value.
        var lastKnown = 0.0
        for idx in points.indices {
            if points[idx] > 0 {
                lastKnown = points[idx]
            } else {
                points[idx] = lastKnown
            }
        }
        return points
    }

    private static func estimateDailyGain(from performance: [APIFlockPerformance], fallbackDay: Int, fallbackWeightKg: Double) -> Double {
        let rows = performance.compactMap { row -> (Int, Double)? in
            guard let day = row.flockAgeDays, let grams = row.averageWeightGrams else { return nil }
            return (day, grams)
        }.sorted(by: { $0.0 < $1.0 })
        guard rows.count >= 2 else {
            return max(0, fallbackWeightKg) * 1000 / Double(max(fallbackDay, 1))
        }
        let last = rows[rows.count - 1]
        let prev = rows[rows.count - 2]
        let dayDelta = max(last.0 - prev.0, 1)
        return max((last.1 - prev.1) / Double(dayDelta), 0)
    }

    private static func buildFlockLogs(from performance: [APIFlockPerformance]) -> [FlockLogEntry] {
        let rows = performance.compactMap { row -> FlockLogEntry? in
            guard let day = row.flockAgeDays else { return nil }
            return FlockLogEntry(
                id: UUID(),
                day: day,
                date: row.recordDate ?? Date(),
                deaths: 0,
                avgWeightKg: (row.averageWeightGrams ?? 0) / 1000,
                note: row.mortalityRate.map { "Mortality \($0.formatted(.number.precision(.fractionLength(2))))%" }
            )
        }
        return rows.sorted(by: { $0.day > $1.day }).prefix(10).map { $0 }
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

    private static func mapWorkerRole(_ value: String) -> UserRole {
        switch value.lowercased() {
        case "owner", "admin": return .owner
        case "manager", "supervisor": return .manager
        case "vet", "veterinarian": return .vet
        default: return .worker
        }
    }

    private func log(_ message: String) {
        guard verboseLogging else { return }
        print("[MockDataStore] \(message)")
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
