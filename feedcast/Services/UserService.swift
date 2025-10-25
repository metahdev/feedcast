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

/// Service for managing user data and preferences
class UserService: ObservableObject {
    
    // MARK: - Singleton
    static let shared = UserService()
    
    // MARK: - Published Properties
    @Published var currentUser: User?
    @Published var playbackStates: [String: PlaybackState] = [:] // podcastId -> PlaybackState
    
    // MARK: - Private Properties
    private var cancellables = Set<AnyCancellable>()
    
    private init() {
        loadDummyUser()
    }
    
    // MARK: - User Management
    
    /// Load user profile
    /// TODO: Integrate with Supabase Auth
    func loadUser() async throws -> User {
        // Simulate network delay
        try await Task.sleep(nanoseconds: 300_000_000)
        
        guard let user = currentUser else {
            throw NSError(domain: "UserService", code: 404, userInfo: [NSLocalizedDescriptionKey: "User not found"])
        }
        
        return user
    }
    
    /// Update user profile
    func updateUser(_ user: User) async throws {
        try await Task.sleep(nanoseconds: 300_000_000)
        
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
        guard var user = currentUser else { return }
        
        var interests = user.interests
        interests.append(interest)
        
        let updatedUser = User(
            id: user.id,
            name: user.name,
            email: user.email,
            interests: interests,
            dailyPodcastEnabled: user.dailyPodcastEnabled,
            dailyPodcastTime: user.dailyPodcastTime,
            createdAt: user.createdAt
        )
        
        try await updateUser(updatedUser)
    }
    
    /// Remove an interest
    func removeInterest(id: String) async throws {
        guard var user = currentUser else { return }
        
        var interests = user.interests
        interests.removeAll { $0.id == id }
        
        let updatedUser = User(
            id: user.id,
            name: user.name,
            email: user.email,
            interests: interests,
            dailyPodcastEnabled: user.dailyPodcastEnabled,
            dailyPodcastTime: user.dailyPodcastTime,
            createdAt: user.createdAt
        )
        
        try await updateUser(updatedUser)
    }
    
    /// Toggle interest active state
    func toggleInterest(id: String) async throws {
        guard var user = currentUser else { return }
        
        var interests = user.interests
        if let index = interests.firstIndex(where: { $0.id == id }) {
            let interest = interests[index]
            interests[index] = Interest(
                id: interest.id,
                name: interest.name,
                category: interest.category,
                isActive: !interest.isActive,
                addedAt: interest.addedAt
            )
        }
        
        let updatedUser = User(
            id: user.id,
            name: user.name,
            email: user.email,
            interests: interests,
            dailyPodcastEnabled: user.dailyPodcastEnabled,
            dailyPodcastTime: user.dailyPodcastTime,
            createdAt: user.createdAt
        )
        
        try await updateUser(updatedUser)
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
            interests: user.interests,
            dailyPodcastEnabled: !user.dailyPodcastEnabled,
            dailyPodcastTime: user.dailyPodcastTime,
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
            interests: user.interests,
            dailyPodcastEnabled: user.dailyPodcastEnabled,
            dailyPodcastTime: time,
            createdAt: user.createdAt
        )
        
        try await updateUser(updatedUser)
    }
    
    // MARK: - Private Methods
    
    private func loadDummyUser() {
        currentUser = User(
            name: "Demo User",
            email: "demo@feedcast.app",
            interests: [
                Interest(name: "Artificial Intelligence", category: .technology),
                Interest(name: "Machine Learning", category: .technology),
                Interest(name: "Space Exploration", category: .science),
                Interest(name: "Startup Strategy", category: .business),
                Interest(name: "Fitness & Nutrition", category: .health),
                Interest(name: "Climate Change", category: .science)
            ],
            dailyPodcastEnabled: true,
            dailyPodcastTime: Calendar.current.date(bySettingHour: 8, minute: 0, second: 0, of: Date())
        )
    }
}

