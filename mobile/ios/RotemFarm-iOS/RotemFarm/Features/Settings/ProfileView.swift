//
//  ProfileView.swift
//  RotemFarm — Profile, farms & access, team, pair controller, sign out.
//

import SwiftUI

struct ProfileView: View {
    @Environment(MockDataStore.self) private var store
    @Environment(AuthService.self) private var auth

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 12) {
                    profileHeader

                    SectionHeader(title: "Notifications")
                    notificationsCard

                    SectionHeader(title: "Farms & access")
                    farmsCard

                    SectionHeader(title: "Team")
                    teamCard

                    SectionHeader(title: "Web parity modules")
                    parityModulesCard

                    SectionHeader(title: "Controllers")
                    controllersCard

                    signOutButton
                }
                .padding(14)
            }
            .background(Color.appBackground)
            .navigationTitle("Profile")
        }
    }

    // MARK: Header

    private var profileHeader: some View {
        HStack(spacing: 12) {
            Circle()
                .fill(BrandGradient.hero)
                .frame(width: 56, height: 56)
                .overlay(
                    Text(store.currentUser.initials)
                        .font(.system(size: 18, weight: .bold))
                        .foregroundStyle(.white)
                )
            VStack(alignment: .leading, spacing: 3) {
                Text(store.currentUser.name).font(AppFont.titleMedium)
                Text(store.currentUser.email)
                    .font(AppFont.caption)
                    .foregroundStyle(.secondary)
                PillBadge(text: store.currentUser.role.displayName,
                          style: store.currentUser.role == .owner ? .ok : .info,
                          systemImage: "person.fill.badge.plus")
            }
            Spacer()
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.appCard, in: RoundedRectangle(cornerRadius: AppRadius.hero))
    }

    // MARK: Notifications

    @State private var criticalOn = true
    @State private var warningOn  = true
    @State private var infoOn     = false
    @State private var aiTipsOn   = true

    private var notificationsCard: some View {
        CardSection {
            VStack(spacing: 0) {
                Toggle(isOn: $criticalOn) {
                    HStack(spacing: 10) {
                        Image(systemName: "exclamationmark.triangle.fill")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(.white)
                            .frame(width: 26, height: 26)
                            .background(Color.stateCritical, in: RoundedRectangle(cornerRadius: 7))
                        Text("Critical (wakes phone)").font(AppFont.body)
                    }
                }
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                Toggle(isOn: $warningOn) {
                    HStack(spacing: 10) {
                        Image(systemName: "exclamationmark.circle.fill")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(.white)
                            .frame(width: 26, height: 26)
                            .background(Color.stateWarning, in: RoundedRectangle(cornerRadius: 7))
                        Text("Warnings").font(AppFont.body)
                    }
                }
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                Toggle(isOn: $infoOn) {
                    HStack(spacing: 10) {
                        Image(systemName: "info.circle.fill")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(.white)
                            .frame(width: 26, height: 26)
                            .background(Color.stateInfo, in: RoundedRectangle(cornerRadius: 7))
                        Text("Info").font(AppFont.body)
                    }
                }
                Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                Toggle(isOn: $aiTipsOn) {
                    HStack(spacing: 10) {
                        Image(systemName: "sparkles")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(.white)
                            .frame(width: 26, height: 26)
                            .background(Color.aiEnd, in: RoundedRectangle(cornerRadius: 7))
                        Text("AI tips").font(AppFont.body)
                    }
                }
            }
            .tint(.farmGreen)
        }
    }

    // MARK: Farms

    private var farmsCard: some View {
        CardSection {
            VStack(spacing: 0) {
                ForEach(Array(store.farms.enumerated()), id: \.element.id) { idx, farm in
                    Button {
                        store.switchFarm(farm.id)
                    } label: {
                        HStack(spacing: 10) {
                            Image(systemName: "mappin.and.ellipse")
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundStyle(.white)
                                .frame(width: 26, height: 26)
                                .background(farm.worstState.tint,
                                            in: RoundedRectangle(cornerRadius: 7))
                            VStack(alignment: .leading, spacing: 2) {
                                Text(farm.name).font(AppFont.body).foregroundStyle(.primary)
                                Text("\(farm.totalBirds.formatted()) birds · \(farm.alertSummary)")
                                    .font(AppFont.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            if farm.id == store.currentFarmId {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 13, weight: .semibold))
                                    .foregroundStyle(Color.farmGreen)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                    if idx < store.farms.count - 1 {
                        Divider().overlay(Color.appSeparator).padding(.vertical, 10)
                    }
                }
            }
        }
    }

    // MARK: Team

    private var teamCard: some View {
        CardSection {
            VStack(spacing: 0) {
                ForEach(Array(store.team.enumerated()), id: \.element.id) { idx, m in
                    HStack(spacing: 10) {
                        Circle()
                            .fill(m.role.tint.opacity(0.15))
                            .frame(width: 30, height: 30)
                            .overlay(
                                Text(m.initials)
                                    .font(.system(size: 11, weight: .bold))
                                    .foregroundStyle(m.role.tint)
                            )
                        VStack(alignment: .leading, spacing: 2) {
                            HStack(spacing: 6) {
                                Text(m.name).font(AppFont.body)
                                if m.isYou {
                                    Text("You")
                                        .font(.system(size: 9, weight: .bold))
                                        .padding(.horizontal, 5)
                                        .padding(.vertical, 1)
                                        .background(Color.farmSoft, in: Capsule())
                                        .foregroundStyle(Color.farmGreen)
                                }
                            }
                            Text("\(m.role.displayName) · \(m.scope)")
                                .font(AppFont.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                    }
                    .padding(.vertical, 6)
                    if idx < store.team.count - 1 {
                        Divider().overlay(Color.appSeparator)
                    }
                }
                Button { } label: {
                    HStack {
                        Image(systemName: "person.fill.badge.plus")
                        Text("Invite member")
                    }
                }
                .buttonStyle(SecondaryButtonStyle())
                .padding(.top, 10)
            }
        }
    }

    // MARK: Controllers

    private var controllersCard: some View {
        CardSection {
            VStack(spacing: 0) {
                ForEach(Array(store.controllers.enumerated()), id: \.element.id) { idx, c in
                    HStack(spacing: 10) {
                        Image(systemName: "cpu")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundStyle(.white)
                            .frame(width: 26, height: 26)
                            .background(c.state.tint, in: RoundedRectangle(cornerRadius: 7))
                        VStack(alignment: .leading, spacing: 2) {
                            Text("\(c.model) · \(c.houseName)").font(AppFont.body)
                            Text("S/N \(c.serial)").font(AppFont.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                        PillBadge(text: lastSeenText(c.lastSeen),
                                  style: c.state == .ok ? .ok : .warning)
                    }
                    .padding(.vertical, 6)
                    if idx < store.controllers.count - 1 {
                        Divider().overlay(Color.appSeparator)
                    }
                }
                Button { } label: {
                    HStack {
                        Image(systemName: "plus.circle.fill")
                        Text("Pair new controller")
                    }
                }
                .buttonStyle(PrimaryButtonStyle())
                .padding(.top, 10)
            }
        }
    }

    private var parityModulesCard: some View {
        CardSection {
            VStack(spacing: 10) {
                NavigationLink(destination: OrganizationsView()) {
                    ValueRow(systemImage: "building.2.fill", iconColor: .stateInfo, title: "Organizations", value: "\(store.organizations.count) orgs")
                }
                NavigationLink(destination: WorkersManagementView()) {
                    ValueRow(systemImage: "person.3.fill", iconColor: .farmGreen, title: "Worker management", value: "\(store.workers.count) workers")
                }
                NavigationLink(destination: ProgramManagerView()) {
                    ValueRow(systemImage: "slider.horizontal.3", iconColor: .stateWarning, title: "Program management", value: "\(store.programs.count) programs")
                }
                NavigationLink(destination: TaskCenterView()) {
                    ValueRow(systemImage: "checklist", iconColor: .stateInfo, title: "Task manager", value: "\(store.tasks.count) tasks")
                }
                NavigationLink(destination: AdminToolsView()) {
                    ValueRow(systemImage: "lock.shield.fill", iconColor: .stateCritical, title: "Email, security, Rotem admin", value: "Admin tools")
                }
            }
        }
    }

    private func lastSeenText(_ d: Date) -> String {
        let sec = Int(-d.timeIntervalSinceNow)
        if sec < 60   { return "\(sec)s ago" }
        if sec < 3600 { return "\(sec / 60)m ago" }
        return "\(sec / 3600)h ago"
    }

    // MARK: Sign out

    private var signOutButton: some View {
        Button {
            auth.signOut()
        } label: {
            Label("Sign out", systemImage: "rectangle.portrait.and.arrow.right")
                .foregroundStyle(Color.stateCritical)
        }
        .buttonStyle(SecondaryButtonStyle())
        .padding(.top, 8)
    }
}

#Preview {
    ProfileView()
        .environment(MockDataStore.preview)
        .environment(AuthService.previewSignedIn())
}
