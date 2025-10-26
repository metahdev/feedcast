//
//  UserService.swift
//  feedcast
//
//  Service layer for user profile and preferences management.
//
//  FUTURE INTEGRATION NOTES:
//  - Integrate with Supabase Auth for user authentication
//  - Sync user preferences and interests with backend
//  - Implement proper session management
//  - Add iCloud sync for cross-device experience
//

import Foundation
import Combine
import Supabase

/// Service for managing user data and preferences
class UserService: ObservableObject {
    
    // MARK: - Singleton
    static let shared = UserService()
    
    // MARK: - Published Properties
    @Published var currentUser: User?
    @Published var playbackStates: [String: PlaybackState] = [:] // podcastId -> PlaybackState
    @Published var isAuthenticated = false
    
    // MARK: - Private Properties
    private var cancellables = Set<AnyCancellable>()
    private var supabase: SupabaseClient? {
        guard Config.isSupabaseConfigured else { return nil }
        return SupabaseManager.shared.client
    }
    
    private init() {
        Task {
            await checkAuthenticationStatus()
        }
    }
    
    // MARK: - Authentication
    
    /// Check if user is already authenticated
    func checkAuthenticationStatus() async {
        guard let supabase = supabase else {
            // No Supabase configured - user must set it up
            await MainActor.run {
                isAuthenticated = false
                currentUser = nil
            }
            print("⚠️ Supabase not configured. Please update Config.swift with your credentials.")
            return
        }
        
        do {
            let session = try await supabase.auth.session
            // Load user data from database
            try await loadUserFromDatabase(userId: session.user.id.uuidString)
            await MainActor.run {
                isAuthenticated = true
            }
        } catch {
            await MainActor.run {
                isAuthenticated = false
                currentUser = nil
            }
        }
    }
    
    /// Sign up new user
    func signUp(
        email: String,
        password: String,
        name: String,
        interests: [String],
        dailyPodcastEnabled: Bool,
        dailyPodcastTime: Date
    ) async throws -> User {
        guard let supabase = supabase else {
            throw NSError(domain: "UserService", code: 500, userInfo: [NSLocalizedDescriptionKey: "Supabase not configured"])
        }
        
        print("🔐 Starting sign up for: \(email)")
        
        // Sign up with Supabase Auth
        let response = try await supabase.auth.signUp(
            email: email,
            password: password
        )
        
        print("✅ Auth sign up successful. User ID: \(response.user.id)")
        print("📧 Session: \(response.session != nil ? "Active" : "Pending email confirmation")")
        
        // Convert selected interest IDs to Interest objects
        let interestObjects = OnboardingViewModel.availableInterests.filter { interests.contains($0.id) }
        
        // Create user profile
        let newUser = User(
            id: response.user.id.uuidString,
            name: name,
            email: email,
            country: nil,
            age: nil,
            gender: nil,
            occupation: nil,
            newsSources: [],
            interests: interestObjects,
            dailyPodcastEnabled: dailyPodcastEnabled,
            dailyPodcastTime: dailyPodcastTime
        )
        
        print("💾 Saving user profile to database...")
        
        // Save user to database
        do {
            try await saveUserToDatabase(newUser)
            print("✅ User profile saved")
        } catch {
            print("❌ Failed to save user profile: \(error)")
            throw error
        }
        
        // Save interests to database
        print("💾 Saving \(interestObjects.count) interests...")
        for interest in interestObjects {
            do {
                try await saveInterestToDatabase(interest, userId: newUser.id)
            } catch {
                print("⚠️ Failed to save interest \(interest.name): \(error)")
                // Continue with other interests
            }
        }
        print("✅ Interests saved")
        
        await MainActor.run {
            self.currentUser = newUser
            self.isAuthenticated = true
        }
        
        print("✅ Sign up complete!")
        return newUser
    }
    
    /// Sign in existing user
    func signIn(email: String, password: String) async throws -> User {
        guard let supabase = supabase else {
            throw NSError(domain: "UserService", code: 500, userInfo: [NSLocalizedDescriptionKey: "Supabase not configured"])
        }
        
        // Sign in with Supabase Auth
        let response = try await supabase.auth.signIn(
            email: email,
            password: password
        )
        
        // Load user profile from database
        try await loadUserFromDatabase(userId: response.user.id.uuidString)
        
        await MainActor.run {
            self.isAuthenticated = true
        }
        
        guard let user = currentUser else {
            throw NSError(domain: "UserService", code: 404, userInfo: [NSLocalizedDescriptionKey: "User not found"])
        }
        
        return user
    }
    
    /// Sign out current user
    func signOut() async throws {
        guard let supabase = supabase else { return }
        
        try await supabase.auth.signOut()
        
        await MainActor.run {
            self.currentUser = nil
            self.isAuthenticated = false
        }
    }
    
    // MARK: - User Management
    
    /// Load user profile
    func loadUser() async throws -> User {
        guard let user = currentUser else {
            throw NSError(domain: "UserService", code: 404, userInfo: [NSLocalizedDescriptionKey: "User not found"])
        }
        return user
    }
    
    /// Load user from Supabase database
    private func loadUserFromDatabase(userId: String) async throws {
        guard let supabase = supabase else { return }
        
        // Fetch user data
        struct UserResponse: Codable {
            let id: String
            let name: String?
            let email: String?
            let country: String?
            let age: Int?
            let gender: String?
            let occupation: String?
            let news_sources: [String]?
            let onboarded: Bool?
            let created_at: String
        }
        
        let userData: UserResponse = try await supabase
            .from("users")
            .select()
            .eq("id", value: userId)
            .single()
            .execute()
            .value
        
        // Fetch user interests
        struct InterestResponse: Codable {
            let id: String
            let name: String
            let category: String
            let is_active: Bool
        }
        
        let interestsData: [InterestResponse] = try await supabase
            .from("interests")
            .select()
            .eq("user_id", value: userId)
            .execute()
            .value
        
        // Convert to Interest objects
        let interests = interestsData.map { data in
            Interest(
                id: data.id,
                name: data.name,
                category: InterestCategory(rawValue: data.category) ?? .other,
                isActive: data.is_active
            )
        }
        
        let user = User(
            id: userId,
            name: userData.name ?? "User",
            email: userData.email ?? "",
            country: userData.country,
            age: userData.age,
            gender: userData.gender,
            occupation: userData.occupation,
            newsSources: userData.news_sources ?? [],
            interests: interests,
            dailyPodcastEnabled: true,
            dailyPodcastTime: nil,
            onboarded: userData.onboarded ?? false
        )
        
        await MainActor.run {
            self.currentUser = user
        }
    }
    
    /// Save user to Supabase database
    private func saveUserToDatabase(_ user: User) async throws {
        guard let supabase = supabase else { return }
        
        struct UserInsert: Codable {
            let id: String
            let name: String
            let email: String
            let country: String?
            let age: Int?
            let gender: String?
            let occupation: String?
            let news_sources: [String]?
            let onboarded: Bool
        }
        
        let insert = UserInsert(
            id: user.id,
            name: user.name,
            email: user.email,
            country: user.country,
            age: user.age,
            gender: user.gender,
            occupation: user.occupation,
            news_sources: user.newsSources.isEmpty ? nil : user.newsSources,
            onboarded: user.onboarded
        )
        
        try await supabase
            .from("users")
            .insert(insert)
            .execute()
    }
    
    /// Save interest to Supabase database
    private func saveInterestToDatabase(_ interest: Interest, userId: String) async throws {
        guard let supabase = supabase else { return }
        
        struct InterestInsert: Codable {
            let id: String
            let user_id: String
            let name: String
            let category: String
            let is_active: Bool
        }
        
        let insert = InterestInsert(
            id: interest.id,
            user_id: userId,
            name: interest.name,
            category: interest.category.rawValue,
            is_active: interest.isActive
        )
        
        try await supabase
            .from("interests")
            .insert(insert)
            .execute()
    }
    
    /// Update user profile
    func updateUser(_ user: User) async throws {
        guard let supabase = supabase else {
            await MainActor.run {
                currentUser = user
            }
            return
        }
        
        print("💾 Updating user profile in database...")
        
        struct UserUpdate: Codable {
            let name: String
            let country: String?
            let age: Int?
            let gender: String?
            let occupation: String?
            let news_sources: [String]?
            let onboarded: Bool
        }
        
        // Update user table
        try await supabase
            .from("users")
            .update(UserUpdate(
                name: user.name,
                country: user.country,
                age: user.age,
                gender: user.gender,
                occupation: user.occupation,
                news_sources: user.newsSources.isEmpty ? nil : user.newsSources,
                onboarded: user.onboarded
            ))
            .eq("id", value: user.id)
            .execute()
        
        print("✅ User profile updated in database")
        
        await MainActor.run {
            currentUser = user
        }
    }
    
    // MARK: - Interest Management
    
    /// Get all user interests
    func getInterests() -> [Interest] {
        return currentUser?.interests ?? []
    }
    
    /// Add a new interest
    func addInterest(_ interest: Interest) async throws {
        guard let user = currentUser else { return }
        
        // Save to Supabase
        try await saveInterestToDatabase(interest, userId: user.id)
        
        // Update local state
        var interests = user.interests
        interests.append(interest)
        
        let updatedUser = User(
            id: user.id,
            name: user.name,
            email: user.email,
            country: user.country,
            age: user.age,
            gender: user.gender,
            occupation: user.occupation,
            newsSources: user.newsSources,
            interests: interests,
            dailyPodcastEnabled: user.dailyPodcastEnabled,
            dailyPodcastTime: user.dailyPodcastTime,
            onboarded: user.onboarded,
            createdAt: user.createdAt
        )
        
        await MainActor.run {
            currentUser = updatedUser
        }
    }
    
    /// Remove an interest
    func removeInterest(id: String) async throws {
        guard let user = currentUser, let supabase = supabase else { return }
        
        // Delete from Supabase
        try await supabase
            .from("interests")
            .delete()
            .eq("id", value: id)
            .execute()
        
        // Update local state
        var interests = user.interests
        interests.removeAll { $0.id == id }
        
        let updatedUser = User(
            id: user.id,
            name: user.name,
            email: user.email,
            country: user.country,
            age: user.age,
            gender: user.gender,
            occupation: user.occupation,
            newsSources: user.newsSources,
            interests: interests,
            dailyPodcastEnabled: user.dailyPodcastEnabled,
            dailyPodcastTime: user.dailyPodcastTime,
            onboarded: user.onboarded,
            createdAt: user.createdAt
        )
        
        await MainActor.run {
            currentUser = updatedUser
        }
    }
    
    /// Toggle interest active state
    func toggleInterest(id: String) async throws {
        guard let user = currentUser, let supabase = supabase else { return }
        
        var interests = user.interests
        guard let index = interests.firstIndex(where: { $0.id == id }) else { return }
        
        let interest = interests[index]
        let newActiveState = !interest.isActive
        
        // Update in Supabase
        struct InterestUpdate: Codable {
            let is_active: Bool
        }
        
        try await supabase
            .from("interests")
            .update(InterestUpdate(is_active: newActiveState))
            .eq("id", value: id)
            .execute()
        
        // Update local state
        interests[index] = Interest(
            id: interest.id,
            name: interest.name,
            category: interest.category,
            isActive: newActiveState,
            addedAt: interest.addedAt
        )
        
        let updatedUser = User(
            id: user.id,
            name: user.name,
            email: user.email,
            country: user.country,
            age: user.age,
            gender: user.gender,
            occupation: user.occupation,
            newsSources: user.newsSources,
            interests: interests,
            dailyPodcastEnabled: user.dailyPodcastEnabled,
            dailyPodcastTime: user.dailyPodcastTime,
            onboarded: user.onboarded,
            createdAt: user.createdAt
        )
        
        await MainActor.run {
            currentUser = updatedUser
        }
    }
    
    // MARK: - Playback State Management
    
    /// Save playback state
    func savePlaybackState(_ state: PlaybackState) {
        playbackStates[state.podcastId] = state
    }
    
    /// Get playback state for a podcast
    func getPlaybackState(for podcastId: String) -> PlaybackState? {
        return playbackStates[podcastId]
    }
    
    // MARK: - Settings
    
    /// Toggle daily podcast generation
    func toggleDailyPodcast() async throws {
        guard var user = currentUser else { return }
        
        let updatedUser = User(
            id: user.id,
            name: user.name,
            email: user.email,
            country: user.country,
            age: user.age,
            gender: user.gender,
            occupation: user.occupation,
            newsSources: user.newsSources,
            interests: user.interests,
            dailyPodcastEnabled: !user.dailyPodcastEnabled,
            dailyPodcastTime: user.dailyPodcastTime,
            onboarded: user.onboarded,
            createdAt: user.createdAt
        )
        
        try await updateUser(updatedUser)
    }
    
    /// Set daily podcast time
    func setDailyPodcastTime(_ time: Date) async throws {
        guard var user = currentUser else { return }
        
        let updatedUser = User(
            id: user.id,
            name: user.name,
            email: user.email,
            country: user.country,
            age: user.age,
            gender: user.gender,
            occupation: user.occupation,
            newsSources: user.newsSources,
            interests: user.interests,
            dailyPodcastEnabled: user.dailyPodcastEnabled,
            dailyPodcastTime: time,
            onboarded: user.onboarded,
            createdAt: user.createdAt
        )
        
        try await updateUser(updatedUser)
    }
    
    /// Mark user as having completed onboarding
    func markOnboarded() async throws {
        guard let user = currentUser else { return }
        
        let updatedUser = User(
            id: user.id,
            name: user.name,
            email: user.email,
            country: user.country,
            age: user.age,
            gender: user.gender,
            occupation: user.occupation,
            newsSources: user.newsSources,
            interests: user.interests,
            dailyPodcastEnabled: user.dailyPodcastEnabled,
            dailyPodcastTime: user.dailyPodcastTime,
            onboarded: true,
            createdAt: user.createdAt
        )
        
        try await updateUser(updatedUser)
    }
    
}

