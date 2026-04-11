import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var appState: AppState
    @State private var username = ""
    @State private var password = ""
    @State private var isSubmitting = false
    @FocusState private var focusedField: Field?

    private enum Field {
        case username
        case password
    }

    var body: some View {
        NavigationStack {
            ZStack {
                LinearGradient(
                    colors: [Color.green.opacity(0.18), Color.blue.opacity(0.12), Color.clear],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 20) {
                        VStack(spacing: 8) {
                            Image(systemName: "leaf.circle.fill")
                                .font(.system(size: 54))
                                .foregroundStyle(.green)
                            Text("Farm Management")
                                .font(.largeTitle.weight(.bold))
                            Text("Sign in to monitor your farms in real time.")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.top, 28)

                        VStack(spacing: 14) {
                            TextField("Username", text: $username)
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .keyboardType(.asciiCapable)
                                .textContentType(.username)
                                .submitLabel(.next)
                                .focused($focusedField, equals: .username)
                                .onSubmit { focusedField = .password }
                                .padding(12)
                                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))

                            SecureField("Password", text: $password)
                                .textContentType(.password)
                                .submitLabel(.go)
                                .focused($focusedField, equals: .password)
                                .onSubmit { submit() }
                                .padding(12)
                                .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 12))

                            if let error = appState.authError {
                                Text(error)
                                    .foregroundStyle(.red)
                                    .font(.footnote)
                                    .frame(maxWidth: .infinity, alignment: .leading)
                            }

                            Button(action: submit) {
                                Group {
                                    if isSubmitting {
                                        ProgressView()
                                    } else {
                                        Text("Sign In")
                                            .fontWeight(.semibold)
                                    }
                                }
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 12)
                            }
                            .buttonStyle(.borderedProminent)
                            .tint(.green)
                            .disabled(username.isEmpty || password.isEmpty || isSubmitting)
                        }
                        .padding(16)
                        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 18))
                    }
                    .padding(.horizontal)
                }
            }
            .toolbar {
                ToolbarItemGroup(placement: .keyboard) {
                    Spacer()
                    Button("Done") { focusedField = nil }
                }
            }
            .scrollDismissesKeyboard(.interactively)
            .navigationTitle("Login")
            .navigationBarTitleDisplayMode(.inline)
        }
    }

    private func submit() {
        guard username.isEmpty == false, password.isEmpty == false, isSubmitting == false else {
            return
        }
        focusedField = nil
        Task {
            isSubmitting = true
            _ = await appState.login(username: username, password: password)
            isSubmitting = false
        }
    }
}
