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
    private var isReloadingSelectedFarmData = false
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
        // Temperature history is now parity-driven from Rotem CommandID 35.
        // Avoid synthetic fallback so UI reflects true backend availability.
        if kind == .temperature {
            return []
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
        if isReloadingSelectedFarmData {
            diagnostic("reloadSelectedFarmData skipped because another reload is already running")
            return
        }
        guard let selectedFarm = farms.first(where: { $0.id == currentFarmId }),
              let selectedFarmBackendID = selectedFarm.backendId else {
            houses = []
            flocks = []
            alarms = []
            return
        }
        isReloadingSelectedFarmData = true
        isLoading = true
        // Prevent stale water/heater values during farm reload.
        houseWaterRealtimeByHouseId = [:]
        houseHeaterRealtimeByHouseId = [:]
        houseRealtimeLoadedIds = []
        monitoringFreshnessByFarmId = [:]
        houseHeaterHoursForListByHouseId = [:]
        defer {
            isLoading = false
            isReloadingSelectedFarmData = false
        }
        do {
            log("reloadSelectedFarmData() farmBackendID=\(selectedFarmBackendID)")
            let client = apiClient
            let apiHouses = try await apiClient.fetchHouses(farmID: selectedFarmBackendID)
            diagnostic("reloadSelectedFarmData fetched apiHouses=\(apiHouses.count) ids=\(apiHouses.map { $0.id }) active=\(apiHouses.filter(\.isActive).count)")
            let dashboard = try? await apiClient.fetchFarmMonitoringDashboard(farmID: selectedFarmBackendID)
            if let dashboard {
                diagnostic("reloadSelectedFarmData overview endpoint houses=\(dashboard.houses.count) alerts=\(dashboard.alertsSummaryTotalActive) fresh=\(String(describing: dashboard.freshness))")
            } else {
                diagnostic("reloadSelectedFarmData overview endpoint FAILED/nil")
            }
            let dashboardByID = Dictionary(
                uniqueKeysWithValues: (dashboard?.houses ?? []).map { ($0.houseID, $0) }
            )
            let activeHouses = apiHouses.filter(\.isActive)
            let snapshotHouses = houses
            var mappedHouses: [House] = []
            var mappedAlarms: [Alarm] = []
            for apiHouse in activeHouses {
                let houseID = Self.stableUUID(prefix: "house", intID: apiHouse.id)
                let fallbackSnapshot = snapshotHouses.first(where: { $0.backendId == apiHouse.id })?.snapshot
                let dashboardData = dashboardByID[apiHouse.id]
                let dashboardHasOnlyZeroes = dashboardData.map(Self.monitoringCardIsAllZeroOrMissing) ?? false
                let usableDashboardData = dashboardHasOnlyZeroes ? nil : dashboardData
                if dashboardHasOnlyZeroes {
                    diagnostic("overview endpoint rejected all-zero house backendID=\(apiHouse.id) number=\(apiHouse.houseNumber)")
                }
                let resolvedTemp = usableDashboardData?.averageTemperature ?? fallbackSnapshot?.tempC ?? .nan
                let resolvedHumidity = usableDashboardData?.humidity ?? fallbackSnapshot?.humidity ?? .nan
                let resolvedStatic = usableDashboardData?.staticPressure ?? fallbackSnapshot?.staticPressurePa ?? .nan
                let resolvedAirflow = usableDashboardData?.airflowPercentage ?? fallbackSnapshot?.airflowPct ?? .nan
                let resolvedWater = usableDashboardData?.waterConsumption ?? fallbackSnapshot?.waterLphr ?? .nan
                let resolvedFeed = usableDashboardData?.feedConsumption ?? fallbackSnapshot?.feedLbs ?? .nan
                let snapshot = HouseSnapshot(
                    tempC: resolvedTemp,
                    humidity: resolvedHumidity,
                    co2Ppm: fallbackSnapshot?.co2Ppm ?? 0,
                    ammoniaPpm: fallbackSnapshot?.ammoniaPpm ?? 0,
                    staticPressurePa: resolvedStatic,
                    airflowPct: resolvedAirflow,
                    waterLphr: resolvedWater,
                    feedLbs: resolvedFeed,
                    feedCyclesDone: fallbackSnapshot?.feedCyclesDone ?? 0,
                    feedCyclesPlanned: fallbackSnapshot?.feedCyclesPlanned ?? 0,
                    tempFill: Self.clamp01(resolvedTemp / 35),
                    humidityFill: Self.clamp01(resolvedHumidity / 100),
                    co2Fill: fallbackSnapshot?.co2Fill ?? 0,
                    ammoniaFill: fallbackSnapshot?.ammoniaFill ?? 0,
                    staticFill: Self.clamp01(resolvedStatic / 60),
                    airflowFill: Self.clamp01(resolvedAirflow / 100)
                )
                diagnostic("map house backendID=\(apiHouse.id) number=\(apiHouse.houseNumber) source=\(usableDashboardData == nil ? "local/empty" : "overviewEndpoint") temp=\(resolvedTemp) humidity=\(resolvedHumidity) pressure=\(resolvedStatic) airflow=\(resolvedAirflow) water=\(resolvedWater) feed=\(resolvedFeed) state=\(Self.stateForSnapshot(snapshot).rawValue)")
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
            }

            houses = mappedHouses
            diagnostic("reloadSelectedFarmData mappedHouses=\(mappedHouses.count) nanSnapshots=\(mappedHouses.filter { $0.snapshot.tempC.isNaN || $0.snapshot.humidity.isNaN || $0.snapshot.staticPressurePa.isNaN || $0.snapshot.airflowPct.isNaN }.count)")
            // Current overview comes from the farm dashboard endpoint; history is loaded by detail screens.
            houseWaterRealtimeByHouseId = Dictionary(
                uniqueKeysWithValues: mappedHouses.compactMap { house in
                    guard house.snapshot.waterLphr.isFinite else { return nil }
                    return (house.id, house.snapshot.waterLphr)
                }
            )
            houseKpisByHouseId = [:]
            houseHeaterRealtimeByHouseId = [:]
            houseRealtimeLoadedIds = Set(mappedHouses.map(\.id))
            diagnostic("reloadSelectedFarmData overview loaded waterRealtime=\(houseWaterRealtimeByHouseId.count) realtimeLoaded=\(houseRealtimeLoadedIds.count)")
            alarms = mappedAlarms.sorted { $0.occurredAt > $1.occurredAt }
            if let idx = farms.firstIndex(where: { $0.id == currentFarmId }) {
                farms[idx].houseIds = houses.map(\.id)
                farms[idx].alertSummary = alarms.isEmpty ? "No alerts" : "\(alarms.count) alerts"
                farms[idx].worstState = Self.farmState(from: houses)
            }
            do {
                let apiFlocks = try await apiClient.fetchFlocks(farmID: selectedFarmBackendID)
                let flockList = Array(apiFlocks)
                let perfBatchSize = 4
                var indexedFlocks: [(Int, Flock)] = []
                var fStart = 0
                while fStart < flockList.count {
                    let fEnd = min(fStart + perfBatchSize, flockList.count)
                    let batch = Array(flockList[fStart..<fEnd])
                    await withTaskGroup(of: (Int, Flock).self) { group in
                        for (offset, apiFlock) in batch.enumerated() {
                            let globalIndex = fStart + offset
                            group.addTask { @MainActor in
                                let metrics = Self.metricsFromStatus(apiFlock.status)
                                let totalDays = Self.totalDays(arrival: apiFlock.arrivalDate, expectedHarvest: apiFlock.expectedHarvestDate)
                                let currentDay = max(0, apiFlock.currentAgeDays)
                                let mortalityRate = apiFlock.mortalityRate ?? 0
                                let livability = max(0, 100 - mortalityRate)
                                let performance = (try? await client.fetchFlockPerformance(flockID: apiFlock.id)) ?? []
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
                                let flock = Flock(
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
                                return (globalIndex, flock)
                            }
                        }
                        for await pair in group {
                            indexedFlocks.append(pair)
                        }
                    }
                    fStart = fEnd
                }
                indexedFlocks.sort { $0.0 < $1.0 }
                flocks = indexedFlocks.map { $0.1 }.sorted { $0.placedOn > $1.placedOn }
            } catch {
                flocks = []
            }
            // Load task center, program library, and workers from live APIs.
            var loadedTasks: [FarmTask] = []
            let taskFetchBatchSize = 6
            let housesForTasks = mappedHouses
            var taskBatchStart = 0
            while taskBatchStart < housesForTasks.count {
                let taskBatchEnd = min(taskBatchStart + taskFetchBatchSize, housesForTasks.count)
                let taskBatch = Array(housesForTasks[taskBatchStart..<taskBatchEnd])
                await withTaskGroup(of: [FarmTask].self) { group in
                    for house in taskBatch {
                        group.addTask { @MainActor in
                            guard let houseBackendID = house.backendId else { return [] }
                            let apiTasks = (try? await client.fetchTasks(houseID: houseBackendID)) ?? []
                            return apiTasks.map { task in
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
                            }
                        }
                    }
                    for await chunk in group {
                        loadedTasks.append(contentsOf: chunk)
                    }
                }
                taskBatchStart = taskBatchEnd
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
            diagnostic("reloadSelectedFarmData success waterRealtime=\(houseWaterRealtimeByHouseId.count) heaterRealtime=\(houseHeaterRealtimeByHouseId.count) realtimeLoaded=\(houseRealtimeLoadedIds.count)")
        } catch {
            lastError = error.localizedDescription
            log("reloadSelectedFarmData() failed error=\(error.localizedDescription)")
            diagnostic("reloadSelectedFarmData top-level FAILED error=\(error.localizedDescription)")
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
            let mapped: [SensorSample]
            if kind == .temperature {
                let history = try await apiClient.fetchRotemTemperatureHistory(houseID: backendID)
                mapped = history.compactMap { point in
                    let date = point.date ?? Date()
                    let value = point.avgValue ?? point.maxValue ?? point.minValue
                    guard let value else { return nil }
                    return SensorSample(id: UUID(), timestamp: date, value: value, probeName: nil)
                }
            } else {
                let history = try await apiClient.fetchHouseMonitoringHistory(houseID: backendID, limit: max(points, 24))
                mapped = history.compactMap { point in
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

    func fetchFeedHistory(houseId: UUID, days: Int = 5) async -> [DailyResourcePoint] {
        guard let backendID = houses.first(where: { $0.id == houseId })?.backendId else { return [] }
        do {
            let rows = try await apiClient.fetchRotemFeedHistory(houseID: backendID, days: days)
            return rows.map { row in
                DailyResourcePoint(
                    day: row.growthDay,
                    date: row.date ?? Date(),
                    value: row.dailyFeedTotal,
                    target: nil,
                    isAnomaly: false
                )
            }.sorted(by: { $0.date < $1.date })
        } catch {
            lastError = error.localizedDescription
            return []
        }
    }

    func fetchWaterHistory(houseId: UUID, days: Int = 5) async -> [DailyResourcePoint] {
        guard let backendID = houses.first(where: { $0.id == houseId })?.backendId else { return [] }
        do {
            let rows = try await apiClient.fetchRotemWaterHistory(houseID: backendID, days: days)
            return rows.enumerated().map { index, row in
                DailyResourcePoint(
                    day: row.growthDay ?? (index + 1),
                    date: row.date ?? Date(),
                    value: row.consumptionAvg,
                    target: nil,
                    isAnomaly: false
                )
            }.sorted(by: { $0.date < $1.date })
        } catch {
            lastError = error.localizedDescription
            return []
        }
    }

    func fetchHeaterHistory(houseId: UUID, days: Int = 5) async -> [DailyResourcePoint] {
        guard let backendID = houses.first(where: { $0.id == houseId })?.backendId else { return [] }
        do {
            return try await apiClient.fetchHouseHeaterHistory(houseID: backendID, days: days)
        } catch {
            if let urlError = error as? URLError, urlError.code == .timedOut {
                lastError = "Heater history request timed out. Please try again."
            } else {
                lastError = error.localizedDescription
            }
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
        let farmUUID = farms.first(where: { $0.backendId == farmBackendID })?.id
        let sourceHouses = houses.filter { house in
            guard let farmUUID else { return false }
            return house.farmId == farmUUID
        }
        var cards: [APIFarmHouseMonitoringCard] = []
        for house in sourceHouses {
            guard let backendID = house.backendId,
                  let number = Int(house.name.replacingOccurrences(of: "House ", with: "")) else {
                continue
            }
            cards.append(APIFarmHouseMonitoringCard(
                houseID: backendID,
                houseNumber: number,
                averageTemperature: house.snapshot.tempC.isFinite ? house.snapshot.tempC : nil,
                humidity: house.snapshot.humidity.isFinite ? house.snapshot.humidity : nil,
                staticPressure: house.snapshot.staticPressurePa.isFinite ? house.snapshot.staticPressurePa : nil,
                airflowPercentage: house.snapshot.airflowPct.isFinite ? house.snapshot.airflowPct : nil,
                waterConsumption: houseWaterRealtimeByHouseId[house.id] ?? (house.snapshot.waterLphr.isFinite ? house.snapshot.waterLphr : nil),
                feedConsumption: house.snapshot.feedLbs.isFinite ? house.snapshot.feedLbs : nil,
                growthDay: house.flockDay,
                houseCurrentDay: house.flockDay,
                activeAlarmsCount: 0
            ))
        }
        return cards
    }

    func refreshMonitoringNowForCurrentFarm() async {
        await reloadSelectedFarmData()
        await refreshFarmHomeOverviews()
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
        var next: [UUID: FarmHomeOverview] = [:]
        for farm in farms {
            let farmHouses = houses.filter { $0.farmId == farm.id }
            let days = farmHouses.map(\.flockDay)
            let avg: Int? = days.isEmpty ? nil : days.reduce(0, +) / days.count
            let alertCount = alarms.filter { alarm in
                farmHouses.contains(where: { $0.name == alarm.houseName })
            }.count
            next[farm.id] = FarmHomeOverview(
                houseCount: max(farmHouses.count, farm.activeHousesFromApi),
                avgDayAge: avg,
                houseRelatedAlertCount: alertCount
            )
        }
        farmHomeOverviewByFarmId = next
    }

    func refreshRotemDataForCurrentFarm(force: Bool = false) async {
        if !force, let last = lastFarmScrapeAt[currentFarmId], Date().timeIntervalSince(last) < 45 {
            return
        }
        await reloadSelectedFarmData()
        lastFarmScrapeAt[currentFarmId] = Date()
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
        if snapshot.tempC.isNaN || snapshot.humidity.isNaN || snapshot.staticPressurePa.isNaN || snapshot.airflowPct.isNaN {
            return .warning
        }
        if snapshot.staticPressurePa > 35 || snapshot.humidity > 75 {
            return .critical
        }
        if snapshot.humidity > 65 || snapshot.tempC > 30 {
            return .warning
        }
        return .ok
    }

    /// Merges Rotem live `monitoring/latest` payload fields into the house snapshot (CO₂/NH₃ unchanged — not in API yet).
    private static func applyLatestMonitoring(_ live: APIMonitoring, to snapshot: inout HouseSnapshot) {
        if let v = live.averageTemperature { snapshot.tempC = v }
        if let v = live.humidity { snapshot.humidity = v }
        if let v = live.staticPressure { snapshot.staticPressurePa = v }
        if let v = live.airflowPercentage { snapshot.airflowPct = v }
        if let v = live.waterConsumption { snapshot.waterLphr = v }
        if let v = live.feedConsumption { snapshot.feedLbs = v }
        snapshot.tempFill = clamp01((snapshot.tempC.isNaN ? 0 : snapshot.tempC) / 35)
        snapshot.humidityFill = clamp01((snapshot.humidity.isNaN ? 0 : snapshot.humidity) / 100)
        snapshot.staticFill = clamp01((snapshot.staticPressurePa.isNaN ? 0 : snapshot.staticPressurePa) / 60)
        snapshot.airflowFill = clamp01((snapshot.airflowPct.isNaN ? 0 : snapshot.airflowPct) / 100)
    }

    private static func monitoringIsAllZeroOrMissing(_ live: APIMonitoring) -> Bool {
        [
            live.averageTemperature,
            live.humidity,
            live.staticPressure,
            live.airflowPercentage,
            live.waterConsumption,
            live.feedConsumption
        ].allSatisfy { value in
            guard let value else { return true }
            return value == 0
        }
    }

    private static func monitoringCardIsAllZeroOrMissing(_ card: APIFarmHouseMonitoringCard) -> Bool {
        [
            card.averageTemperature,
            card.humidity,
            card.staticPressure,
            card.airflowPercentage,
            card.waterConsumption,
            card.feedConsumption
        ].allSatisfy { value in
            guard let value else { return true }
            return value == 0
        }
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
        print("[FarmDataStore] \(message)")
    }

    private func diagnostic(_ message: String) {
        print("[FarmDataStore][diagnostic] \(message)")
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
