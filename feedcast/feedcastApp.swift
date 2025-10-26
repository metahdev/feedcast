//
//  feedcastApp.swift
//  feedcast
//
//  Created by Askar Almukhamet on 24.10.2025.
//

//
//  feedcastApp.swift
//  feedcast
//
//  AI-personalized podcast app for iOS
//  Main app entry point
//

import SwiftUI

@main
struct feedcastApp: App {
    @StateObject private var userService = UserService.shared
    
    var body: some Scene {
        WindowGroup {
            Group {
                if !userService.isAuthenticated {
                    // Step 1: Show auth screen for new/returning users
                    AuthenticationView(onComplete: {
                        print("📱 Auth completed")
                    })
                    .onAppear {
                        print("📱 Auth screen shown - user needs to sign up/sign in")
                    }
                } else if let user = userService.currentUser, !user.onboarded {
                    // Step 2: After auth, show onboarding if not completed
                    OnboardingView(onComplete: {
                        print("📱 Onboarding completed, marking as done")
                        Task {
                            try? await userService.markOnboarded()
                        }
                    })
                } else {
                    // Step 3: Show main app when authenticated AND onboarded
                    ContentView()
                        .onAppear {
                            print("📱 Main app shown - user is authenticated and onboarded")
                        }
                }
            }
            .environmentObject(userService)
            .onChange(of: userService.isAuthenticated) { oldValue, newValue in
                print("📱 Auth state changed: \(oldValue) → \(newValue)")
            }
            .onChange(of: userService.currentUser?.onboarded) { oldValue, newValue in
                print("📱 Onboarding state changed: \(oldValue ?? false) → \(newValue ?? false)")
            }
        }
    }
}
