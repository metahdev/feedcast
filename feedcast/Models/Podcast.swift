//
//  Podcast.swift
//  feedcast
//
//  Data model representing an AI-generated personalized podcast.
//  Each podcast can contain multiple episodes and is generated based on user interests.
//

import Foundation

/// Represents a personalized AI-generated podcast
struct Podcast: Identifiable, Codable, Hashable {
    let id: String
    let title: String
    let description: String
    let coverImageURL: String?
    let interests: [String] // Related user interests
    let episodes: [Episode]
    let createdAt: Date
    let isDaily: Bool // Whether this is a daily generated podcast
    
    init(
        id: String = UUID().uuidString,
        title: String,
        description: String,
        coverImageURL: String? = nil,
        interests: [String] = [],
        episodes: [Episode] = [],
        createdAt: Date = Date(),
        isDaily: Bool = false
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.coverImageURL = coverImageURL
        self.interests = interests
        self.episodes = episodes
        self.createdAt = createdAt
        self.isDaily = isDaily
    }
    
    /// Total duration of all episodes in seconds
    var totalDuration: TimeInterval {
        episodes.reduce(0) { $0 + $1.duration }
    }
    
    /// Formatted duration string
    var formattedDuration: String {
        let minutes = Int(totalDuration) / 60
        if minutes < 60 {
            return "\(minutes) min"
        } else {
            let hours = minutes / 60
            let remainingMinutes = minutes % 60
            return remainingMinutes > 0 ? "\(hours)h \(remainingMinutes)m" : "\(hours)h"
        }
    }
}

/// Represents an individual episode within a podcast
struct Episode: Identifiable, Codable, Hashable {
    let id: String
    let title: String
    let description: String
    let duration: TimeInterval // in seconds
    let audioURL: String? // Will be populated by backend/LiveKit
    let transcript: String?
    let createdAt: Date
    
    init(
        id: String = UUID().uuidString,
        title: String,
        description: String,
        duration: TimeInterval,
        audioURL: String? = nil,
        transcript: String? = nil,
        createdAt: Date = Date()
    ) {
        self.id = id
        self.title = title
        self.description = description
        self.duration = duration
        self.audioURL = audioURL
        self.transcript = transcript
        self.createdAt = createdAt
    }
    
    /// Formatted duration string (MM:SS)
    var formattedDuration: String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }
}

