//
//  Theme.swift
//  RotemFarm — Design tokens.
//
//  Centralizes colors, typography, and sensor state so every screen stays
//  on-brand. Mirrors the tokens in RotemFarm-iOS-UX-Mockups.html.
//

import SwiftUI

// MARK: - Colors ---------------------------------------------------------------

extension Color {
    // Brand
    static let farmGreen = Color(red: 46 / 255, green: 125 / 255, blue: 91 / 255)   // #2E7D5B
    static let farmDeep  = Color(red: 31 / 255, green:  92 / 255, blue: 66 / 255)   // #1F5C42
    static let farmSoft  = Color(red: 232 / 255, green: 242 / 255, blue: 236 / 255) // #E8F2EC

    // State
    static let stateOK       = Color(red:  52 / 255, green: 199 / 255, blue:  89 / 255) // #34C759
    static let stateWarning  = Color(red: 255 / 255, green: 149 / 255, blue:   0 / 255) // #FF9500
    static let stateCritical = Color(red: 255 / 255, green:  59 / 255, blue:  48 / 255) // #FF3B30
    static let stateInfo     = Color(red:   0 / 255, green: 122 / 255, blue: 255 / 255) // #007AFF

    // AI gradient
    static let aiStart = Color(red: 124 / 255, green: 58 / 255, blue: 237 / 255) // #7C3AED
    static let aiEnd   = Color(red:  79 / 255, green: 70 / 255, blue: 229 / 255) // #4F46E5

    // Surfaces — mapped to iOS system colors so dark mode works for free.
    static let appBackground = Color(uiColor: .systemGroupedBackground)
    static let appCard       = Color(uiColor: .secondarySystemGroupedBackground)
    static let appSeparator  = Color(uiColor: .separator)

    // Sensor-tint soft backgrounds
    static let warnSoft = Color.stateWarning.opacity(0.14)
    static let critSoft = Color.stateCritical.opacity(0.14)
    static let okSoft   = Color.stateOK.opacity(0.14)
    static let infoSoft = Color.stateInfo.opacity(0.14)
}

// MARK: - Gradients ------------------------------------------------------------

enum BrandGradient {
    static let hero = LinearGradient(
        colors: [.farmDeep, .farmGreen],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
    static let ai = LinearGradient(
        colors: [.aiStart, .aiEnd],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
    static let aiSoft = LinearGradient(
        colors: [Color(red: 0.935, green: 0.945, blue: 1.0),
                 Color(red: 0.957, green: 0.925, blue: 1.0)],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
    static let critical = LinearGradient(
        colors: [.stateCritical, Color(red: 1.0, green: 0.42, blue: 0.34)],
        startPoint: .topLeading, endPoint: .bottomTrailing
    )
}

// MARK: - Typography -----------------------------------------------------------

enum AppFont {
    static let hero        = Font.system(size: 42, weight: .bold,     design: .rounded)
    static let bigNum      = Font.system(size: 32, weight: .bold,     design: .rounded)
    static let titleLarge  = Font.system(size: 28, weight: .bold)
    static let titleMedium = Font.system(size: 22, weight: .bold)
    static let title       = Font.system(size: 17, weight: .semibold)
    static let body        = Font.system(size: 14)
    static let bodyBold    = Font.system(size: 14, weight: .semibold)
    static let caption     = Font.system(size: 12)
    static let captionBold = Font.system(size: 12, weight: .semibold)
    static let tiny        = Font.system(size: 10)
    static let eyebrow     = Font.system(size: 11, weight: .bold)   // uppercase section labels
}

// MARK: - Sensor state ---------------------------------------------------------

enum SensorState: String, Codable, CaseIterable, Sendable {
    case ok, warning, critical

    var tint: Color {
        switch self {
        case .ok:       .farmGreen
        case .warning:  .stateWarning
        case .critical: .stateCritical
        }
    }

    var iconBackground: Color {
        switch self {
        case .ok:       .farmSoft
        case .warning:  .warnSoft
        case .critical: .critSoft
        }
    }

    var pillBackground: Color {
        switch self {
        case .ok:       .okSoft
        case .warning:  .warnSoft
        case .critical: .critSoft
        }
    }

    var pillText: Color {
        switch self {
        case .ok:       Color(red: 0.12, green: 0.48, blue: 0.23)
        case .warning:  Color(red: 0.63, green: 0.32, blue: 0.04)
        case .critical: Color(red: 0.70, green: 0.14, blue: 0.11)
        }
    }

    var label: String {
        switch self {
        case .ok:       "Healthy"
        case .warning:  "Warning"
        case .critical: "Critical"
        }
    }
}

// MARK: - Layout tokens --------------------------------------------------------

enum AppRadius {
    static let card: CGFloat       = 14
    static let hero: CGFloat       = 18
    static let pill: CGFloat       = 999
    static let button: CGFloat     = 12
    static let control: CGFloat    = 9
}

enum AppSpacing {
    static let xs: CGFloat  = 4
    static let s:  CGFloat  = 8
    static let m:  CGFloat  = 12
    static let l:  CGFloat  = 16
    static let xl: CGFloat  = 24
}
