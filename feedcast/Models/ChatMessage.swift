//
//  ChatMessage.swift
//  feedcast
//
//  Data model for chat messages between user and AI podcast assistant.
//  Chat is contextual to the currently playing podcast/episode.
//

import Foundation

/// Represents a chat message in the podcast conversation
struct ChatMessage: Identifiable, Codable, Hashable {
    let id: String
    let podcastId: String
    let episodeId: String?
    let content: String
    let sender: MessageSender
    let timestamp: Date
    let isTyping: Bool // For AI typing indicator
    
    init(
        id: String = UUID().uuidString,
        podcastId: String,
        episodeId: String? = nil,
        content: String,
        sender: MessageSender,
        timestamp: Date = Date(),
        isTyping: Bool = false
    ) {
        self.id = id
        self.podcastId = podcastId
        self.episodeId = episodeId
        self.content = content
        self.sender = sender
        self.timestamp = timestamp
        self.isTyping = isTyping
    }
}

/// Sender type for chat messages
enum MessageSender: String, Codable {
    case user = "user"
    case ai = "ai"
}

/// Conversation context for a podcast
struct Conversation: Identifiable, Codable {
    let id: String
    let podcastId: String
    let messages: [ChatMessage]
    let lastUpdated: Date
    
    init(
        id: String = UUID().uuidString,
        podcastId: String,
        messages: [ChatMessage] = [],
        lastUpdated: Date = Date()
    ) {
        self.id = id
        self.podcastId = podcastId
        self.messages = messages
        self.lastUpdated = lastUpdated
    }
}

