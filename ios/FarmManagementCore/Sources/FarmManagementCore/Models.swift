import Foundation

public struct AuthUser: Codable, Equatable {
    public let id: Int
    public let username: String
    public let email: String
    public let isStaff: Bool
    public let isAuthenticated: Bool?

    enum CodingKeys: String, CodingKey {
        case id
        case username
        case email
        case isStaff = "is_staff"
        case isAuthenticated = "is_authenticated"
    }
}

public struct LoginResponse: Codable, Equatable {
    public let message: String?
    public let token: String
    public let user: AuthUser
}

public struct FarmSummary: Codable, Identifiable, Equatable {
    public let id: Int
    /// Backend sends a UUID string or null; keep as String to avoid decode failures.
    public let organization: String?
    public let name: String
    public let location: String?
    public let description: String?
    public let isActive: Bool
    public let totalHouses: Int?
    public let activeHouses: Int?
    public let isIntegrated: Bool?

    enum CodingKeys: String, CodingKey {
        case id
        case organization
        case name
        case location
        case description
        case isActive = "is_active"
        case totalHouses = "total_houses"
        case activeHouses = "active_houses"
        case isIntegrated = "is_integrated"
    }
}

public struct HouseSummary: Codable, Identifiable, Equatable {
    public let id: Int
    public let houseNumber: Int
    public let isIntegrated: Bool?
    public let currentAgeDays: Int?
    public let ageDays: Int?
    public let status: String?
    public let batchStartDate: String?
    public let expectedHarvestDate: String?
    public let isActive: Bool?

    enum CodingKeys: String, CodingKey {
        case id
        case houseNumber = "house_number"
        case isIntegrated = "is_integrated"
        case currentAgeDays = "current_age_days"
        case ageDays = "age_days"
        case status
        case batchStartDate = "batch_start_date"
        case expectedHarvestDate = "expected_harvest_date"
        case isActive = "is_active"
    }
}

public struct FarmDetail: Codable, Identifiable, Equatable {
    public let id: Int
    public let organization: String?
    public let name: String
    public let location: String?
    public let description: String?
    public let contactPerson: String?
    public let contactPhone: String?
    public let contactEmail: String?
    public let isActive: Bool
    public let totalHouses: Int?
    public let activeHouses: Int?
    public let houses: [HouseSummary]

    enum CodingKeys: String, CodingKey {
        case id
        case organization
        case name
        case location
        case description
        case contactPerson = "contact_person"
        case contactPhone = "contact_phone"
        case contactEmail = "contact_email"
        case isActive = "is_active"
        case totalHouses = "total_houses"
        case activeHouses = "active_houses"
        case houses
    }
}

public struct HouseDetail: Codable, Identifiable, Equatable {
    public let id: Int
    public let houseNumber: Int
    public let currentDay: Int?
    public let currentAgeDays: Int?
    public let ageDays: Int?
    public let daysRemaining: Int?
    public let status: String?
    public let isActive: Bool
    public let isIntegrated: Bool
    public let batchStartDate: String?
    public let expectedHarvestDate: String?

    enum CodingKeys: String, CodingKey {
        case id
        case houseNumber = "house_number"
        case currentDay = "current_day"
        case currentAgeDays = "current_age_days"
        case ageDays = "age_days"
        case daysRemaining = "days_remaining"
        case status
        case isActive = "is_active"
        case isIntegrated = "is_integrated"
        case batchStartDate = "batch_start_date"
        case expectedHarvestDate = "expected_harvest_date"
    }
}

public struct UserInfoResponse: Codable, Equatable {
    public let user: AuthUser
}

public struct HouseDetailsResponse: Codable, Equatable {
    public let house: HouseDetail
    public let monitoring: HouseMonitoringSnapshot?
    public let alarms: [HouseAlarmSummary]
    public let stats: HouseStats?
}

public struct HouseMonitoringSnapshot: Codable, Equatable {
    public let id: Int
    public let timestamp: String?
    public let averageTemperature: Double?
    public let outsideTemperature: Double?
    public let humidity: Double?
    public let staticPressure: Double?
    public let targetTemperature: Double?
    public let ventilationLevel: Double?
    public let growthDay: Int?
    public let birdCount: Int?
    public let livability: Double?
    public let waterConsumption: Double?
    public let feedConsumption: Double?
    public let airflowPercentage: Double?
    public let sensorData: SnapshotSensorData?

    enum CodingKeys: String, CodingKey {
        case id
        case timestamp
        case averageTemperature = "average_temperature"
        case outsideTemperature = "outside_temperature"
        case humidity
        case staticPressure = "static_pressure"
        case targetTemperature = "target_temperature"
        case ventilationLevel = "ventilation_level"
        case growthDay = "growth_day"
        case birdCount = "bird_count"
        case livability
        case waterConsumption = "water_consumption"
        case feedConsumption = "feed_consumption"
        case airflowPercentage = "airflow_percentage"
        case sensorData = "sensor_data"
    }
}

public struct SnapshotSensorData: Codable, Equatable {
    public let wind: WindContext?
}

public struct WindContext: Codable, Equatable {
    public let windSpeed: Double?
    public let windDirection: Double?
    public let windChillTemperature: Double?

    enum CodingKeys: String, CodingKey {
        case windSpeed = "wind_speed"
        case windDirection = "wind_direction"
        case windChillTemperature = "wind_chill_temperature"
    }
}

public struct HouseAlarmSummary: Codable, Equatable, Identifiable {
    public let id: Int
    public let alarmType: String
    public let severity: String
    public let message: String
    public let timestamp: String?

    enum CodingKeys: String, CodingKey {
        case id
        case alarmType = "alarm_type"
        case severity
        case message
        case timestamp
    }
}

public struct HouseStats: Codable, Equatable {
    public let temperature: StatRange?
    public let humidity: StatRange?
    public let pressure: StatRange?
}

public struct StatRange: Codable, Equatable {
    public let avg: Double?
    public let max: Double?
    public let min: Double?
}

public struct HouseMonitoringKpisResponse: Codable, Equatable {
    public let houseID: Int
    public let windowHours: Int
    public let heaterRuntime: HeaterRuntime
    public let fanRuntime: FanRuntime
    public let waterDayOverDay: DeltaMetric
    public let feedDayOverDay: DeltaMetric
    public let waterFeedRatio: RatioMetric
    public let ventilationEffortIndex: Double?
    public let alarmBurden: AlarmBurden

    enum CodingKeys: String, CodingKey {
        case houseID = "house_id"
        case windowHours = "window_hours"
        case heaterRuntime = "heater_runtime"
        case fanRuntime = "fan_runtime"
        case waterDayOverDay = "water_day_over_day"
        case feedDayOverDay = "feed_day_over_day"
        case waterFeedRatio = "water_feed_ratio"
        case ventilationEffortIndex = "ventilation_effort_index"
        case alarmBurden = "alarm_burden"
    }
}

public struct HeaterRuntime: Codable, Equatable {
    public let hours24h: Double?
    public let cycles24h: Int?

    enum CodingKeys: String, CodingKey {
        case hours24h = "hours_24h"
        case cycles24h = "cycles_24h"
    }
}

public struct FanRuntime: Codable, Equatable {
    public let hours24h: Double?

    enum CodingKeys: String, CodingKey {
        case hours24h = "hours_24h"
    }
}

public struct DeltaMetric: Codable, Equatable {
    public let current: Double?
    public let previous: Double?
    public let delta: Double?
    public let deltaPct: Double?

    enum CodingKeys: String, CodingKey {
        case current
        case previous
        case delta
        case deltaPct = "delta_pct"
    }
}

public struct RatioMetric: Codable, Equatable {
    public let today: Double?
    public let yesterday: Double?
    public let deltaPct: Double?

    enum CodingKeys: String, CodingKey {
        case today
        case yesterday
        case deltaPct = "delta_pct"
    }
}

public struct AlarmBurden: Codable, Equatable {
    public let total24h: Int
    public let critical24h: Int
    public let high24h: Int
    public let medium24h: Int
    public let low24h: Int
    public let activeNow: Int

    enum CodingKeys: String, CodingKey {
        case total24h = "total_24h"
        case critical24h = "critical_24h"
        case high24h = "high_24h"
        case medium24h = "medium_24h"
        case low24h = "low_24h"
        case activeNow = "active_now"
    }
}

public struct WaterHistoryResponse: Codable, Equatable {
    public let waterHistory: [WaterHistoryEntry]

    enum CodingKeys: String, CodingKey {
        case waterHistory = "water_history"
    }
}

public struct WaterHistoryEntry: Codable, Equatable, Identifiable {
    public var id: String { date ?? UUID().uuidString }
    public let date: String?
    public let growthDay: Int?
    public let dailyWater1: Double?
    public let dailyWater2: Double?
    public let dailyWater3: Double?
    public let dailyWater4: Double?
    public let cooling: Double?
    public let fogger: Double?

    enum CodingKeys: String, CodingKey {
        case date
        case growthDay = "growth_day"
        case dailyWater1 = "daily_water_1"
        case dailyWater2 = "daily_water_2"
        case dailyWater3 = "daily_water_3"
        case dailyWater4 = "daily_water_4"
        case cooling
        case fogger
    }
}

public struct FarmMonitoringResponse: Codable, Equatable {
    public let farmID: Int
    public let farmName: String
    public let housesCount: Int
    public let houses: [FarmMonitoringHouse]

    enum CodingKeys: String, CodingKey {
        case farmID = "farm_id"
        case farmName = "farm_name"
        case housesCount = "houses_count"
        case houses
    }
}

public struct FarmMonitoringHouse: Codable, Identifiable, Equatable {
    public var id: Int { houseID ?? fallbackID ?? -1 }
    public let houseID: Int?
    public let fallbackID: Int?
    public let houseNumber: Int
    public let timestamp: String?
    public let averageTemperature: Double?
    public let humidity: Double?
    public let staticPressure: Double?
    public let growthDay: Int?
    public let alarmStatus: String?
    public let connectionStatus: Int?
    public let hasAlarms: Bool?
    public let isConnected: Bool?
    public let status: String?
    public let message: String?

    enum CodingKeys: String, CodingKey {
        case houseID = "house_id"
        case fallbackID = "id"
        case houseNumber = "house_number"
        case timestamp
        case averageTemperature = "average_temperature"
        case humidity
        case staticPressure = "static_pressure"
        case growthDay = "growth_day"
        case alarmStatus = "alarm_status"
        case connectionStatus = "connection_status"
        case hasAlarms = "has_alarms"
        case isConnected = "is_connected"
        case status
        case message
    }
}

public struct FarmMonitoringDashboardResponse: Codable, Equatable {
    public let farmID: Int
    public let farmName: String
    public let totalHouses: Int
    public let houses: [FarmMonitoringDashboardHouse]
    public let alertsSummary: AlertsSummary
    public let connectionSummary: ConnectionSummary

    enum CodingKeys: String, CodingKey {
        case farmID = "farm_id"
        case farmName = "farm_name"
        case totalHouses = "total_houses"
        case houses
        case alertsSummary = "alerts_summary"
        case connectionSummary = "connection_summary"
    }
}

public struct FarmMonitoringDashboardHouse: Codable, Identifiable, Equatable {
    public let id: Int
    public let houseNumber: Int
    public let currentDay: Int?
    public let status: String?
    public let timestamp: String?
    public let averageTemperature: Double?
    public let humidity: Double?
    public let staticPressure: Double?
    public let growthDay: Int?
    public let alarmStatus: String?
    public let isConnected: Bool?
    public let activeAlarmsCount: Int?

    enum CodingKeys: String, CodingKey {
        case id = "house_id"
        case houseNumber = "house_number"
        case currentDay = "current_day"
        case status
        case timestamp
        case averageTemperature = "average_temperature"
        case humidity
        case staticPressure = "static_pressure"
        case growthDay = "growth_day"
        case alarmStatus = "alarm_status"
        case isConnected = "is_connected"
        case activeAlarmsCount = "active_alarms_count"
    }
}

public struct AlertsSummary: Codable, Equatable {
    public let totalActive: Int
    public let critical: Int
    public let warning: Int
    public let normal: Int

    enum CodingKeys: String, CodingKey {
        case totalActive = "total_active"
        case critical
        case warning
        case normal
    }
}

public struct ConnectionSummary: Codable, Equatable {
    public let connected: Int
    public let disconnected: Int
}

public struct HouseComparisonResponse: Codable, Equatable {
    public let count: Int
    public let houses: [HouseComparisonItem]
}

public struct HouseComparisonItem: Codable, Identifiable, Equatable {
    public let id: Int
    public let houseNumber: Int
    public let farmID: Int
    public let farmName: String
    public let currentDay: Int?
    public let ageDays: Int?
    public let status: String
    public let isFullHouse: Bool
    public let lastUpdateTime: String?
    public let averageTemperature: Double?
    public let outsideTemperature: Double?
    public let targetTemperature: Double?
    public let staticPressure: Double?
    public let insideHumidity: Double?
    public let airflowPercentage: Double?
    public let waterConsumption: Double?
    public let feedConsumption: Double?
    public let waterPerBird: Double?
    public let feedPerBird: Double?
    public let waterFeedRatio: Double?
    public let birdCount: Int?
    public let livability: Double?
    public let growthDay: Int?
    public let isConnected: Bool
    public let hasAlarms: Bool
    public let alarmStatus: String
    public let activeAlarmsCount: Int?
    public let dataFreshnessMinutes: Int?
    public let heaterOn: Bool?
    public let fanOn: Bool?
    public let windSpeed: Double?
    public let windDirection: Double?
    public let windChillTemperature: Double?

    enum CodingKeys: String, CodingKey {
        case id = "house_id"
        case houseNumber = "house_number"
        case farmID = "farm_id"
        case farmName = "farm_name"
        case currentDay = "current_day"
        case ageDays = "age_days"
        case status
        case isFullHouse = "is_full_house"
        case lastUpdateTime = "last_update_time"
        case averageTemperature = "average_temperature"
        case outsideTemperature = "outside_temperature"
        case targetTemperature = "target_temperature"
        case staticPressure = "static_pressure"
        case insideHumidity = "inside_humidity"
        case airflowPercentage = "airflow_percentage"
        case waterConsumption = "water_consumption"
        case feedConsumption = "feed_consumption"
        case waterPerBird = "water_per_bird"
        case feedPerBird = "feed_per_bird"
        case waterFeedRatio = "water_feed_ratio"
        case birdCount = "bird_count"
        case livability
        case growthDay = "growth_day"
        case isConnected = "is_connected"
        case hasAlarms = "has_alarms"
        case alarmStatus = "alarm_status"
        case activeAlarmsCount = "active_alarms_count"
        case dataFreshnessMinutes = "data_freshness_minutes"
        case heaterOn = "heater_on"
        case fanOn = "fan_on"
        case windSpeed = "wind_speed"
        case windDirection = "wind_direction"
        case windChillTemperature = "wind_chill_temperature"
    }
}
