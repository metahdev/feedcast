//
//  User.swift
//  feedcast
//
//  User profile model for storing preferences and settings.
//  Will be synced with Supabase backend in future.
//

import Foundation

/// Represents the app user
struct User: Identifiable, Codable {
    let id: String
    let name: String
    let email: String
    let interests: [Interest]
    let dailyPodcastEnabled: Bool
    let dailyPodcastTime: Date? // Preferred time for daily podcast
    let createdAt: Date
    
    init(
        id: String = UUID().uuidString,
        name: String,
        email: String,
        interests: [Interest] = [],
        dailyPodcastEnabled: Bool = true,
        dailyPodcastTime: Date? = nil,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.email = email
        self.interests = interests
        self.dailyPodcastEnabled = dailyPodcastEnabled
        self.dailyPodcastTime = dailyPodcastTime
        self.createdAt = createdAt
    }
}

/// User playback state for resuming podcasts
struct PlaybackState: Codable {
    let podcastId: String
    let episodeId: String
    let currentTime: TimeInterval
    let lastPlayed: Date
    
    init(
        podcastId: String,
        episodeId: String,
        currentTime: TimeInterval,
        lastPlayed: Date = Date()
    ) {
        self.podcastId = podcastId
        self.episodeId = episodeId
        self.currentTime = currentTime
        self.lastPlayed = lastPlayed
    }
}

