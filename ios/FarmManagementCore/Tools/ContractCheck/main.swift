import Foundation
import FarmManagementCore

let decoder = JSONDecoder()
let bundle = Bundle.module

func loadFixture(_ name: String) throws -> Data {
    guard let url = bundle.url(forResource: name, withExtension: "json") else {
        throw APIError.decoding("Missing fixture \(name)")
    }
    return try Data(contentsOf: url)
}

func runChecks() throws {
    let farmsPaginatedData = try loadFixture("farms_paginated")
    let farmsPaginated = try decoder.decode(FlexibleListResponse<FarmSummary>.self, from: farmsPaginatedData)
    guard farmsPaginated.values.count == 2 else {
        throw APIError.decoding("Expected 2 farms in paginated fixture")
    }

    let farmsArrayData = try loadFixture("farms_array")
    let farmsArray = try decoder.decode(FlexibleListResponse<FarmSummary>.self, from: farmsArrayData)
    guard farmsArray.values.first?.id == 30 else {
        throw APIError.decoding("Expected farm id 30 in array fixture")
    }

    let loginData = try loadFixture("login_response")
    let login = try decoder.decode(LoginResponse.self, from: loginData)
    guard login.token == "sample-token" else {
        throw APIError.decoding("Unexpected login token in fixture")
    }

    let houseData = try loadFixture("house_detail")
    let house = try decoder.decode(HouseDetail.self, from: houseData)
    guard house.houseNumber == 5, house.ageDays == 19 else {
        throw APIError.decoding("Unexpected house detail fixture values")
    }

    let monitoringData = try loadFixture("farm_monitoring")
    let monitoring = try decoder.decode(FarmMonitoringResponse.self, from: monitoringData)
    guard monitoring.housesCount == 2, monitoring.houses.first?.houseNumber == 1 else {
        throw APIError.decoding("Unexpected farm monitoring fixture values")
    }

    let comparisonData = try loadFixture("house_comparison")
    let comparison = try decoder.decode(HouseComparisonResponse.self, from: comparisonData)
    guard comparison.count == 2, comparison.houses.first?.farmID == 12 else {
        throw APIError.decoding("Unexpected house comparison fixture values")
    }
}

do {
    try runChecks()
    print("ContractCheck passed: fixture decoding succeeded.")
} catch {
    fputs("ContractCheck failed: \(error.localizedDescription)\n", stderr)
    exit(1)
}
