//
//  VoiceChatView.swift
//  feedcast
//
//  Voice conversation with AI using LiveKit real-time infrastructure
//  STT, LLM, and TTS all handled by LiveKit Agent (server-side)
//  Implementation based on agent-starter-swift template
//

import SwiftUI
import AVFoundation
import LiveKit
import LiveKitComponents

struct VoiceChatView: View {
    @ObservedObject var viewModel: PlayerViewModel
    @Environment(\.dismiss) private var dismiss
    @StateObject private var voiceViewModel: VoiceConversationViewModel
    
    init(viewModel: PlayerViewModel) {
        self.viewModel = viewModel
        _voiceViewModel = StateObject(wrappedValue: VoiceConversationViewModel(podcast: viewModel.podcast))
    }
    
    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                LinearGradient(
                    colors: [.blue.opacity(0.15), .purple.opacity(0.15)],
                    startPoint: .topLeading,
                    endPoint: .bottomTrailing
                )
                .ignoresSafeArea()
                
                VStack(spacing: 32) {
                    Spacer()
                    
                    // Animated voice indicator (Siri-like)
                    SiriLikeVisualizer(
                        isListening: voiceViewModel.isListening,
                        isProcessing: voiceViewModel.isProcessing,
                        isSpeaking: voiceViewModel.isSpeaking,
                        audioTrack: voiceViewModel.agentAudioTrack
                    )
                    
                    // Status text
                    VStack(spacing: 8) {
                        Text(voiceViewModel.statusText)
                            .font(.title3)
                            .fontWeight(.semibold)
                        
                        Text(voiceViewModel.subtitleText)
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    .padding(.horizontal, 40)
                    
                    Spacer()
                    
                    // Transcript area
                    if !voiceViewModel.conversationTranscript.isEmpty {
                        ScrollView {
                            VStack(alignment: .leading, spacing: 16) {
                                ForEach(voiceViewModel.conversationTranscript, id: \.id) { item in
                                    VoiceTranscriptRow(item: item)
                                }
                            }
                            .padding()
                        }
                        .frame(height: 200)
                        .background(.ultraThinMaterial)
                        .clipShape(RoundedRectangle(cornerRadius: 20))
                        .padding(.horizontal)
                    }
                    
                    // Control buttons
                    HStack(spacing: 40) {
                        if voiceViewModel.isActive {
                            Button {
                                voiceViewModel.stopConversation()
                            } label: {
                                VStack(spacing: 8) {
                                    Image(systemName: "stop.circle.fill")
                                        .font(.system(size: 64))
                                        .foregroundStyle(.red)
                                    Text("End")
                                        .font(.caption)
                                        .foregroundStyle(.red)
                                }
                            }
                        } else {
                            Button {
                                voiceViewModel.startConversation()
                            } label: {
                                VStack(spacing: 8) {
                                    Image(systemName: "waveform.circle.fill")
                                        .font(.system(size: 64))
                                        .foregroundStyle(
                                            LinearGradient(
                                                colors: [.blue, .purple],
                                                startPoint: .topLeading,
                                                endPoint: .bottomTrailing
                                            )
                                        )
                                    Text("Start Voice Chat")
                                        .font(.caption)
                                        .foregroundStyle(.primary)
                                }
                            }
                        }
                    }
                    .padding(.bottom, 40)
                }
            }
            .navigationTitle("Voice Chat")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Close") {
                        voiceViewModel.stopConversation()
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .topBarTrailing) {
                    if voiceViewModel.isActive {
                        HStack(spacing: 4) {
                            Circle()
                                .fill(.red)
                                .frame(width: 8, height: 8)
                                .animation(.easeInOut(duration: 1).repeatForever(), value: voiceViewModel.isActive)
                            Text("Live")
                                .font(.caption)
                                .foregroundStyle(.red)
                        }
                    }
                }
            }
            .alert("LiveKit Not Configured", isPresented: $voiceViewModel.showConfigAlert) {
                Button("OK", role: .cancel) { }
            } message: {
                Text("Please configure LiveKit credentials in Config.swift to enable voice chat.")
            }
        }
    }
}

// MARK: - Siri-Like Voice Visualizer

struct SiriLikeVisualizer: View {
    let isListening: Bool
    let isProcessing: Bool
    let isSpeaking: Bool
    let audioTrack: AudioTrack?
    @State private var animationAmount = 1.0
    
    var body: some View {
        ZStack {
            // Outer animated rings (Siri-like)
            ForEach(0..<3) { index in
                Circle()
                    .stroke(lineWidth: 3)
                    .fill(
                        LinearGradient(
                            colors: currentGradientColors,
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                        .opacity(0.4 - Double(index) * 0.1)
                    )
                    .frame(width: 140 + CGFloat(index * 40), height: 140 + CGFloat(index * 40))
                    .scaleEffect(isActive ? animationAmount : 1)
                    .opacity(isActive ? (1 - Double(index) * 0.25) : 0.3)
            }
            
            // Center waveform circle with LiveKit BarAudioVisualizer
            ZStack {
                Circle()
                    .fill(
                        LinearGradient(
                            colors: currentGradientColors,
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 120, height: 120)
                    .shadow(color: currentGradientColors.first?.opacity(0.6) ?? .clear, radius: 20)
                
                // Use LiveKit's BarAudioVisualizer when audio track is available
                if let audioTrack = audioTrack {
                    BarAudioVisualizer(
                        audioTrack: audioTrack,
                        agentState: currentAgentState,
                        barCount: 5,
                        barSpacingFactor: 0.15
                    )
                    .frame(width: 80, height: 60)
                } else {
                    // Fallback placeholder waveform
                    HStack(spacing: 6) {
                        ForEach(0..<5) { index in
                            RoundedRectangle(cornerRadius: 10)
                                .fill(.white)
                                .frame(width: 6, height: waveformHeight(for: index))
                                .animation(
                                    .easeInOut(duration: 0.5)
                                    .repeatForever(autoreverses: true)
                                    .delay(Double(index) * 0.1),
                                    value: isActive
                                )
                        }
                    }
                }
            }
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 1.5).repeatForever(autoreverses: true)) {
                animationAmount = 1.15
            }
        }
    }
    
    var isActive: Bool {
        isListening || isProcessing || isSpeaking
    }
    
    var currentAgentState: AgentState {
        if isSpeaking {
            return .speaking
        } else if isProcessing {
            return .thinking
        } else {
            return .listening
        }
    }
    
    var currentGradientColors: [Color] {
        if isSpeaking {
            return [.blue, .cyan]
        } else if isProcessing {
            return [.orange, .pink]
        } else if isListening {
            return [.green, .mint]
        } else {
            return [.gray, .gray.opacity(0.5)]
        }
    }
    
    func waveformHeight(for index: Int) -> CGFloat {
        guard isActive else { return 20 }
        
        let baseHeights: [CGFloat] = [30, 50, 60, 50, 30]
        let multiplier: CGFloat = isSpeaking ? 1.2 : (isListening ? 1.0 : 0.7)
        
        return baseHeights[index] * multiplier
    }
}

// MARK: - Voice Transcript Row

struct VoiceTranscriptRow: View {
    let item: VoiceTranscriptItem
    
    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: item.isUser ? "person.circle.fill" : "waveform.circle.fill")
                .font(.title3)
                .foregroundStyle(item.isUser ? .blue : .purple)
            
            VStack(alignment: .leading, spacing: 4) {
                Text(item.isUser ? "You" : "AI Assistant")
                    .font(.caption)
                    .fontWeight(.semibold)
                    .foregroundStyle(.secondary)
                
                Text(item.text)
                    .font(.subheadline)
            }
            
            Spacer()
        }
    }
}

// MARK: - Voice Conversation ViewModel

@MainActor
class VoiceConversationViewModel: ObservableObject {
    @Published var isActive = false
    @Published var isListening = false
    @Published var isProcessing = false
    @Published var isSpeaking = false
    @Published var conversationTranscript: [VoiceTranscriptItem] = []
    @Published var showConfigAlert = false
    @Published var agentAudioTrack: AudioTrack?
    
    let podcast: Podcast
    private var liveKitService: LiveKitVoiceService?
    
    init(podcast: Podcast) {
        self.podcast = podcast
    }
    
    var statusText: String {
        if isSpeaking {
            return "AI is speaking..."
        } else if isProcessing {
            return "Thinking..."
        } else if isListening {
            return "Listening..."
        } else if isActive {
            return "Ready to listen"
        } else {
            return "Voice Chat About Podcast"
        }
    }
    
    var subtitleText: String {
        if isActive {
            return "Ask me anything about '\(podcast.title)'"
        } else {
            return "Tap to start a voice conversation with AI"
        }
    }
    
    func startConversation() {
        print("🎙️ Starting LiveKit voice conversation")
        
        // Check if LiveKit is configured
        guard Config.isLiveKitConfigured else {
            print("❌ LiveKit not configured")
            showConfigAlert = true
            return
        }
        
        isActive = true
        
        // Initialize LiveKit service
        liveKitService = LiveKitVoiceService(
            podcast: podcast,
            onTranscript: { [weak self] text, isUser in
                self?.handleTranscript(text: text, isUser: isUser)
            },
            onStateChange: { [weak self] state in
                self?.handleStateChange(state: state)
            },
            onAgentAudioTrack: { [weak self] audioTrack in
                self?.agentAudioTrack = audioTrack
            }
        )
        
        // Connect to LiveKit room
        Task {
            do {
                try await liveKitService?.connect()
                isListening = true
            } catch {
                print("❌ Failed to connect to LiveKit: \(error)")
                isActive = false
            }
        }
    }
    
    func stopConversation() {
        print("🛑 Stopping voice conversation")
        isActive = false
        isListening = false
        isProcessing = false
        isSpeaking = false
        
        Task {
            await liveKitService?.disconnect()
            liveKitService = nil
        }
    }
    
    private func handleTranscript(text: String, isUser: Bool) {
        conversationTranscript.append(VoiceTranscriptItem(text: text, isUser: isUser))
    }
    
    private func handleStateChange(state: VoiceState) {
        switch state {
        case .listening:
            isListening = true
            isProcessing = false
            isSpeaking = false
        case .processing:
            isListening = false
            isProcessing = true
            isSpeaking = false
        case .speaking:
            isListening = false
            isProcessing = false
            isSpeaking = true
        }
    }
}

// MARK: - Supporting Types

struct VoiceTranscriptItem: Identifiable {
    let id = UUID()
    let text: String
    let isUser: Bool
}

enum VoiceState {
    case listening
    case processing
    case speaking
}

// MARK: - LiveKit Voice Service

/// Connection details for LiveKit
private struct LiveKitConnectionDetails {
    let url: String
    let token: String
}

/// Handles real-time voice communication with LiveKit Agent
/// Based on agent-starter-swift template implementation
@MainActor
class LiveKitVoiceService: RoomDelegate {
    let podcast: Podcast
    let onTranscript: (String, Bool) -> Void
    let onStateChange: (VoiceState) -> Void
    let onAgentAudioTrack: (AudioTrack?) -> Void
    
    private var room: Room?
    private var agentParticipant: RemoteParticipant?
    
    init(
        podcast: Podcast,
        onTranscript: @escaping (String, Bool) -> Void,
        onStateChange: @escaping (VoiceState) -> Void,
        onAgentAudioTrack: @escaping (AudioTrack?) -> Void
    ) {
        self.podcast = podcast
        self.onTranscript = onTranscript
        self.onStateChange = onStateChange
        self.onAgentAudioTrack = onAgentAudioTrack
    }
    
    func connect() async throws {
        print("🔌 Connecting to LiveKit room for podcast: \(podcast.title)")
        
        // 1. Create room
        room = Room()
        
        // 2. Add delegate to observe room events
        room?.add(delegate: self)
        
        // 3. Register transcription stream handler
        registerTranscriptionHandler()
        
        // 4. Get connection details (URL + token)
        let roomName = "podcast-\(podcast.id ?? UUID().uuidString)"
        let connectionDetails = try await fetchConnectionDetails(roomName: roomName)
        
        print("🔌 Connecting to: \(connectionDetails.url)")
        
        // 5. Prepare podcast metadata for the agent including transcript
        var podcastMetadata: [String: Any] = [
            "podcast_title": podcast.title,
            "podcast_description": podcast.description,
            "podcast_interests": podcast.interests.joined(separator: ", ")
        ]
        
        // Add current episode info and transcript if available
        if let episode = podcast.episodes.first {
            podcastMetadata["current_episode"] = episode.title
            podcastMetadata["episode_description"] = episode.description
            
            // Parse and include transcript
            if let transcriptString = episode.transcript,
               let transcriptData = transcriptString.data(using: .utf8),
               let transcriptSegments = try? JSONDecoder().decode([OpenAIService.TranscriptSegment].self, from: transcriptData) {
                
                // Convert transcript segments to simple text for the agent
                let fullTranscript = transcriptSegments.map { segment in
                    let timestamp = formatTime(segment.startTime)
                    return "[\(timestamp)] \(segment.text)"
                }.joined(separator: "\n")
                
                podcastMetadata["episode_transcript"] = fullTranscript
                print("📝 Transcript included: \(transcriptSegments.count) segments, \(fullTranscript.count) characters")
            } else {
                print("⚠️ No transcript available for episode")
            }
        }
        
        // Convert to JSON string
        let metadataJSON = try? JSONSerialization.data(withJSONObject: podcastMetadata)
        let metadataString = metadataJSON.flatMap { String(data: $0, encoding: .utf8) } ?? "{}"
        
        print("📦 Sending podcast context to agent")
        print("📦 Metadata size: \(metadataString.count) bytes")
        
        // 6. Connect with pre-connect audio
        try await room?.withPreConnectAudio {
            try await self.room?.connect(
                url: connectionDetails.url,
                token: connectionDetails.token,
                connectOptions: ConnectOptions(
                    enableMicrophone: true
                )
            )
        }
        
        // 7. Set participant metadata after connection
        try await room?.localParticipant.set(metadata: metadataString)
        print("✅ Connected to LiveKit room: \(roomName)")
        print("📦 Participant metadata updated with podcast context")
        
        // 8. Also send transcript as a data message for reliability
        if let episode = podcast.episodes.first,
           let transcriptString = episode.transcript,
           let transcriptData = transcriptString.data(using: .utf8),
           let transcriptSegments = try? JSONDecoder().decode([OpenAIService.TranscriptSegment].self, from: transcriptData) {
            
            // Send transcript via data channel as backup
            let transcriptMessage: [String: Any] = [
                "type": "podcast_transcript",
                "segments": transcriptSegments.map { segment -> [String: Any] in
                    return [
                        "startTime": segment.startTime,
                        "endTime": segment.endTime,
                        "text": segment.text
                    ]
                }
            ]
            
            if let transcriptJSON = try? JSONSerialization.data(withJSONObject: transcriptMessage) {
                try await room?.localParticipant.publish(data: transcriptJSON, reliable: true, topic: "podcast_transcript")
                print("📤 Transcript sent via data channel (\(transcriptJSON.count) bytes)")
            }
        }
        
        onStateChange(.listening)
    }
    
    private func registerTranscriptionHandler() {
        Task {
            do {
                print("📝 Registering transcription handler...")
                try await room?.registerTextStreamHandler(for: "lk.transcription") { [weak self] reader, participantIdentity in
                    guard let self = self else { return }
                    
                    print("📝 Transcription stream started for participant: \(participantIdentity)")
                    
                    var accumulatedText = ""
                    
                    for try await text in reader where !text.isEmpty {
                        accumulatedText = text // Each message contains the full text so far
                        
                        let isFinal = reader.info.attributes["lk.transcription_final"] == "true"
                        let isUser = await (participantIdentity == self.room?.localParticipant.identity)
                        
                        print("📝 Transcription chunk [\(isUser ? "User" : "Agent")]: \"\(text)\" (final: \(isFinal))")
                        
                        // Send both interim and final transcripts, but mark them differently
                        if !accumulatedText.isEmpty {
                            if isFinal {
                                print("📝 ✅ Final transcription [\(isUser ? "User" : "Agent")]: \(accumulatedText)")
                                await MainActor.run {
                                    self.onTranscript(accumulatedText, isUser)
                                }
                                accumulatedText = "" // Reset for next message
                            } else {
                                // For interim transcripts, just log them (optional: could show in UI as "typing...")
                                print("📝 ⏳ Interim transcription [\(isUser ? "User" : "Agent")]: \(accumulatedText)")
                            }
                        }
                    }
                    
                    print("📝 Transcription stream ended for participant: \(participantIdentity)")
                }
                print("✅ Transcription stream handler registered successfully")
            } catch {
                print("❌ Failed to register transcription handler: \(error)")
                print("❌ Error details: \(error.localizedDescription)")
            }
        }
    }
    
    // MARK: - RoomDelegate Methods
    
    nonisolated func room(_ room: Room, participant: RemoteParticipant, didUpdateAttributes attributes: [String: String]) {
        // Monitor agent state changes via attributes
        if participant.isAgent, let state = attributes["lk.agent.state"] {
            print("🤖 Agent state: \(state)")
            
            Task { @MainActor in
                switch state {
                case "listening":
                    self.onStateChange(.listening)
                case "thinking":
                    self.onStateChange(.processing)
                case "speaking":
                    self.onStateChange(.speaking)
                default:
                    break
                }
            }
        }
    }
    
    nonisolated func room(_ room: Room, participant: RemoteParticipant, didSubscribeTrack publication: TrackPublication) {
        // Monitor when agent audio track becomes available
        Task { @MainActor in
            if participant.isAgent, 
               let audioTrack = publication.track as? AudioTrack,
               publication.source == .microphone {
                print("🔊 Agent audio track available")
                self.onAgentAudioTrack(audioTrack)
            }
        }
    }
    
    nonisolated func room(_ room: Room, participant: RemoteParticipant, didUnsubscribeTrack publication: TrackPublication) {
        // Handle track removal
        Task { @MainActor in
            if participant.isAgent, publication.source == .microphone {
                print("🔇 Agent audio track removed")
                self.onAgentAudioTrack(nil)
            }
        }
    }
    
    nonisolated func room(_ room: Room, didUpdateConnectionState connectionState: ConnectionState, from oldValue: ConnectionState) {
        print("🔌 Connection state changed: \(oldValue) -> \(connectionState)")
    }
    
    nonisolated func room(_ room: Room, participantDidConnect participant: RemoteParticipant) {
        Task { @MainActor in
            if participant.isAgent {
                self.agentParticipant = participant
                print("🤖 Agent joined the room: \(participant.identity)")
            }
        }
    }
    
    nonisolated func room(_ room: Room, participantDidDisconnect participant: RemoteParticipant) {
        Task { @MainActor in
            if participant.isAgent {
                self.agentParticipant = nil
                print("🤖 Agent left the room")
            }
        }
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
    
    private func fetchConnectionDetails(roomName: String) async throws -> LiveKitConnectionDetails {
        let participantName = "user-\(Int.random(in: 1000...9999))"
        
        // Option 1: Use LiveKit Sandbox (recommended for development)
        if let sandboxId = Config.liveKitSandboxId, !sandboxId.isEmpty {
            return try await fetchFromSandbox(
                sandboxId: sandboxId,
                roomName: roomName,
                participantName: participantName
            )
        }
        
        // Option 2: Use hardcoded token (quick testing only)
        if let hardcodedToken = Config.liveKitHardcodedToken, !hardcodedToken.isEmpty {
            return LiveKitConnectionDetails(url: Config.liveKitURL, token: hardcodedToken)
        }
        
        // Option 3: Use your own token server (production)
        return try await fetchFromCustomServer(
            roomName: roomName,
            participantName: participantName
        )
    }
    
    private func fetchFromSandbox(sandboxId: String, roomName: String, participantName: String) async throws -> LiveKitConnectionDetails {
        let sandboxUrl = "https://cloud-api.livekit.io/api/sandbox/connection-details"
        
        var urlComponents = URLComponents(string: sandboxUrl)!
        urlComponents.queryItems = [
            URLQueryItem(name: "roomName", value: roomName),
            URLQueryItem(name: "participantName", value: participantName),
        ]
        
        var request = URLRequest(url: urlComponents.url!)
        request.httpMethod = "POST"
        request.addValue(sandboxId, forHTTPHeaderField: "X-Sandbox-ID")
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw LiveKitError.tokenFetchFailed
        }
        
        struct SandboxResponse: Codable {
            let serverUrl: String
            let participantToken: String
        }
        
        let details = try JSONDecoder().decode(SandboxResponse.self, from: data)
        
        // Return URL and token from sandbox
        return LiveKitConnectionDetails(url: details.serverUrl, token: details.participantToken)
    }
    
    private func fetchFromCustomServer(roomName: String, participantName: String) async throws -> LiveKitConnectionDetails {
        // Your own token server endpoint
        let url = URL(string: "http://localhost:3000/token")!
        // For production: URL(string: "https://your-token-server.vercel.app/token")!
        
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        
        // Include podcast context in metadata
        let podcastMetadata: [String: Any] = [
            "title": podcast.title,
            "description": podcast.description,
            "interests": podcast.interests,
            "currentEpisode": podcast.episodes.first?.title ?? ""
        ]
        
        let body: [String: Any] = [
            "roomName": roomName,
            "participantName": participantName,
            "metadata": ["podcast": podcastMetadata]
        ]
        
        request.httpBody = try JSONSerialization.data(withJSONObject: body)
        
        let (data, response) = try await URLSession.shared.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw LiveKitError.tokenFetchFailed
        }
        
        struct TokenResponse: Codable {
            let token: String
            let url: String?  // Optional: server might return URL
        }
        
        let tokenResponse = try JSONDecoder().decode(TokenResponse.self, from: data)
        
        // Use URL from server response, or fall back to Config
        let serverUrl = tokenResponse.url ?? Config.liveKitURL
        
        return LiveKitConnectionDetails(url: serverUrl, token: tokenResponse.token)
    }
    
    func disconnect() async {
        print("🔌 Disconnecting from LiveKit room...")
        
        // Remove delegate
        room?.remove(delegate: self)
        
        // Unregister transcription handler
        await room?.unregisterTextStreamHandler(for: "lk.transcription")
        
        // Disconnect from room
        await room?.disconnect()
        room = nil
        agentParticipant = nil
        print("✅ Disconnected from LiveKit")
    }
}

// MARK: - LiveKit Errors

enum LiveKitError: LocalizedError {
    case tokenFetchFailed
    
    var errorDescription: String? {
        switch self {
        case .tokenFetchFailed:
            return "Failed to fetch LiveKit token from server"
        }
    }
}

#Preview {
    VoiceChatView(viewModel: PlayerViewModel(
        podcast: Podcast(
            title: "AI and the Future",
            description: "Exploring artificial intelligence",
            interests: ["AI", "Technology"],
            episodes: [Episode(title: "Episode 1", description: "Intro", duration: 300)]
        )
    ))
}
