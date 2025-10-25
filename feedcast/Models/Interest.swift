//
//  Interest.swift
//  feedcast
//
//  Data model for user interests used to personalize podcast content.
//  These will be sent to FetchAI for content generation.
//

import Foundation

/// Represents a user interest/topic for podcast personalization
struct Interest: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let category: InterestCategory
    let isActive: Bool
    let addedAt: Date
    
    init(
        id: String = UUID().uuidString,
        name: String,
        category: InterestCategory,
        isActive: Bool = true,
        addedAt: Date = Date()
    ) {
        self.id = id
        self.name = name
        self.category = category
        self.isActive = isActive
        self.addedAt = addedAt
    }
}

/// Categories for organizing interests
enum InterestCategory: String, Codable, CaseIterable {
    case technology = "Technology"
    case science = "Science"
    case business = "Business"
    case health = "Health"
    case arts = "Arts"
    case sports = "Sports"
    case politics = "Politics"
    case entertainment = "Entertainment"
    case education = "Education"
    case other = "Other"
    
    var emoji: String {
        switch self {
        case .technology: return "💻"
        case .science: return "🔬"
        case .business: return "💼"
        case .health: return "💪"
        case .arts: return "🎨"
        case .sports: return "⚽"
        case .politics: return "🏛️"
        case .entertainment: return "🎬"
        case .education: return "📚"
        case .other: return "✨"
        }
    }
}

