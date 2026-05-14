// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FarmManagementCore",
    platforms: [
        .iOS(.v16),
        .macOS(.v13)
    ],
    products: [
        .library(
            name: "FarmManagementCore",
            targets: ["FarmManagementCore"]
        ),
        .executable(
            name: "ContractCheck",
            targets: ["ContractCheck"]
        )
    ],
    targets: [
        .target(
            name: "FarmManagementCore"
        ),
        .executableTarget(
            name: "ContractCheck",
            dependencies: ["FarmManagementCore"],
            path: "Tools/ContractCheck",
            resources: [.process("Fixtures")]
        )
    ]
)
