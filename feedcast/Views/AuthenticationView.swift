//
//  AuthenticationView.swift
//  feedcast
//
//  Authentication screen (Sign In / Sign Up)
//

import SwiftUI

struct AuthenticationView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var viewModel = AuthViewModel()
    @State private var isSignUp = true
    let onComplete: (() -> Void)?
    
    init(onComplete: (() -> Void)? = nil) {
        self.onComplete = onComplete
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                LinearGradient(
                    colors: [.blue.opacity(0.15), .purple.opacity(0.15)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                ScrollView {
                    VStack(spacing: 30) {
                        // Logo
                        VStack(spacing: 16) {
                            Image(systemName: "waveform.circle.fill")
                                .font(.system(size: 60))
                                .foregroundStyle(.blue)
                            
                            Text("Feedcast")
                                .font(.system(size: 32, weight: .bold))
                        }
                        .padding(.top, 40)
                        
                        // Toggle Sign In / Sign Up
                        Picker("Mode", selection: $isSignUp) {
                            Text("Sign Up").tag(true)
                            Text("Sign In").tag(false)
                        }
                        .pickerStyle(.segmented)
                        .padding(.horizontal)
                        
                        // Form
                        VStack(spacing: 16) {
                            if isSignUp {
                                TextField("Name", text: $viewModel.name)
                                    .textContentType(.name)
                                    .textInputAutocapitalization(.words)
                                    .padding()
                                    .background(.white.opacity(0.95))
                                    .cornerRadius(12)
                                    .shadow(color: Color.black.opacity(0.1), radius: 5, x: 0, y: 2)
                            }
                            
                            TextField("Email", text: $viewModel.email)
                                .textContentType(.emailAddress)
                                .textInputAutocapitalization(.never)
                                .keyboardType(.emailAddress)
                                .autocorrectionDisabled()
                                .padding()
                                .background(.white.opacity(0.95))
                                .cornerRadius(12)
                                .shadow(color: Color.black.opacity(0.1), radius: 5, x: 0, y: 2)
                            
                            SecureField("Password", text: $viewModel.password)
                                .textContentType(isSignUp ? .newPassword : .password)
                                .padding()
                                .background(.white.opacity(0.95))
                                .cornerRadius(12)
                                .shadow(color: Color.black.opacity(0.1), radius: 5, x: 0, y: 2)
                            
                            if isSignUp && !viewModel.password.isEmpty {
                                SecureField("Confirm Password", text: $viewModel.confirmPassword)
                                    .textContentType(.newPassword)
                                    .padding()
                                    .background(.white.opacity(0.95))
                                    .cornerRadius(12)
                                    .shadow(color: Color.black.opacity(0.1), radius: 5, x: 0, y: 2)
                            }
                        }
                        .padding(.horizontal)
                        
                        // Error message
                        if let error = viewModel.errorMessage {
                            Text(error)
                                .font(.subheadline)
                                .foregroundStyle(.red)
                                .padding(.horizontal)
                        }
                        
                        // Submit button
                        Button {
                            print("🔘 Button tapped! isSignUp: \(isSignUp)")
                            Task {
                                await viewModel.authenticate(isSignUp: isSignUp)
                                if viewModel.isAuthenticated {
                                    print("✅ Authentication successful, calling onComplete and dismiss")
                                    onComplete?()
                                    dismiss()
                                }
                            }
                        } label: {
                            Group {
                                if viewModel.isLoading {
                                    ProgressView()
                                        .tint(.white)
                                } else {
                                    Text(isSignUp ? "Create Account" : "Sign In")
                                        .fontWeight(.semibold)
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .padding()
                            .background(.blue)
                            .foregroundStyle(.white)
                            .cornerRadius(12)
                        }
                        .disabled(!viewModel.canSubmit || viewModel.isLoading)
                        .opacity((!viewModel.canSubmit || viewModel.isLoading) ? 0.5 : 1.0)
                        .padding(.horizontal)
                        
                        Spacer()
                    }
                }
            }
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

// MARK: - ViewModel

@MainActor
class AuthViewModel: ObservableObject {
    @Published var name = ""
    @Published var email = ""
    @Published var password = ""
    @Published var confirmPassword = ""
    @Published var isLoading = false
    @Published var errorMessage: String?
    @Published var isAuthenticated = false
    
    private let userService = UserService.shared
    
    var canSubmit: Bool {
        !email.isEmpty && !password.isEmpty && password.count >= 6
    }
    
    func authenticate(isSignUp: Bool) async {
        print("🎯 authenticate() called! isSignUp: \(isSignUp)")
        errorMessage = nil
        isLoading = true
        defer { isLoading = false }
        
        // Validate
        guard canSubmit else {
            print("❌ Validation failed: canSubmit is false")
            errorMessage = "Please fill in all fields"
            return
        }
        print("✅ canSubmit passed")
        
        if isSignUp {
            guard !name.isEmpty else {
                errorMessage = "Please enter your name"
                return
            }
            
            guard password == confirmPassword else {
                errorMessage = "Passwords don't match"
                return
            }
        }
        
        do {
            if isSignUp {
                // Sign up with Supabase - create basic user account
                print("📱 AuthView: Starting sign up...")
                _ = try await userService.signUp(
                    email: email,
                    password: password,
                    name: name,
                    interests: [], // Interests will be collected in onboarding
                    dailyPodcastEnabled: false,
                    dailyPodcastTime: Date()
                )
                print("📱 AuthView: Sign up completed successfully")
            } else {
                // Sign in with Supabase
                print("📱 AuthView: Starting sign in...")
                _ = try await userService.signIn(email: email, password: password)
                print("📱 AuthView: Sign in completed successfully")
            }
            
            isAuthenticated = true
        } catch {
            print("❌ Auth error: \(error)")
            if let nsError = error as NSError? {
                print("❌ Error domain: \(nsError.domain), code: \(nsError.code)")
                print("❌ Error info: \(nsError.userInfo)")
            }
            errorMessage = error.localizedDescription
        }
    }
    
}

#Preview {
    AuthenticationView()
}

