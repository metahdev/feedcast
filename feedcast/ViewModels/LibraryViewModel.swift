//
//  LibraryViewModel.swift
//  feedcast
//
//  ViewModel for the main library/home view displaying all podcasts.
//

import Foundation
import Combine

@MainActor
class LibraryViewModel: ObservableObject {
    
    // MARK: - Published Properties
    @Published var podcasts: [Podcast] = []
    @Published var isLoading = false
    @Published var error: Error?
    @Published var searchText = ""
    @Published var sortOption: SortOption = .newest
    @Published var generationProgress: String?
    @Published var isGeneratingPodcast = false
    
    // MARK: - Private Properties
    private let podcastService = PodcastService.shared
    private var cancellables = Set<AnyCancellable>()
    private var hasCheckedForEmptyLibrary = false
    
    // MARK: - Computed Properties
    
    var filteredPodcasts: [Podcast] {
        var filtered = podcasts
        
        // Filter by search text
        if !searchText.isEmpty {
            filtered = filtered.filter { podcast in
                podcast.title.localizedCaseInsensitiveContains(searchText) ||
                podcast.description.localizedCaseInsensitiveContains(searchText) ||
                podcast.interests.contains { $0.localizedCaseInsensitiveContains(searchText) }
            }
        }
        
        // Sort
        switch sortOption {
        case .newest:
            return filtered.sorted { $0.createdAt > $1.createdAt }
        case .oldest:
            return filtered.sorted { $0.createdAt < $1.createdAt }
        case .duration:
            return filtered.sorted { $0.totalDuration > $1.totalDuration }
        case .title:
            return filtered.sorted { $0.title < $1.title }
        }
    }
    
    var dailyPodcast: Podcast? {
        podcasts.first { $0.isDaily }
    }
    
    var recentPodcasts: [Podcast] {
        Array(filteredPodcasts.prefix(10))
    }
    
    // MARK: - Initialization
    
    init() {
        setupBindings()
        loadPodcasts()
    }
    
    // MARK: - Public Methods
    
    func loadPodcasts() {
        Task {
            isLoading = true
            defer { isLoading = false }
            
            do {
                podcasts = try await podcastService.fetchPodcasts()
                
                // Check if library is empty and auto-generate if needed
                if podcasts.isEmpty && !hasCheckedForEmptyLibrary {
                    hasCheckedForEmptyLibrary = true
                    await generateDailyPodcastIfNeeded()
                }
            } catch {
                self.error = error
            }
        }
    }
    
    func refreshPodcasts() async {
        do {
            podcasts = try await podcastService.fetchPodcasts()
        } catch {
            self.error = error
        }
    }
    
    func deletePodcast(_ podcast: Podcast) {
        Task {
            do {
                try await podcastService.deletePodcast(id: podcast.id)
                podcasts.removeAll { $0.id == podcast.id }
            } catch {
                self.error = error
            }
        }
    }
    
    func generateNewPodcast(interests: [Interest]) {
        Task {
            isGeneratingPodcast = true
            defer { isGeneratingPodcast = false }
            
            do {
                _ = try await podcastService.generatePodcast(
                    interests: interests,
                    isDaily: false,
                    onProgress: { [weak self] progress in
                        Task { @MainActor in
                            self?.generationProgress = progress
                        }
                    }
                )
                await refreshPodcasts()
            } catch {
                self.error = error
            }
        }
    }
    
    /// Auto-generate a daily podcast based on user's interests
    private func generateDailyPodcastIfNeeded() async {
        // Get user interests
        let userInterests = UserService.shared.getInterests().filter { $0.isActive }
        
        print("📊 Debug: Found \(userInterests.count) active interests")
        print("📊 Debug: User authenticated: \(UserService.shared.isAuthenticated)")
        print("📊 Debug: Current user: \(UserService.shared.currentUser?.email ?? "nil")")
        
        guard !userInterests.isEmpty else {
            print("⚠️ No active interests found. Skipping auto-generation.")
            print("💡 Tip: Make sure you selected interests during onboarding")
            return
        }
        
        guard UserService.shared.isAuthenticated else {
            print("⚠️ User not authenticated. Skipping auto-generation.")
            return
        }
        
        print("📻 Library is empty. Auto-generating daily podcast...")
        print("📻 Using interests: \(userInterests.map { $0.name }.joined(separator: ", "))")
        
        isGeneratingPodcast = true
        generationProgress = "Welcome! Preparing your first podcast..."
        
        defer {
            isGeneratingPodcast = false
            generationProgress = nil
        }
        
        do {
            _ = try await podcastService.generatePodcast(
                interests: userInterests,
                isDaily: true,
                onProgress: { [weak self] progress in
                    Task { @MainActor in
                        print("📡 Progress: \(progress)")
                        self?.generationProgress = progress
                    }
                }
            )
            
            // Refresh the podcast list
            await refreshPodcasts()
            
            print("✅ Daily podcast generated successfully!")
        } catch {
            print("❌ Failed to auto-generate podcast: \(error)")
            print("❌ Error details: \(error.localizedDescription)")
            if let nsError = error as NSError? {
                print("❌ Error domain: \(nsError.domain)")
                print("❌ Error code: \(nsError.code)")
                print("❌ Error userInfo: \(nsError.userInfo)")
            }
            self.error = error
        }
    }
    
    // MARK: - Private Methods
    
    private func setupBindings() {
        podcastService.$podcasts
            .assign(to: &$podcasts)
    }
}

// MARK: - Supporting Types

enum SortOption: String, CaseIterable {
    case newest = "Newest First"
    case oldest = "Oldest First"
    case duration = "Longest First"
    case title = "A to Z"
}

