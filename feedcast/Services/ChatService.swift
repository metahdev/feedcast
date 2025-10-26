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
import Supabase

/// Service for managing chat functionality
class ChatService: ObservableObject {
    
    // MARK: - Singleton
    static let shared = ChatService()
    
    // MARK: - Published Properties
    @Published var conversations: [String: Conversation] = [:] // podcastId -> Conversation
    @Published var isProcessing = false
    
    // MARK: - Private Properties
    private var cancellables = Set<AnyCancellable>()
    private var supabase: SupabaseClient? {
        guard Config.isSupabaseConfigured else { return nil }
        return SupabaseManager.shared.client
    }
    
    private init() {
        // Don't load dummy data - fetch from Supabase when needed
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
    
    /// Load conversation from Supabase
    func loadConversation(for podcastId: String) async throws {
        guard let supabase = supabase else { return }
        
        struct MessageResponse: Codable {
            let id: String
            let podcast_id: String
            let episode_id: String?
            let user_id: String
            let content: String
            let sender: String
            let timestamp: String
        }
        
        let messagesData: [MessageResponse] = try await supabase
            .from("chat_messages")
            .select()
            .eq("podcast_id", value: podcastId)
            .order("timestamp", ascending: true)
            .execute()
            .value
        
        let messages = messagesData.map { data in
            ChatMessage(
                id: data.id,
                podcastId: data.podcast_id,
                episodeId: data.episode_id,
                content: data.content,
                sender: MessageSender(rawValue: data.sender) ?? .user,
                timestamp: ISO8601DateFormatter().date(from: data.timestamp) ?? Date(),
                isTyping: false
            )
        }
        
        let conversation = Conversation(
            podcastId: podcastId,
            messages: messages,
            lastUpdated: messages.last?.timestamp ?? Date()
        )
        
        await MainActor.run {
            conversations[podcastId] = conversation
        }
    }
    
    /// Send a message and get AI response
    /// TODO: Integrate with FetchAI for intelligent responses
    func sendMessage(
        podcastId: String,
        episodeId: String?,
        content: String,
        podcast: Podcast?
    ) async throws -> ChatMessage {
        guard let supabase = supabase else {
            throw NSError(domain: "ChatService", code: 500, userInfo: [NSLocalizedDescriptionKey: "Supabase not configured"])
        }
        
        guard let userId = UserService.shared.currentUser?.id else {
            throw NSError(domain: "ChatService", code: 401, userInfo: [NSLocalizedDescriptionKey: "User not authenticated"])
        }
        
        // Create user message
        let userMessage = ChatMessage(
            podcastId: podcastId,
            episodeId: episodeId,
            content: content,
            sender: .user
        )
        
        // Save user message to Supabase
        try await saveMessage(userMessage, userId: userId)
        
        // Update local state
        await MainActor.run {
            var conversation = getConversation(for: podcastId)
            conversation.messages.append(userMessage)
            conversations[podcastId] = conversation
            isProcessing = true
        }
        
        // Generate AI response with podcast context
        isProcessing = true
        let aiResponse: String
        if let podcast = podcast {
            aiResponse = try await generateAIResponse(for: content, podcast: podcast, podcastId: podcastId)
        } else {
            aiResponse = "I'm sorry, I don't have enough context about this podcast to answer your question properly."
        }
        let aiMessage = ChatMessage(
            podcastId: podcastId,
            episodeId: episodeId,
            content: aiResponse,
            sender: .ai
        )
        
        // Save AI message to Supabase
        try await saveMessage(aiMessage, userId: userId)
        
        // Update local state
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
    
    /// Save a message to Supabase
    private func saveMessage(_ message: ChatMessage, userId: String) async throws {
        guard let supabase = supabase else { return }
        
        struct MessageInsert: Codable {
            let id: String
            let podcast_id: String
            let episode_id: String?
            let user_id: String
            let content: String
            let sender: String
        }
        
        let messageInsert = MessageInsert(
            id: message.id,
            podcast_id: message.podcastId,
            episode_id: message.episodeId,
            user_id: userId,
            content: message.content,
            sender: message.sender.rawValue
        )
        
        try await supabase
            .from("chat_messages")
            .insert(messageInsert)
            .execute()
    }
    
    /// Clear conversation for a podcast
    func clearConversation(for podcastId: String) async throws {
        guard let supabase = supabase else { return }
        
        // Delete from Supabase
        try await supabase
            .from("chat_messages")
            .delete()
            .eq("podcast_id", value: podcastId)
            .execute()
        
        // Update local state
        await MainActor.run {
            conversations[podcastId] = Conversation(podcastId: podcastId)
        }
    }
    
    // MARK: - Private Methods
    
    /// Generate AI response using OpenAI with full podcast context
    private func generateAIResponse(for userMessage: String, podcast: Podcast, podcastId: String) async throws -> String {
        // Build context from podcast and conversation history
        let conversation = getConversation(for: podcastId)
        let context = buildPodcastContext(podcast: podcast, conversation: conversation)
        
        // Check if OpenAI is configured
        guard Config.isOpenAIConfigured else {
            print("⚠️ OpenAI not configured, using fallback response")
            return generateDummyResponse(for: userMessage, podcast: podcast)
        }
        
        do {
            return try await callOpenAI(userMessage: userMessage, context: context)
        } catch {
            print("❌ OpenAI chat failed: \(error), using fallback")
            return generateDummyResponse(for: userMessage, podcast: podcast)
        }
    }
    
    /// Build context from podcast and conversation
    private func buildPodcastContext(podcast: Podcast, conversation: Conversation) -> String {
        var context = """
        You are an AI assistant helping users understand and discuss a podcast.
        
        Podcast Information:
        - Title: \(podcast.title)
        - Description: \(podcast.description)
        - Topics: \(podcast.interests.joined(separator: ", "))
        
        """
        
        // Add transcript if available
        if let episode = podcast.episodes.first,
           let transcript = episode.transcript,
           !transcript.isEmpty {
            context += "\nPodcast Content:\n\(transcript.prefix(2000))\n"
        }
        
        // Add recent conversation history
        let recentMessages = conversation.messages.suffix(6).dropLast() // Last 6 messages, excluding current
        if !recentMessages.isEmpty {
            context += "\nConversation History:\n"
            for msg in recentMessages {
                context += "\(msg.sender == .user ? "User" : "AI"): \(msg.content)\n"
            }
        }
        
        context += """
        
        Instructions:
        - Answer based on the podcast content
        - Be conversational and helpful
        - Keep responses 2-3 paragraphs max
        - If asked about something not in the podcast, acknowledge it but still provide helpful information
        """
        
        return context
    }
    
    /// Call OpenAI API
    private func callOpenAI(userMessage: String, context: String) async throws -> String {
        let url = URL(string: "https://api.openai.com/v1/chat/completions")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(Config.openAIAPIKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let messages: [[String: String]] = [
            ["role": "system", "content": context],
            ["role": "user", "content": userMessage]
        ]
        
        let body: [String: Any] = [
            "model": "gpt-4o",
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 400
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, _) = try await URLSession.shared.data(for: request)
        
        struct ChatResponse: Codable {
            struct Choice: Codable {
                struct Message: Codable {
                    let content: String
                }
                let message: Message
            }
            let choices: [Choice]
        }
        
        let response = try JSONDecoder().decode(ChatResponse.self, from: data)
        
        guard let content = response.choices.first?.message.content else {
            throw NSError(domain: "ChatService", code: 500, userInfo: [NSLocalizedDescriptionKey: "No response"])
        }
        
        return content
    }
    
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
    
}

