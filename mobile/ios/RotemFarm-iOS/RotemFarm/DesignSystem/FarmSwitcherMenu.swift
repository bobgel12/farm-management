import SwiftUI

struct FarmSwitcherMenu: View {
    @Environment(MockDataStore.self) private var store

    var body: some View {
        Menu {
            if store.farms.isEmpty {
                Text("No farms available")
            } else {
                ForEach(store.farms) { farm in
                    Button {
                        store.switchFarm(farm.id)
                    } label: {
                        if farm.id == store.currentFarmId {
                            Label(farm.name, systemImage: "checkmark")
                        } else {
                            Text(farm.name)
                        }
                    }
                }
            }
        } label: {
            HStack(spacing: 6) {
                Image(systemName: "building.2")
                Text(store.currentFarm.name)
                    .lineLimit(1)
            }
            .font(.system(size: 13, weight: .semibold))
        }
    }
}

