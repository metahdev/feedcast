//
//  PodcastService.swift
//  feedcast
//
//  Service layer for podcast data management.
//
//  FUTURE INTEGRATION NOTES:
//  - Replace dummy data with Supabase queries
//  - Integrate FetchAI for podcast content generation
//  - Implement LiveKit for real-time audio streaming
//  - Add caching layer for offline support
//

import Foundation
import Combine
import Supabase

/// Service for managing podcast data and operations
class PodcastService: ObservableObject {
    
    // MARK: - Singleton
    static let shared = PodcastService()
    
    // MARK: - Published Properties
    @Published var podcasts: [Podcast] = []
    @Published var isLoading = false
    @Published var error: Error?
    
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
    
    /// Fetch all podcasts for the current user
    func fetchPodcasts() async throws -> [Podcast] {
        guard let supabase = supabase else {
            throw NSError(domain: "PodcastService", code: 500, userInfo: [NSLocalizedDescriptionKey: "Supabase not configured"])
        }
        
        guard let userId = UserService.shared.currentUser?.id else {
            throw NSError(domain: "PodcastService", code: 401, userInfo: [NSLocalizedDescriptionKey: "User not authenticated"])
        }
        
        isLoading = true
        defer { isLoading = false }
        
        // Fetch podcasts from Supabase
        struct PodcastResponse: Codable {
            let id: String
            let user_id: String
            let title: String
            let description: String?
            let interests: [String]
            let is_daily: Bool
            let created_at: String
        }
        
        let podcastsData: [PodcastResponse] = try await supabase
            .from("podcasts")
            .select()
            .eq("user_id", value: userId)
            .order("created_at", ascending: false)
            .execute()
            .value
        
        // Fetch episodes for each podcast
        var fetchedPodcasts: [Podcast] = []
        
        for podcastData in podcastsData {
            let episodes = try await fetchEpisodes(for: podcastData.id)
            
            let podcast = Podcast(
                id: podcastData.id,
                title: podcastData.title,
                description: podcastData.description ?? "",
                coverImageURL: nil,
                interests: podcastData.interests,
                episodes: episodes,
                createdAt: ISO8601DateFormatter().date(from: podcastData.created_at) ?? Date(),
                isDaily: podcastData.is_daily
            )
            
            fetchedPodcasts.append(podcast)
        }
        
        await MainActor.run {
            podcasts = fetchedPodcasts
        }
        
        return fetchedPodcasts
    }
    
    /// Fetch episodes for a specific podcast
    private func fetchEpisodes(for podcastId: String) async throws -> [Episode] {
        guard let supabase = supabase else { return [] }
        
        struct EpisodeResponse: Codable {
            let id: String
            let title: String
            let description: String?
            let duration: Double
            let audio_url: String?
            let transcript: String?
            let created_at: String
        }
        
        let episodesData: [EpisodeResponse] = try await supabase
            .from("episodes")
            .select()
            .eq("podcast_id", value: podcastId)
            .order("created_at", ascending: true)
            .execute()
            .value
        
        return episodesData.map { data in
            Episode(
                id: data.id,
                title: data.title,
                description: data.description ?? "",
                duration: data.duration,
                audioURL: data.audio_url,
                transcript: data.transcript,
                createdAt: ISO8601DateFormatter().date(from: data.created_at) ?? Date()
            )
        }
    }
    
    /// Get a specific podcast by ID
    func getPodcast(by id: String) -> Podcast? {
        return podcasts.first { $0.id == id }
    }
    
    /// Request a new AI-generated podcast based on user interests
    func generatePodcast(
        interests: [Interest],
        prompt: String? = nil,
        isDaily: Bool = false,
        onProgress: ((String) -> Void)? = nil
    ) async throws -> Podcast {
        print("🎙️ Starting podcast generation...")
        print("🎙️ Interests: \(interests.map { $0.name }.joined(separator: ", "))")
        print("🎙️ Is daily: \(isDaily)")
        
        guard let supabase = supabase else {
            print("❌ Supabase not configured")
            throw NSError(domain: "PodcastService", code: 500, userInfo: [NSLocalizedDescriptionKey: "Supabase not configured"])
        }
        
        guard let userId = UserService.shared.currentUser?.id else {
            print("❌ User not authenticated")
            throw NSError(domain: "PodcastService", code: 401, userInfo: [NSLocalizedDescriptionKey: "User not authenticated"])
        }
        
        guard Config.isOpenAIConfigured else {
            print("❌ OpenAI not configured")
            print("❌ API Key check: isEmpty=\(Config.openAIAPIKey.isEmpty), contains YOUR=\(Config.openAIAPIKey.contains("YOUR_"))")
            throw NSError(domain: "PodcastService", code: 500, userInfo: [NSLocalizedDescriptionKey: "OpenAI not configured"])
        }
        
        print("✅ All checks passed, proceeding with generation")
        
        isLoading = true
        defer { isLoading = false }
        
        onProgress?("Initializing podcast generation...")
        
        // Get user demographics
        let user = UserService.shared.currentUser
        let userInfo = UserDemographics(
            gender: user?.gender ?? "male",
            age: user?.age ?? 22,
            country: user?.country ?? "United States"
        )
        
        print("👤 User demographics: \(userInfo.gender), \(userInfo.age), \(userInfo.country)")
        
        // Generate podcast script using OpenAI
        onProgress?("Generating content with AI...")
        print("🤖 Calling OpenAI GPT...")
        let script: OpenAIService.PodcastScript
        do {
            script = try await OpenAIService.shared.generateDailyPodcast(
                interests: interests.map { $0.name },
                userInfo: userInfo,
                onProgress: { progress in
                    print("🤖 GPT Progress: \(progress)")
                    onProgress?(progress)
                }
            )
            print("✅ Script generated successfully")
            print("📝 Title: \(script.title)")
            print("📝 Segments: \(script.segments.count)")
        } catch {
            print("❌ Failed to generate script: \(error)")
            throw error
        }
        
        // Create IDs early so we can use them for file naming
        let podcastId = UUID().uuidString
        let episodeId = UUID().uuidString
        
        print("📦 Generated IDs - Podcast: \(podcastId), Episode: \(episodeId)")
        
        // Combine all segments into one text for TTS
        let fullScript = script.segments.map { $0.text }.joined(separator: "\n\n")
        print("📝 Full script length: \(fullScript.count) characters")
        
        // Convert to speech
        onProgress?("Converting to speech...")
        print("🎤 Starting TTS conversion...")
        print("🎤 Script will be chunked if over 4000 characters")
        let audioData: Data
        do {
            audioData = try await OpenAIService.shared.textToSpeech(text: fullScript) { progress in
                let percentage = Int(progress * 100)
                print("🎤 TTS Progress: \(percentage)%")
                onProgress?("Converting to speech: \(percentage)%")
            }
            print("✅ TTS conversion complete, audio size: \(audioData.count) bytes")
        } catch {
            print("❌ Failed TTS conversion: \(error)")
            throw error
        }
        
        // Upload audio to Supabase Storage
        onProgress?("Uploading audio file...")
        print("☁️ Uploading audio to Supabase Storage...")
        let audioURL = try await uploadAudioToSupabase(audioData: audioData, podcastId: podcastId)
        
        // Generate transcript with timestamps
        let estimatedDuration = script.segments.reduce(0) { $0 + $1.estimatedDuration }
        let transcript = OpenAIService.shared.generateTranscript(
            text: fullScript,
            totalDuration: estimatedDuration
        )
        
        let title = script.title
        let description = "An AI-generated podcast tailored to your interests: \(interests.map { $0.name }.joined(separator: ", "))"
        
        onProgress?("Saving to database...")
        
        // Save podcast to Supabase
        struct PodcastInsert: Codable {
            let id: String
            let user_id: String
            let title: String
            let description: String
            let interests: [String]
            let is_daily: Bool
        }
        
        let podcastInsert = PodcastInsert(
            id: podcastId,
            user_id: userId,
            title: title,
            description: description,
            interests: interests.map { $0.name },
            is_daily: isDaily
        )
        
        try await supabase
            .from("podcasts")
            .insert(podcastInsert)
            .execute()
        
        // Prepare transcript for database storage
        let transcriptJSON = try? JSONEncoder().encode(transcript)
        let transcriptString = transcriptJSON.flatMap { String(data: $0, encoding: .utf8) }
        
        print("📝 Transcript segments: \(transcript.count)")
        print("📝 Transcript JSON size: \(transcriptString?.count ?? 0) bytes")
        
        // Save episode to Supabase with transcript
        struct EpisodeInsert: Codable {
            let id: String
            let podcast_id: String
            let title: String
            let description: String
            let duration: Double
            let audio_url: String
            let transcript: String?
        }
        
        let episodeInsert = EpisodeInsert(
            id: episodeId,
            podcast_id: podcastId,
            title: "Episode 1",
            description: "Your personalized daily briefing",
            duration: estimatedDuration,
            audio_url: audioURL, // Now a cloud URL, not local path
            transcript: transcriptString
        )
        
        print("💾 Inserting episode with transcript into database...")
        try await supabase
            .from("episodes")
            .insert(episodeInsert)
            .execute()
        
        print("✅ Episode and transcript saved to database")
        
        // Create episode object with transcript
        let episode = Episode(
            id: episodeId,
            title: "Episode 1",
            description: "Your personalized daily briefing",
            duration: estimatedDuration,
            audioURL: audioURL, // Cloud URL for streaming
            transcript: transcriptString
        )
        
        let newPodcast = Podcast(
            id: podcastId,
            title: title,
            description: description,
            coverImageURL: nil,
            interests: interests.map { $0.name },
            episodes: [episode],
            isDaily: isDaily
        )
        
        // Add to local list
        await MainActor.run {
            podcasts.insert(newPodcast, at: 0)
        }
        
        onProgress?("Podcast ready!")
        
        return newPodcast
    }
    
    /// Upload audio data to Supabase Storage and return public URL
    private func uploadAudioToSupabase(audioData: Data, podcastId: String) async throws -> String {
        guard let supabase = supabase else {
            throw NSError(domain: "PodcastService", code: 500, userInfo: [NSLocalizedDescriptionKey: "Supabase not configured"])
        }
        
        // Generate unique filename
        let fileName = "\(podcastId)_\(UUID().uuidString).mp3"
        let filePath = "podcasts/\(fileName)"
        
        print("📤 Uploading to: \(filePath)")
        print("📊 File size: \(audioData.count) bytes (\(Double(audioData.count) / 1_000_000) MB)")
        
        // Upload to Supabase Storage
        do {
            _ = try await supabase.storage
                .from("podcast-audio")
                .upload(
                    path: filePath,
                    file: audioData,
                    options: .init(
                        contentType: "audio/mpeg"
                    )
                )
            
            print("✅ Audio uploaded successfully")
            
            // Get public URL
            let publicURL = try supabase.storage
                .from("podcast-audio")
                .getPublicURL(path: filePath)
            
            print("🔗 Public URL: \(publicURL)")
            
            return publicURL.absoluteString
            
        } catch {
            print("❌ Failed to upload audio: \(error)")
            print("💡 Make sure 'podcast-audio' bucket exists in Supabase Storage")
            throw error
        }
    }
    
    /// Save audio data to local documents directory (fallback/cache)
    private func saveAudioFileLocally(audioData: Data) async throws -> URL {
        let fileManager = FileManager.default
        let documentsPath = fileManager.urls(for: .documentDirectory, in: .userDomainMask)[0]
        let audioDirectory = documentsPath.appendingPathComponent("Podcasts", isDirectory: true)
        
        // Create directory if it doesn't exist
        if !fileManager.fileExists(atPath: audioDirectory.path) {
            try fileManager.createDirectory(at: audioDirectory, withIntermediateDirectories: true)
        }
        
        let fileName = "\(UUID().uuidString).mp3"
        let fileURL = audioDirectory.appendingPathComponent(fileName)
        
        try audioData.write(to: fileURL)
        
        return fileURL
    }
    
    /// Delete a podcast
    func deletePodcast(id: String) async throws {
        guard let supabase = supabase else {
            throw NSError(domain: "PodcastService", code: 500, userInfo: [NSLocalizedDescriptionKey: "Supabase not configured"])
        }
        
        guard let userId = UserService.shared.currentUser?.id else {
            throw NSError(domain: "PodcastService", code: 401, userInfo: [NSLocalizedDescriptionKey: "User not authenticated"])
        }
        
        // Delete from Supabase (episodes will cascade delete)
        // Filter by both id and user_id to ensure users can only delete their own podcasts
        try await supabase
            .from("podcasts")
            .delete()
            .eq("id", value: id)
            .eq("user_id", value: userId)
            .execute()
        
        // Update local state
        await MainActor.run {
            podcasts.removeAll { $0.id == id }
        }
    }
}

