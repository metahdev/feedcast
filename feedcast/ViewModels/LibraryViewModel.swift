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
    
    // MARK: - Private Properties
    private let podcastService = PodcastService.shared
    private var cancellables = Set<AnyCancellable>()
    
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
        podcastService.deletePodcast(id: podcast.id)
        podcasts.removeAll { $0.id == podcast.id }
    }
    
    func generateNewPodcast(interests: [Interest]) {
        Task {
            do {
                _ = try await podcastService.generatePodcast(interests: interests)
                await refreshPodcasts()
            } catch {
                self.error = error
            }
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

