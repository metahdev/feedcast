//
//  PlayerViewModel.swift
//  feedcast
//
//  ViewModel for podcast player with integrated chat functionality.
//
//  FUTURE INTEGRATION NOTES:
//  - Integrate LiveKit for real-time audio streaming
//  - Add audio playback controls (AVPlayer or custom audio engine)
//  - Implement background audio playback
//  - Add playback speed controls, skip forward/back
//

import Foundation
import Combine
import AVFoundation

@MainActor
class PlayerViewModel: ObservableObject {
    
    // MARK: - Published Properties
    @Published var podcast: Podcast
    @Published var currentEpisode: Episode
    @Published var isPlaying = false
    @Published var currentTime: TimeInterval = 0
    @Published var duration: TimeInterval = 0
    @Published var playbackRate: Float = 1.0
    
    // Chat properties
    @Published var messages: [ChatMessage] = []
    @Published var messageText = ""
    @Published var isChatVisible = false
    @Published var isSendingMessage = false
    
    // MARK: - Private Properties
    private let chatService = ChatService.shared
    private let userService = UserService.shared
    private var cancellables = Set<AnyCancellable>()
    private var playbackTimer: Timer?
    
    // MARK: - Initialization
    
    init(podcast: Podcast, episode: Episode? = nil) {
        self.podcast = podcast
        self.currentEpisode = episode ?? podcast.episodes.first ?? Episode(
            title: "Unknown",
            description: "",
            duration: 0
        )
        self.duration = self.currentEpisode.duration
        
        loadConversation()
        setupBindings()
        loadPlaybackState()
    }
    
    // MARK: - Playback Control
    
    func togglePlayPause() {
        isPlaying.toggle()
        
        if isPlaying {
            startPlayback()
        } else {
            pausePlayback()
        }
    }
    
    func play() {
        isPlaying = true
        startPlayback()
    }
    
    func pause() {
        isPlaying = false
        pausePlayback()
    }
    
    func seek(to time: TimeInterval) {
        currentTime = min(max(time, 0), duration)
        savePlaybackState()
        
        // TODO: Seek in actual audio player when LiveKit is integrated
    }
    
    func skip(seconds: TimeInterval) {
        seek(to: currentTime + seconds)
    }
    
    func changePlaybackRate(_ rate: Float) {
        playbackRate = rate
        // TODO: Update actual audio player rate when LiveKit is integrated
    }
    
    func selectEpisode(_ episode: Episode) {
        savePlaybackState()
        currentEpisode = episode
        duration = episode.duration
        currentTime = 0
        
        if isPlaying {
            pause()
        }
    }
    
    // MARK: - Chat Methods
    
    func sendMessage() {
        guard !messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty else { return }
        
        let content = messageText
        messageText = ""
        
        Task {
            isSendingMessage = true
            defer { isSendingMessage = false }
            
            do {
                _ = try await chatService.sendMessage(
                    podcastId: podcast.id,
                    episodeId: currentEpisode.id,
                    content: content,
                    podcast: podcast
                )
                loadConversation()
            } catch {
                print("Error sending message: \(error)")
            }
        }
    }
    
    func toggleChat() {
        withAnimation {
            isChatVisible.toggle()
        }
    }
    
    // MARK: - Private Methods
    
    private func startPlayback() {
        // TODO: Start actual audio playback when LiveKit is integrated
        
        // Simulate playback with timer
        playbackTimer = Timer.scheduledTimer(withTimeInterval: 0.1, repeats: true) { [weak self] _ in
            guard let self = self else { return }
            Task { @MainActor in
                self.currentTime += 0.1 * Double(self.playbackRate)
                
                if self.currentTime >= self.duration {
                    self.currentTime = self.duration
                    self.pause()
                }
                
                // Save state periodically
                if Int(self.currentTime) % 10 == 0 {
                    self.savePlaybackState()
                }
            }
        }
    }
    
    private func pausePlayback() {
        playbackTimer?.invalidate()
        playbackTimer = nil
        savePlaybackState()
    }
    
    private func loadConversation() {
        let conversation = chatService.getConversation(for: podcast.id)
        messages = conversation.messages
    }
    
    private func setupBindings() {
        chatService.$conversations
            .map { [weak self] conversations in
                guard let self = self else { return [] }
                return conversations[self.podcast.id]?.messages ?? []
            }
            .assign(to: &$messages)
    }
    
    private func savePlaybackState() {
        let state = PlaybackState(
            podcastId: podcast.id,
            episodeId: currentEpisode.id,
            currentTime: currentTime
        )
        userService.savePlaybackState(state)
    }
    
    private func loadPlaybackState() {
        if let state = userService.getPlaybackState(for: podcast.id),
           state.episodeId == currentEpisode.id {
            currentTime = state.currentTime
        }
    }
    
    // MARK: - Computed Properties
    
    var progress: Double {
        guard duration > 0 else { return 0 }
        return currentTime / duration
    }
    
    var formattedCurrentTime: String {
        formatTime(currentTime)
    }
    
    var formattedDuration: String {
        formatTime(duration)
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

