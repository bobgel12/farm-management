import Foundation

enum TaskStatus: String, CaseIterable, Codable {
    case pending, inProgress, done, blocked

    var label: String {
        switch self {
        case .pending: "Pending"
        case .inProgress: "In progress"
        case .done: "Done"
        case .blocked: "Blocked"
        }
    }
}

struct FarmTask: Identifiable, Hashable {
    let id: UUID
    var backendId: Int?
    var title: String
    var houseId: UUID?
    var assigneeName: String
    var dueAt: Date
    var status: TaskStatus
    var notes: String
}

struct Program: Identifiable, Hashable {
    let id: UUID
    var backendId: Int?
    var name: String
    var category: String
    var isActive: Bool
    var assignedHouseIds: [UUID]
    var updatedAt: Date
}

struct WorkerProfile: Identifiable, Hashable {
    let id: UUID
    var backendId: Int?
    var name: String
    var role: UserRole
    var phone: String
    var farmName: String
    var assignedHouseIds: [UUID]
}

struct Organization: Identifiable, Hashable {
    let id: UUID
    var name: String
    var memberCount: Int
    var farmsCount: Int
    var active: Bool
}

struct OrganizationMember: Identifiable, Hashable {
    let id: UUID
    var orgId: UUID
    var name: String
    var email: String
    var role: UserRole
}

struct BIKPI: Identifiable, Hashable {
    let id = UUID()
    var label: String
    var value: String
    var delta: String
}

struct ReportItem: Identifiable, Hashable {
    let id: UUID
    var title: String
    var generatedAt: Date
    var scope: String
}

struct RotemFarmHealth: Identifiable, Hashable {
    let id: UUID
    var farmName: String
    var devicesOnline: Int
    var devicesTotal: Int
    var criticalCount: Int
    var warningCount: Int
}

