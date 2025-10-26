//
//  OpenAIService.swift
//  feedcast
//
//  Service for interacting with OpenAI API for GPT and TTS.
//

import Foundation

/// Service for OpenAI API integration
class OpenAIService {
    
    // MARK: - Singleton
    static let shared = OpenAIService()
    
    // MARK: - Constants
    private let baseURL = "https://api.openai.com/v1"
    private var apiKey: String {
        return Config.openAIAPIKey
    }
    
    private init() {}
    
    // MARK: - Models
    
    struct ChatMessage: Codable {
        let role: String
        let content: String
    }
    
    struct ChatRequest: Codable {
        let model: String
        let messages: [ChatMessage]
        let temperature: Double?
        let max_tokens: Int?
    }
    
    struct ChatResponse: Codable {
        let id: String
        let choices: [Choice]
        
        struct Choice: Codable {
            let message: ChatMessage
            let finish_reason: String?
        }
    }
    
    struct TTSRequest: Codable {
        let model: String
        let input: String
        let voice: String
        let response_format: String?
    }
    
    struct PodcastScript {
        let title: String
        let segments: [ScriptSegment]
    }
    
    struct ScriptSegment {
        let text: String
        let estimatedDuration: TimeInterval
    }
    
    // MARK: - Public Methods
    
    /// Generate a daily podcast script based on user interests and demographics
    func generateDailyPodcast(
        interests: [String],
        userInfo: UserDemographics,
        onProgress: @escaping (String) -> Void
    ) async throws -> PodcastScript {
        onProgress("Analyzing your interests...")
        
        let prompt = buildPrompt(interests: interests, userInfo: userInfo)
        
        onProgress("Generating podcast content...")
        
        let script = try await generateScript(prompt: prompt)
        
        return script
    }
    
    /// Convert text to speech using OpenAI TTS
    /// Handles long text by chunking into segments under 4096 character limit
    func textToSpeech(text: String, onProgress: @escaping (Double) -> Void) async throws -> Data {
        print("🎤 Starting TTS conversion...")
        print("🎤 Text length: \(text.count) characters")
        
        guard !apiKey.isEmpty else {
            print("❌ API key is empty")
            throw OpenAIError.invalidAPIKey
        }
        
        // OpenAI TTS has a 4096 character limit, so we need to chunk long text
        let maxChunkSize = 4000 // Leave some buffer
        
        if text.count <= maxChunkSize {
            // Text is short enough, process in one go
            print("✅ Text fits in single TTS request")
            return try await generateTTSForChunk(text: text, onProgress: onProgress)
        }
        
        // Text is too long, need to split into chunks
        print("⚠️ Text exceeds 4096 char limit, splitting into chunks...")
        let chunks = splitTextIntoChunks(text: text, maxSize: maxChunkSize)
        print("📦 Split into \(chunks.count) chunks")
        
        var allAudioData = Data()
        
        for (index, chunk) in chunks.enumerated() {
            print("🎤 Processing chunk \(index + 1)/\(chunks.count) (\(chunk.count) chars)")
            
            let chunkProgress = Double(index) / Double(chunks.count)
            onProgress(chunkProgress)
            
            let audioData = try await generateTTSForChunk(text: chunk) { _ in
                // Individual chunk progress
            }
            
            allAudioData.append(audioData)
            print("✅ Chunk \(index + 1) complete, total audio: \(allAudioData.count) bytes")
        }
        
        onProgress(1.0)
        print("✅ All chunks processed, total audio size: \(allAudioData.count) bytes")
        
        return allAudioData
    }
    
    /// Generate TTS for a single chunk of text
    private func generateTTSForChunk(text: String, onProgress: @escaping (Double) -> Void) async throws -> Data {
        let url = URL(string: "\(baseURL)/audio/speech")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let ttsRequest = TTSRequest(
            model: "tts-1",
            input: text,
            voice: "alloy",
            response_format: "mp3"
        )
        
        request.httpBody = try JSONEncoder().encode(ttsRequest)
        
        onProgress(0.1)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ Invalid HTTP response")
            throw OpenAIError.invalidResponse
        }
        
        guard httpResponse.statusCode == 200 else {
            let errorString = String(data: data, encoding: .utf8) ?? "Unknown error"
            print("❌ TTS Error (\(httpResponse.statusCode)): \(errorString)")
            throw OpenAIError.apiError(statusCode: httpResponse.statusCode, message: errorString)
        }
        
        onProgress(1.0)
        
        return data
    }
    
    /// Split text into chunks at natural boundaries (sentences/paragraphs)
    private func splitTextIntoChunks(text: String, maxSize: Int) -> [String] {
        var chunks: [String] = []
        var currentChunk = ""
        
        // Split by paragraphs first
        let paragraphs = text.components(separatedBy: "\n\n")
        
        for paragraph in paragraphs {
            // If adding this paragraph would exceed limit, save current chunk
            if !currentChunk.isEmpty && (currentChunk.count + paragraph.count + 2) > maxSize {
                chunks.append(currentChunk)
                currentChunk = ""
            }
            
            // If a single paragraph is too large, split by sentences
            if paragraph.count > maxSize {
                let sentences = splitParagraphIntoSentences(paragraph: paragraph, maxSize: maxSize)
                for sentence in sentences {
                    if !currentChunk.isEmpty && (currentChunk.count + sentence.count + 2) > maxSize {
                        chunks.append(currentChunk)
                        currentChunk = sentence
                    } else {
                        if !currentChunk.isEmpty {
                            currentChunk += "\n\n"
                        }
                        currentChunk += sentence
                    }
                }
            } else {
                if !currentChunk.isEmpty {
                    currentChunk += "\n\n"
                }
                currentChunk += paragraph
            }
        }
        
        // Add the last chunk
        if !currentChunk.isEmpty {
            chunks.append(currentChunk)
        }
        
        return chunks
    }
    
    /// Split a paragraph into sentences
    private func splitParagraphIntoSentences(paragraph: String, maxSize: Int) -> [String] {
        let sentenceEnders = CharacterSet(charactersIn: ".!?")
        var sentences: [String] = []
        var currentSentence = ""
        
        let words = paragraph.components(separatedBy: .whitespaces)
        
        for word in words {
            let testSentence = currentSentence.isEmpty ? word : currentSentence + " " + word
            
            if testSentence.count > maxSize {
                if !currentSentence.isEmpty {
                    sentences.append(currentSentence)
                }
                currentSentence = word
            } else {
                currentSentence = testSentence
                
                // Check if this word ends a sentence
                if let lastChar = word.last, sentenceEnders.contains(Unicode.Scalar(String(lastChar))!) {
                    sentences.append(currentSentence)
                    currentSentence = ""
                }
            }
        }
        
        // Add remaining text
        if !currentSentence.isEmpty {
            sentences.append(currentSentence)
        }
        
        return sentences
    }
    
    /// Generate transcript with timestamps based on text and duration
    func generateTranscript(text: String, totalDuration: TimeInterval) -> [TranscriptSegment] {
        // Split text into sentences
        let sentences = text.components(separatedBy: CharacterSet(charactersIn: ".!?"))
            .map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
            .filter { !$0.isEmpty }
        
        guard !sentences.isEmpty else { return [] }
        
        // Calculate approximate duration per character
        let totalCharacters = text.count
        let durationPerCharacter = totalDuration / Double(totalCharacters)
        
        var segments: [TranscriptSegment] = []
        var currentTime: TimeInterval = 0
        
        for sentence in sentences {
            let sentenceWithPunctuation = sentence + "."
            let duration = Double(sentenceWithPunctuation.count) * durationPerCharacter
            
            segments.append(TranscriptSegment(
                text: sentenceWithPunctuation,
                startTime: currentTime,
                endTime: currentTime + duration
            ))
            
            currentTime += duration
        }
        
        return segments
    }
    
    // MARK: - Private Methods
    
    private func buildPrompt(interests: [String], userInfo: UserDemographics) -> String {
        let interestsList = interests.joined(separator: ", ")
        let today = Date()
        let formatter = DateFormatter()
        formatter.dateFormat = "EEEE, MMMM d, yyyy"
        let dateString = formatter.string(from: today)
        
        return """
        You are a podcast host creating a personalized daily news and interest podcast.
        
        Today's Date: \(dateString)
        
        Audience Profile:
        - Gender: \(userInfo.gender)
        - Age: \(userInfo.age)
        - Country: \(userInfo.country)
        - Interests: \(interestsList)
        
        IMPORTANT: Start your response with a compelling title on the first line, formatted as:
        TITLE: [Your catchy podcast title here]
        
        The title should be:
        - Specific and engaging (not generic like "Daily Briefing")
        - Related to the main topics covered
        - Between 3-8 words
        - Exciting and clickable
        
        Examples of good titles:
        - "AI Breakthroughs Reshape Medicine"
        - "SpaceX's Mars Mission Takes Flight"
        - "Quantum Computing: The Next Frontier"
        - "Climate Tech Innovations Transform Energy"
        
        Then create an engaging 5-7 minute podcast script that:
        1. Starts with a warm, personalized greeting
        2. Covers the latest news and updates related to their interests
        3. Provides insights, analysis, or interesting facts
        4. Uses a conversational, engaging tone
        5. Ends with a thought-provoking conclusion or call-to-action
        
        Format: Start with "TITLE: [title]" on the first line, then your script.
        Write the script exactly as you would speak it, with natural transitions and personality.
        Aim for approximately 900-1200 words for a 5-7 minute podcast.
        """
    }
    
    private func generateScript(prompt: String) async throws -> PodcastScript {
        print("🤖 Generating script with GPT...")
        
        guard !apiKey.isEmpty else {
            print("❌ API key is empty")
            throw OpenAIError.invalidAPIKey
        }
        
        guard !apiKey.contains("YOUR_") else {
            print("❌ API key contains placeholder text")
            throw OpenAIError.invalidAPIKey
        }
        
        print("✅ API key looks valid (length: \(apiKey.count))")
        
        let url = URL(string: "\(baseURL)/chat/completions")!
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("Bearer \(apiKey)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        let chatRequest = ChatRequest(
            model: "gpt-4o",
            messages: [
                ChatMessage(role: "system", content: "You are an expert podcast host who creates engaging, personalized content."),
                ChatMessage(role: "user", content: prompt)
            ],
            temperature: 0.7,
            max_tokens: 2000
        )
        
        request.httpBody = try JSONEncoder().encode(chatRequest)
        print("📤 Sending request to OpenAI GPT API...")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse else {
            print("❌ Invalid HTTP response")
            throw OpenAIError.invalidResponse
        }
        
        print("📥 Received response with status code: \(httpResponse.statusCode)")
        
        guard httpResponse.statusCode == 200 else {
            let errorString = String(data: data, encoding: .utf8) ?? "Unknown error"
            print("❌ GPT Error (\(httpResponse.statusCode)): \(errorString)")
            throw OpenAIError.apiError(statusCode: httpResponse.statusCode, message: errorString)
        }
        
        let chatResponse: ChatResponse
        do {
            chatResponse = try JSONDecoder().decode(ChatResponse.self, from: data)
            print("✅ Successfully decoded GPT response")
        } catch {
            print("❌ Failed to decode GPT response: \(error)")
            let responseString = String(data: data, encoding: .utf8) ?? "Unable to decode"
            print("❌ Raw response: \(responseString)")
            throw error
        }
        
        guard let scriptText = chatResponse.choices.first?.message.content else {
            print("❌ GPT response has no content")
            throw OpenAIError.emptyResponse
        }
        
        print("✅ Got script text (length: \(scriptText.count) characters)")
        
        // Parse script into segments
        let paragraphs = scriptText.components(separatedBy: "\n\n")
            .filter { !$0.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty }
        
        let segments = paragraphs.map { paragraph in
            let wordCount = paragraph.components(separatedBy: .whitespaces).count
            // Average speaking rate: 150 words per minute
            let estimatedDuration = Double(wordCount) / 150.0 * 60.0
            return ScriptSegment(text: paragraph, estimatedDuration: estimatedDuration)
        }
        
        // Generate title from first line or create one
        let title = generateTitle(from: scriptText)
        
        return PodcastScript(title: title, segments: segments)
    }
    
    private func generateTitle(from text: String) -> String {
        let lines = text.components(separatedBy: .newlines)
        
        // Look for "TITLE: " prefix
        for line in lines.prefix(3) { // Check first 3 lines
            let trimmed = line.trimmingCharacters(in: .whitespacesAndNewlines)
            if trimmed.hasPrefix("TITLE:") {
                let title = trimmed.replacingOccurrences(of: "TITLE:", with: "")
                    .trimmingCharacters(in: .whitespacesAndNewlines)
                if !title.isEmpty && title.count < 100 {
                    print("📰 Extracted title: \(title)")
                    return title
                }
            }
        }
        
        // Fallback: use first line if reasonable
        if let firstLine = lines.first?.trimmingCharacters(in: .whitespacesAndNewlines),
           !firstLine.isEmpty,
           firstLine.count < 100,
           !firstLine.contains("Welcome") {
            return firstLine
        }
        
        // Generate a default title with current date
        let formatter = DateFormatter()
        formatter.dateFormat = "MMMM d"
        return "Daily Podcast - \(formatter.string(from: Date()))"
    }
}

// MARK: - Supporting Types

struct UserDemographics {
    let gender: String
    let age: Int
    let country: String
}

struct TranscriptSegment: Codable {
    let text: String
    let startTime: TimeInterval
    let endTime: TimeInterval
}

enum OpenAIError: LocalizedError {
    case invalidAPIKey
    case invalidResponse
    case apiError(statusCode: Int, message: String)
    case emptyResponse
    
    var errorDescription: String? {
        switch self {
        case .invalidAPIKey:
            return "Invalid OpenAI API key"
        case .invalidResponse:
            return "Invalid response from OpenAI"
        case .apiError(let statusCode, let message):
            return "OpenAI API error (\(statusCode)): \(message)"
        case .emptyResponse:
            return "Empty response from OpenAI"
        }
    }
}

