import SwiftUI

struct OrganizationsView: View {
    @Environment(MockDataStore.self) private var store

    var body: some View {
        List {
            Section("Organizations") {
                ForEach(store.organizations) { org in
                    VStack(alignment: .leading, spacing: 4) {
                        HStack {
                            Text(org.name).font(AppFont.bodyBold)
                            Spacer()
                            PillBadge(text: org.active ? "Active" : "Inactive", style: org.active ? .ok : .neutral)
                        }
                        Text("\(org.memberCount) members · \(org.farmsCount) farms")
                            .font(AppFont.caption)
                            .foregroundStyle(.secondary)
                    }
                }
            }

            Section("Members") {
                ForEach(store.organizationMembers) { member in
                    HStack {
                        VStack(alignment: .leading, spacing: 3) {
                            Text(member.name).font(AppFont.body)
                            Text(member.email).font(AppFont.caption).foregroundStyle(.secondary)
                        }
                        Spacer()
                        Text(member.role.displayName).font(AppFont.captionBold)
                    }
                }
            }
        }
        .navigationTitle("Organizations")
    }
}

