//
//  LoginView.swift
//  RotemFarm — Sign in with Apple splash.
//

import AuthenticationServices
import SwiftUI

struct LoginView: View {
    @Environment(AuthService.self) private var auth
    @Environment(\.colorScheme) private var scheme
    @State private var username = ""
    @State private var password = ""
    @State private var selectedEnvironment: APIEnvironment = .local
    @State private var baseURLText = ""

    var body: some View {
        ZStack {
            BrandGradient.hero
                .overlay(backgroundAccents)
                .ignoresSafeArea()

            VStack(alignment: .leading, spacing: 16) {
                Spacer(minLength: 60)

                RoundedRectangle(cornerRadius: 16)
                    .fill(Color.white.opacity(0.16))
                    .frame(width: 56, height: 56)
                    .overlay(
                        Image(systemName: "house.fill")
                            .font(.system(size: 26, weight: .semibold))
                            .foregroundStyle(.white)
                    )

                VStack(alignment: .leading, spacing: 8) {
                    Text("Welcome to RotemFarm")
                        .font(AppFont.titleLarge)
                        .foregroundStyle(.white)
                    Text("Monitor your Rotem-controlled broiler houses from anywhere.")
                        .font(AppFont.body)
                        .foregroundStyle(Color.white.opacity(0.82))
                        .fixedSize(horizontal: false, vertical: true)
                }

                Spacer()

                VStack(spacing: 8) {
                    Picker("Environment", selection: $selectedEnvironment) {
                        ForEach(APIEnvironment.allCases, id: \.self) { environment in
                            Text(environment.displayName).tag(environment)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(.bottom, 2)

                    if !baseURLText.isEmpty {
                        Text(baseURLText + "/api")
                            .font(AppFont.caption)
                            .foregroundStyle(Color.white.opacity(0.75))
                            .frame(maxWidth: .infinity, alignment: .leading)
                    }

                    TextField("Username", text: $username)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                        .padding(12)
                        .background(Color.white.opacity(0.12), in: RoundedRectangle(cornerRadius: 10))
                        .foregroundStyle(.white)
                    SecureField("Password", text: $password)
                        .padding(12)
                        .background(Color.white.opacity(0.12), in: RoundedRectangle(cornerRadius: 10))
                        .foregroundStyle(.white)
                }

                Button("Sign in") {
                    Task { await auth.signIn(username: username, password: password) }
                }
                .buttonStyle(PrimaryButtonStyle())

                SignInWithAppleButton(
                    onRequest: { $0.requestedScopes = [.fullName, .email] },
                    onCompletion: { _ in
                        Task { await auth.signInWithApple() }
                    }
                )
                .signInWithAppleButtonStyle(scheme == .dark ? .white : .black)
                .frame(height: 48)
                .cornerRadius(12)

                if auth.status == .signingIn {
                    ProgressView().tint(.white).frame(maxWidth: .infinity)
                }
                if let error = auth.errorMessage {
                    Text(error)
                        .font(AppFont.caption)
                        .foregroundStyle(Color.stateCritical)
                        .frame(maxWidth: .infinity, alignment: .center)
                }
            }
            .padding(.horizontal, 28)
            .padding(.bottom, 28)
            .onAppear {
                username = auth.username
                password = auth.password
                selectedEnvironment = auth.environment
                Task {
                    baseURLText = await auth.currentBaseURLString
                }
            }
            .onChange(of: selectedEnvironment) { _, newEnvironment in
                Task {
                    await auth.selectEnvironment(newEnvironment)
                    baseURLText = await auth.currentBaseURLString
                }
            }
        }
    }

    private var backgroundAccents: some View {
        GeometryReader { geo in
            Circle()
                .fill(Color.stateOK.opacity(0.35))
                .frame(width: geo.size.width * 0.8)
                .blur(radius: 50)
                .offset(x: geo.size.width * 0.4, y: geo.size.height * 0.7)
            Circle()
                .fill(Color.farmGreen.opacity(0.45))
                .frame(width: geo.size.width * 0.6)
                .blur(radius: 40)
                .offset(x: -geo.size.width * 0.2, y: -geo.size.height * 0.1)
        }
    }
}

#Preview {
    LoginView().environment(AuthService.previewSignedIn())
}
