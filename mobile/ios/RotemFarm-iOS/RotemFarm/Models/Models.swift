//
//  Models.swift
//  RotemFarm — Domain model types.
//
//  All models are value types (`struct`) and `Identifiable` so SwiftUI
//  diffing stays cheap. When the real API lands, keep these as DTOs and
//  just drop a decoder in Services/APIClient.
//

import Foundation
import SwiftUI

// MARK: - User / role ---------------------------------------------------------

enum UserRole: String, Codable, CaseIterable {
    case owner, manager, worker, vet

    var displayName: String {
        switch self {
        case .owner:   "Owner"
        case .manager: "Manager"
        case .worker:  "Worker"
        case .vet:     "Vet"
        }
    }

    var tint: Color {
        switch self {
        case .owner:   .farmGreen
        case .manager: .stateInfo
        case .worker:  Color(red: 166 / 255, green: 90 / 255, blue: 40 / 255)
        case .vet:     .aiEnd
        }
    }

    var canWriteSetpoints: Bool {
        self == .owner || self == .manager
    }
}

struct AppUser: Identifiable, Codable, Hashable {
    let id: UUID
    var backendId: Int?
    var name: String
    var email: String
    var initials: String
    var role: UserRole
    var assignedHouseIds: [UUID]   // empty = all houses in user's farms
}

// MARK: - Farm / House / Flock ------------------------------------------------

struct Farm: Identifiable, Hashable {
    let id: UUID
    var backendId: Int?
    var name: String
    var houseIds: [UUID]
    var totalBirds: Int
    var flockAgeDays: Int
    var worstState: SensorState
    var alertSummary: String   // e.g. "2 alerts" · "1 critical"
    /// From list API (`active_houses`); used before per-farm house load completes.
    var activeHousesFromApi: Int
}

/// Aggregates for home “all farms” list (from monitoring dashboard).
struct FarmHomeOverview: Hashable, Sendable {
    var houseCount: Int
    var avgDayAge: Int?
    /// Sum of per-house active alarms from dashboard (house-related).
    var houseRelatedAlertCount: Int
}

enum HouseType: String, Codable, CaseIterable {
    case tunnel  = "Tunnel"
    case curtain = "Curtain"
    case brood   = "Brood"
}

struct House: Identifiable, Hashable {
    let id: UUID
    var backendId: Int?
    var farmId: UUID
    var name: String
    var type: HouseType
    var birdCount: Int
    var flockDay: Int
    var state: SensorState
    var pillText: String            // "All OK" / "High RH" / "Static P" …
    var snapshot: HouseSnapshot
}

struct HouseSnapshot: Hashable {
    var tempC: Double
    var humidity: Double
    var co2Ppm: Double
    var ammoniaPpm: Double
    var staticPressurePa: Double
    var airflowPct: Double
    var waterLphr: Double
    var feedCyclesDone: Int
    var feedCyclesPlanned: Int
    /// For progress bars: fraction of alarm threshold consumed, clamped [0,1]
    var tempFill: Double
    var humidityFill: Double
    var co2Fill: Double
    var ammoniaFill: Double
    var staticFill: Double
    var airflowFill: Double
}

struct Flock: Identifiable, Hashable {
    let id: UUID
    var farmId: UUID
    var name: String            // "Flock 24-A"
    var breed: String           // "Cobb 500"
    var placedOn: Date
    var targetCatchOn: Date
    var currentDay: Int
    var totalDays: Int
    var birdsPlaced: Int
    var birdsRemaining: Int
    var avgWeightKg: Double
    var targetWeightKg: Double
    var fcr: Double
    var targetFcr: Double
    var livabilityPct: Double
    var dailyGainG: Double
    var waterFeedRatio: Double
    var epef: Int
    var state: SensorState
    var statePillText: String
    var isActive: Bool
    /// Per-day [0...42] actual weight (kg) for the growth curve
    var actualWeightCurve: [Double]
    var targetWeightCurve: [Double]
    /// Recent daily log entries
    var log: [FlockLogEntry]
}

struct FlockLogEntry: Identifiable, Hashable {
    let id: UUID
    var day: Int
    var date: Date
    var deaths: Int
    var avgWeightKg: Double
    var note: String?
}

// MARK: - Sensor history -------------------------------------------------------

struct SensorSample: Identifiable, Hashable {
    let id: UUID
    var timestamp: Date
    var value: Double
    /// Per-probe label for the "Sensors" list in the detail view
    var probeName: String?
}

enum SensorKind: String, CaseIterable, Codable {
    case temperature, humidity, co2, ammonia, staticPressure, airflow

    var title: String {
        switch self {
        case .temperature:    "Temperature"
        case .humidity:       "Humidity"
        case .co2:            "CO₂"
        case .ammonia:        "NH₃ Ammonia"
        case .staticPressure: "Static Pressure"
        case .airflow:        "Airflow"
        }
    }

    var unit: String {
        switch self {
        case .temperature:    "°C"
        case .humidity:       "%"
        case .co2:            "k ppm"
        case .ammonia:        "ppm"
        case .staticPressure: "Pa"
        case .airflow:        "%"
        }
    }

    var systemImage: String {
        switch self {
        case .temperature:    "thermometer.medium"
        case .humidity:       "drop.fill"
        case .co2:            "cloud.fog.fill"
        case .ammonia:        "wind"
        case .staticPressure: "gauge.medium"
        case .airflow:        "fan.fill"
        }
    }

    var targetBand: (low: Double, high: Double)? {
        switch self {
        case .temperature:    (26.5, 28.0)
        case .humidity:       (60, 65)
        case .co2:            (0, 3.0)
        case .ammonia:        (0, 20)
        case .staticPressure: (10, 35)
        case .airflow:        (40, 80)
        }
    }
}

// MARK: - Resource history (water / feed / heater) ----------------------------

struct DailyResourcePoint: Identifiable, Hashable {
    let id = UUID()
    var day: Int        // flock day for x-axis
    var date: Date
    var value: Double
    var target: Double?
    var isAnomaly: Bool = false
}

struct HourlyPoint: Identifiable, Hashable {
    let id = UUID()
    var hour: Int
    var value: Double
}

struct SiloLevel: Identifiable, Hashable {
    let id = UUID()
    var name: String
    var rationCode: String
    var tonsRemaining: Double
    var pctFull: Double
    var daysRemaining: Double
}

struct HeaterStatus: Identifiable, Hashable {
    let id = UUID()
    var name: String
    var isOn: Bool
    var runtimeTodayMinutes: Int
    var state: SensorState
}

struct CompareSeries: Identifiable, Hashable {
    let id = UUID()
    var houseName: String
    var color: Color
    var points: [DailyResourcePoint]
    var todayDelta: String   // "+18%" / "0%" / "−2%"
    var todayDeltaState: SensorState
}

// MARK: - Alarms ---------------------------------------------------------------

enum AlertSeverity: String, Codable, CaseIterable {
    case critical, warning, info, acknowledged

    var label: String {
        switch self {
        case .critical:      "Critical"
        case .warning:       "Warning"
        case .info:          "Info"
        case .acknowledged:  "Acknowledged"
        }
    }

    var state: SensorState {
        switch self {
        case .critical:      .critical
        case .warning:       .warning
        case .info, .acknowledged: .ok
        }
    }

    var systemImage: String {
        switch self {
        case .critical:      "exclamationmark.triangle.fill"
        case .warning:       "exclamationmark.circle.fill"
        case .info:          "info.circle.fill"
        case .acknowledged:  "checkmark.circle.fill"
        }
    }
}

struct Alarm: Identifiable, Hashable {
    let id: UUID
    var backendId: Int?
    var severity: AlertSeverity
    var title: String
    var meta: String                 // "House 4 · 6 min ago · over threshold"
    var houseName: String
    var occurredAt: Date
    var sparkline: [Double]          // last ~20 samples
    var threshold: Double?
    var peakValue: Double?
    var recommendation: AIRecommendation?
    var isAcknowledged: Bool
}

struct AIRecommendation: Hashable {
    var title: String
    var body: String
    var confidence: Double  // 0...1
    var primaryAction: String
    var secondaryAction: String
}

// MARK: - AI tips --------------------------------------------------------------

enum TipCategory: String, CaseIterable {
    case air, heat, feed, biosecurity

    var title: String {
        switch self {
        case .air:          "Air Quality"
        case .heat:         "Heat plan"
        case .feed:         "Feed schedule"
        case .biosecurity:  "Biosecurity"
        }
    }

    var tint: Color {
        switch self {
        case .air:          .aiEnd
        case .heat:         .stateWarning
        case .feed:         .farmGreen
        case .biosecurity:  .stateInfo
        }
    }
}

struct AITip: Identifiable, Hashable {
    let id: UUID
    var category: TipCategory
    var scope: String        // "House 3" or "Farm-wide"
    var severity: SensorState
    var title: String
    var body: String
    var primaryAction: String
    var secondaryAction: String
    var confidence: Double
    var createdAt: Date
}

// MARK: - Team -----------------------------------------------------------------

struct TeamMember: Identifiable, Hashable {
    let id: UUID
    var name: String
    var initials: String
    var role: UserRole
    var scope: String       // "all houses" / "House 1–3"
    var isYou: Bool
}

// MARK: - Controller pairing ---------------------------------------------------

struct PairedController: Identifiable, Hashable {
    let id: UUID
    var model: String       // "Platinum Touch" / "Trio" / "Plus"
    var serial: String
    var houseName: String
    var lastSeen: Date
    var state: SensorState
}
