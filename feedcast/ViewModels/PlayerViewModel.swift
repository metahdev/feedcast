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
import SwiftUI

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
    
    // Voice chat properties
    @Published var showVoiceChat = false
    @Published var isVoiceChatActive = false
    @Published var voiceTranscript = ""
    
    // MARK: - Private Properties
    private let chatService = ChatService.shared
    private let userService = UserService.shared
    private var cancellables = Set<AnyCancellable>()
    private var playbackTimer: Timer?
    private var audioPlayer: AVPlayer?
    private var timeObserver: Any?
    
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
        setupAudioPlayer()
    }
    
    deinit {
        if let observer = timeObserver {
            audioPlayer?.removeTimeObserver(observer)
        }
        audioPlayer?.pause()
        audioPlayer = nil
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
        let seekTime = min(max(time, 0), duration)
        currentTime = seekTime
        
        // Seek in audio player
        let cmTime = CMTime(seconds: seekTime, preferredTimescale: CMTimeScale(NSEC_PER_SEC))
        audioPlayer?.seek(to: cmTime, toleranceBefore: .zero, toleranceAfter: .zero)
        
        savePlaybackState()
    }
    
    func skip(seconds: TimeInterval) {
        seek(to: currentTime + seconds)
    }
    
    func changePlaybackRate(_ rate: Float) {
        playbackRate = rate
        audioPlayer?.rate = rate
    }
    
    func selectEpisode(_ episode: Episode) {
        savePlaybackState()
        
        let wasPlaying = isPlaying
        pause()
        
        currentEpisode = episode
        duration = episode.duration
        currentTime = 0
        
        setupAudioPlayer()
        
        if wasPlaying {
            play()
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
    
    private func setupAudioPlayer() {
        print("🎵 Setting up audio player for episode: \(currentEpisode.title)")
        
        // Remove old observer
        if let observer = timeObserver {
            audioPlayer?.removeTimeObserver(observer)
            timeObserver = nil
        }
        
        guard let audioURLString = currentEpisode.audioURL,
              let audioURL = URL(string: audioURLString) else {
            print("❌ No valid audio URL for episode")
            return
        }
        
        print("🔗 Audio URL: \(audioURL)")
        
        // Create player with URL
        let playerItem = AVPlayerItem(url: audioURL)
        audioPlayer = AVPlayer(playerItem: playerItem)
        audioPlayer?.rate = playbackRate
        
        // Observe playback time
        let interval = CMTime(seconds: 0.1, preferredTimescale: CMTimeScale(NSEC_PER_SEC))
        timeObserver = audioPlayer?.addPeriodicTimeObserver(forInterval: interval, queue: .main) { [weak self] time in
            guard let self = self else { return }
            self.currentTime = time.seconds
            
            // Save state periodically
            if Int(self.currentTime) % 10 == 0 {
                self.savePlaybackState()
            }
        }
        
        // Observe when playback finishes
        NotificationCenter.default.addObserver(
            forName: .AVPlayerItemDidPlayToEndTime,
            object: playerItem,
            queue: .main
        ) { [weak self] _ in
            self?.pause()
            self?.currentTime = 0
            self?.seek(to: 0)
        }
        
        // Observe player status
        audioPlayer?.currentItem?.publisher(for: \.status)
            .sink { [weak self] status in
                switch status {
                case .readyToPlay:
                    print("✅ Audio ready to play")
                    // Get actual duration from the audio file
                    if let duration = self?.audioPlayer?.currentItem?.duration.seconds,
                       duration.isFinite {
                        self?.duration = duration
                        print("📊 Actual duration: \(duration) seconds")
                    }
                case .failed:
                    print("❌ Audio player failed: \(self?.audioPlayer?.currentItem?.error?.localizedDescription ?? "Unknown error")")
                case .unknown:
                    print("⏳ Audio player status unknown")
                @unknown default:
                    break
                }
            }
            .store(in: &cancellables)
        
        print("✅ Audio player set up successfully")
    }
    
    private func startPlayback() {
        guard audioPlayer != nil else {
            print("⚠️ No audio player available, setting up...")
            setupAudioPlayer()
            return 
        }
        
        print("▶️ Starting playback at \(currentTime) seconds")
        audioPlayer?.play()
        audioPlayer?.rate = playbackRate
    }
    
    private func pausePlayback() {
        print("⏸️ Pausing playback")
        audioPlayer?.pause()
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

