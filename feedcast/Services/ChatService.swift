//
//  ChatService.swift
//  feedcast
//
//  Service layer for managing chat conversations with AI podcast assistant.
//
//  FUTURE INTEGRATION NOTES:
//  - Integrate FetchAI for intelligent podcast-aware responses
//  - Add context from podcast transcript for better answers
//  - Implement streaming responses for better UX
//  - Store conversations in Supabase
//

import Foundation
import Combine

/// Service for managing chat functionality
class ChatService: ObservableObject {
    
    // MARK: - Singleton
    static let shared = ChatService()
    
    // MARK: - Published Properties
    @Published var conversations: [String: Conversation] = [:] // podcastId -> Conversation
    @Published var isProcessing = false
    
    // MARK: - Private Properties
    private var cancellables = Set<AnyCancellable>()
    
    private init() {
        loadDummyConversations()
    }
    
    // MARK: - Public Methods
    
    /// Get conversation for a specific podcast
    func getConversation(for podcastId: String) -> Conversation {
        if let existing = conversations[podcastId] {
            return existing
        }
        
        let newConversation = Conversation(podcastId: podcastId)
        conversations[podcastId] = newConversation
        return newConversation
    }
    
    /// Send a message and get AI response
    /// TODO: Integrate with FetchAI for intelligent responses
    func sendMessage(
        podcastId: String,
        episodeId: String?,
        content: String,
        podcast: Podcast?
    ) async throws -> ChatMessage {
        
        // Add user message
        let userMessage = ChatMessage(
            podcastId: podcastId,
            episodeId: episodeId,
            content: content,
            sender: .user
        )
        
        await MainActor.run {
            var conversation = getConversation(for: podcastId)
            conversation.messages.append(userMessage)
            conversations[podcastId] = conversation
            isProcessing = true
        }
        
        // Simulate AI processing
        try await Task.sleep(nanoseconds: 1_500_000_000)
        
        // Generate AI response (dummy logic)
        let aiResponse = generateDummyResponse(for: content, podcast: podcast)
        let aiMessage = ChatMessage(
            podcastId: podcastId,
            episodeId: episodeId,
            content: aiResponse,
            sender: .ai
        )
        
        await MainActor.run {
            var conversation = getConversation(for: podcastId)
            conversation.messages.append(aiMessage)
            conversations[podcastId] = Conversation(
                id: conversation.id,
                podcastId: conversation.podcastId,
                messages: conversation.messages,
                lastUpdated: Date()
            )
            isProcessing = false
        }
        
        return aiMessage
    }
    
    /// Clear conversation for a podcast
    func clearConversation(for podcastId: String) {
        conversations[podcastId] = Conversation(podcastId: podcastId)
    }
    
    // MARK: - Private Methods
    
    private func generateDummyResponse(for message: String, podcast: Podcast?) -> String {
        let lowercased = message.lowercased()
        
        if lowercased.contains("summary") || lowercased.contains("summarize") {
            return "This podcast covers \(podcast?.interests.joined(separator: ", ") ?? "various topics") with \(podcast?.episodes.count ?? 0) episodes. The main themes include cutting-edge developments and insights tailored to your interests."
        } else if lowercased.contains("what") || lowercased.contains("explain") {
            return "Based on the podcast content, this topic explores the intersection of your selected interests. Each episode is designed to provide deep insights while remaining engaging and accessible."
        } else if lowercased.contains("how long") || lowercased.contains("duration") {
            return "The total duration of this podcast is \(podcast?.formattedDuration ?? "unknown"). You can listen at your own pace and resume anytime."
        } else if lowercased.contains("when") {
            return "This podcast was generated on \(formatDate(podcast?.createdAt)). Daily podcasts are created based on your preferences and the latest information."
        } else {
            return "That's an interesting question about this podcast! The content is personalized based on your interests in \(podcast?.interests.prefix(2).joined(separator: " and ") ?? "various topics"). Feel free to ask me anything about the episodes or topics covered."
        }
    }
    
    private func formatDate(_ date: Date?) -> String {
        guard let date = date else { return "recently" }
        let formatter = DateFormatter()
        formatter.dateStyle = .medium
        formatter.timeStyle = .short
        return formatter.string(from: date)
    }
    
    private func loadDummyConversations() {
        // Load some example conversations
        let exampleMessages = [
            ChatMessage(
                podcastId: "1",
                content: "What is this podcast about?",
                sender: .user,
                timestamp: Date().addingTimeInterval(-300)
            ),
            ChatMessage(
                podcastId: "1",
                content: "This podcast covers your interests in Technology, AI, and Innovation with 2 episodes focused on recent breakthroughs and industry trends.",
                sender: .ai,
                timestamp: Date().addingTimeInterval(-290)
            )
        ]
        
        conversations["1"] = Conversation(
            podcastId: "1",
            messages: exampleMessages,
            lastUpdated: Date().addingTimeInterval(-290)
        )
    }
}

