//
//  Components.swift
//  RotemFarm — Shared SwiftUI building blocks.
//
//  Keeps screens declarative. Anything that appears on more than one screen
//  lives here.
//

import SwiftUI

// MARK: - Section header -------------------------------------------------------

struct SectionHeader: View {
    let title: String
    var trailing: String? = nil

    var body: some View {
        HStack {
            Text(title.uppercased())
                .font(AppFont.eyebrow)
                .foregroundStyle(.secondary)
                .tracking(0.6)
            Spacer()
            if let trailing {
                Text(trailing)
                    .font(AppFont.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.horizontal, 6)
        .padding(.top, 10)
        .padding(.bottom, 4)
    }
}

// MARK: - Pill badge -----------------------------------------------------------

struct PillBadge: View {
    enum Style { case ok, warning, critical, info, ai, live, neutral }
    let text: String
    var style: Style = .neutral
    var systemImage: String? = nil

    var body: some View {
        HStack(spacing: 5) {
            if style == .live {
                Circle()
                    .fill(Color.farmGreen)
                    .frame(width: 6, height: 6)
                    .overlay(Circle().stroke(Color.farmGreen.opacity(0.25), lineWidth: 3))
            }
            if let systemImage {
                Image(systemName: systemImage).font(.system(size: 10, weight: .semibold))
            }
            Text(text)
                .font(.system(size: 11, weight: .semibold))
        }
        .padding(.horizontal, 9)
        .padding(.vertical, 3)
        .background(bg, in: Capsule())
        .foregroundStyle(fg)
    }

    private var bg: Color {
        switch style {
        case .ok, .live: .okSoft
        case .warning:   .warnSoft
        case .critical:  .critSoft
        case .info:      .infoSoft
        case .ai:        .clear
        case .neutral:   Color(uiColor: .tertiarySystemFill)
        }
    }

    private var fg: Color {
        switch style {
        case .ok, .live: Color(red: 0.12, green: 0.48, blue: 0.23)
        case .warning:   Color(red: 0.63, green: 0.32, blue: 0.04)
        case .critical:  Color(red: 0.70, green: 0.14, blue: 0.11)
        case .info:      Color(red: 0.04, green: 0.31, blue: 0.65)
        case .ai:        .white
        case .neutral:   .secondary
        }
    }
}

// MARK: - Sensor card (3 states) -----------------------------------------------

struct SensorCard: View {
    let title: String
    let value: String
    let unit: String
    let state: SensorState
    let systemImage: String
    /// 0...1 — how close the value is to its alarm threshold.
    let fillFraction: Double

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack {
                Image(systemName: systemImage)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(state.tint)
                    .frame(width: 26, height: 26)
                    .background(state.iconBackground, in: RoundedRectangle(cornerRadius: 8))
                Spacer()
            }
            Text(title.uppercased())
                .font(.system(size: 11, weight: .medium))
                .tracking(0.4)
                .foregroundStyle(.secondary)
            HStack(alignment: .firstTextBaseline, spacing: 2) {
                Text(value).font(.system(size: 20, weight: .bold, design: .rounded))
                Text(unit)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundStyle(.secondary)
            }
            GeometryReader { geo in
                ZStack(alignment: .leading) {
                    Capsule().fill(Color(uiColor: .tertiarySystemFill))
                    Capsule()
                        .fill(state.tint)
                        .frame(width: geo.size.width * max(0.05, min(1, fillFraction)))
                }
            }
            .frame(height: 4)
        }
        .padding(11)
        .frame(minHeight: 96, alignment: .topLeading)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
    }
}

// MARK: - Hero metric card -----------------------------------------------------

struct HeroMetricCard<Trailing: View>: View {
    let label: String
    let value: String
    let unit: String
    let target: String?
    let delta: (text: String, state: SensorState)?
    @ViewBuilder let trailing: () -> Trailing

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(label.uppercased())
                        .font(AppFont.eyebrow)
                        .tracking(0.6)
                        .foregroundStyle(.secondary)
                    HStack(alignment: .firstTextBaseline, spacing: 4) {
                        Text(value).font(AppFont.hero)
                        Text(unit)
                            .font(.system(size: 18, weight: .semibold, design: .rounded))
                            .foregroundStyle(.secondary)
                    }
                    if let target {
                        HStack(spacing: 6) {
                            Text(target).font(AppFont.caption).foregroundStyle(.secondary)
                            if let delta {
                                Text(delta.text)
                                    .font(AppFont.captionBold)
                                    .foregroundStyle(delta.state.tint)
                            }
                        }
                    }
                }
                Spacer()
                trailing()
            }
        }
        .padding(14)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.hero))
    }
}

extension HeroMetricCard where Trailing == EmptyView {
    init(label: String, value: String, unit: String, target: String?, delta: (text: String, state: SensorState)?) {
        self.init(label: label, value: value, unit: unit, target: target, delta: delta) { EmptyView() }
    }
}

// MARK: - KPI tile --------------------------------------------------------------

struct KPICard: View {
    let label: String
    let value: String
    var delta: String? = nil
    var deltaState: SensorState = .ok

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(label.uppercased())
                .font(.system(size: 10, weight: .semibold))
                .tracking(0.4)
                .foregroundStyle(.secondary)
            Text(value).font(.system(size: 18, weight: .bold, design: .rounded))
            if let delta {
                Text(delta)
                    .font(.system(size: 10, weight: .semibold))
                    .foregroundStyle(deltaState.tint)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.button))
    }
}

// MARK: - House card ------------------------------------------------------------

struct HouseCardMini: View {
    let houseName: String
    let subtitle: String
    let state: SensorState
    let pillText: String
    /// ordered (label, value) pairs to show in the bottom strip
    let stats: [(label: String, value: String)]

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                Image(systemName: "house.fill")
                    .font(.system(size: 20))
                    .foregroundStyle(state.tint)
                    .frame(width: 36, height: 36)
                    .background(state.iconBackground, in: RoundedRectangle(cornerRadius: 10))
                VStack(alignment: .leading, spacing: 2) {
                    Text(houseName).font(AppFont.bodyBold)
                    Text(subtitle).font(.system(size: 11)).foregroundStyle(.secondary)
                }
                Spacer()
                PillBadge(text: pillText, style: pillStyle)
            }
            if !stats.isEmpty {
                Divider().overlay(Color.appSeparator)
                HStack(alignment: .top, spacing: 10) {
                    ForEach(Array(stats.enumerated()), id: \.offset) { _, s in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(s.value).font(.system(size: 13, weight: .semibold))
                            Text(s.label.uppercased())
                                .font(.system(size: 10, weight: .medium))
                                .tracking(0.3)
                                .foregroundStyle(.secondary)
                        }
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
            }
        }
        .padding(12)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.card)
                .stroke(state == .ok ? Color.clear : state.tint.opacity(0.45), lineWidth: 1)
        )
    }

    private var pillStyle: PillBadge.Style {
        switch state {
        case .ok:       .ok
        case .warning:  .warning
        case .critical: .critical
        }
    }
}

// MARK: - AI tip card -----------------------------------------------------------

struct AICard: View {
    let label: String
    let title: String
    let message: String
    var severity: PillBadge.Style? = nil
    var severityText: String? = nil
    var primaryAction: (title: String, action: () -> Void)? = nil
    var secondaryAction: (title: String, action: () -> Void)? = nil

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 8) {
                RoundedRectangle(cornerRadius: 8)
                    .fill(BrandGradient.ai)
                    .frame(width: 26, height: 26)
                    .overlay(
                        Image(systemName: "sparkle")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundStyle(.white)
                    )
                Text(label.uppercased())
                    .font(AppFont.eyebrow)
                    .tracking(0.6)
                    .foregroundStyle(Color.aiEnd)
                Spacer()
                if let severity, let severityText {
                    PillBadge(text: severityText, style: severity)
                }
            }
            Text(title).font(AppFont.bodyBold)
            Text(message)
                .font(AppFont.caption)
                .foregroundStyle(Color(uiColor: .secondaryLabel))
                .fixedSize(horizontal: false, vertical: true)
            if primaryAction != nil || secondaryAction != nil {
                HStack(spacing: 6) {
                    if let primary = primaryAction {
                        Button(primary.title, action: primary.action)
                            .buttonStyle(AICardButtonStyle(primary: true))
                    }
                    if let secondary = secondaryAction {
                        Button(secondary.title, action: secondary.action)
                            .buttonStyle(AICardButtonStyle(primary: false))
                    }
                }
            }
        }
        .padding(14)
        .background(BrandGradient.aiSoft, in: RoundedRectangle(cornerRadius: AppRadius.card))
        .overlay(
            RoundedRectangle(cornerRadius: AppRadius.card)
                .stroke(Color.aiEnd.opacity(0.15), lineWidth: 1)
        )
    }
}

private struct AICardButtonStyle: ButtonStyle {
    let primary: Bool
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(size: 11, weight: .semibold))
            .padding(.horizontal, 10)
            .padding(.vertical, 6)
            .background(primary ? Color.aiEnd : Color.white,
                        in: RoundedRectangle(cornerRadius: 8))
            .foregroundStyle(primary ? .white : Color.aiEnd)
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}

// MARK: - Segmented control wrapper -------------------------------------------

struct AppSegmented<T: Hashable & CaseIterable & RawRepresentable>: View where T.RawValue == String {
    @Binding var selection: T
    let options: [T]
    var labels: [T: String] = [:]

    var body: some View {
        HStack(spacing: 0) {
            ForEach(options, id: \.self) { opt in
                Button {
                    withAnimation(.easeInOut(duration: 0.18)) { selection = opt }
                } label: {
                    Text(labels[opt] ?? opt.rawValue)
                        .font(.system(size: 12, weight: .medium))
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 6)
                        .background(
                            selection == opt
                            ? Color(uiColor: .systemBackground)
                            : Color.clear,
                            in: RoundedRectangle(cornerRadius: 7)
                        )
                        .foregroundStyle(selection == opt ? .primary : .secondary)
                        .shadow(color: selection == opt
                                ? Color.black.opacity(0.06)
                                : .clear,
                                radius: 1, y: 1)
                }
                .buttonStyle(.plain)
            }
        }
        .padding(2)
        .background(Color(uiColor: .tertiarySystemFill),
                    in: RoundedRectangle(cornerRadius: AppRadius.control))
    }
}

// MARK: - Alert row -------------------------------------------------------------

struct AlertRow: View {
    let systemImage: String
    let title: String
    let meta: String
    let state: SensorState
    var showsChevron: Bool = true

    var body: some View {
        HStack(alignment: .center, spacing: 10) {
            Image(systemName: systemImage)
                .font(.system(size: 14, weight: .semibold))
                .foregroundStyle(state.tint)
                .frame(width: 30, height: 30)
                .background(state.iconBackground, in: RoundedRectangle(cornerRadius: 9))
            VStack(alignment: .leading, spacing: 1) {
                Text(title).font(AppFont.bodyBold)
                Text(meta).font(.system(size: 11)).foregroundStyle(.secondary)
            }
            Spacer(minLength: 0)
            if showsChevron {
                Image(systemName: "chevron.right")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(.tertiary)
            }
        }
        .padding(.vertical, 4)
    }
}

// MARK: - Value row in a grouped list -----------------------------------------

struct ValueRow: View {
    let systemImage: String?
    let iconColor: Color
    let title: String
    let value: String?
    var showsChevron: Bool = true

    var body: some View {
        HStack(spacing: 10) {
            if let systemImage {
                Image(systemName: systemImage)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(.white)
                    .frame(width: 26, height: 26)
                    .background(iconColor, in: RoundedRectangle(cornerRadius: 7))
            }
            Text(title).font(AppFont.body)
            Spacer()
            if let value {
                Text(value).font(AppFont.caption).foregroundStyle(.secondary)
            }
            if showsChevron {
                Image(systemName: "chevron.right")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundStyle(.tertiary)
            }
        }
    }
}

// MARK: - Card container wrapper ----------------------------------------------

struct CardSection<Content: View>: View {
    let content: () -> Content

    init(@ViewBuilder content: @escaping () -> Content) {
        self.content = content
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            content()
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.card))
    }
}

// MARK: - Styled buttons -------------------------------------------------------

struct PrimaryButtonStyle: ButtonStyle {
    var tint: Color = .farmGreen
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(AppFont.bodyBold)
            .foregroundStyle(.white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(tint, in: RoundedRectangle(cornerRadius: AppRadius.button))
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}

struct SecondaryButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(AppFont.bodyBold)
            .foregroundStyle(.primary)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 12)
            .background(Color(uiColor: .tertiarySystemFill),
                        in: RoundedRectangle(cornerRadius: AppRadius.button))
            .opacity(configuration.isPressed ? 0.8 : 1)
    }
}
