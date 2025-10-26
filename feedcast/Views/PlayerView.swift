//
//  PlayerView.swift
//  feedcast
//
//  Podcast player view with integrated chat functionality.
//  Features playback controls and AI assistant chat in the same screen.
//

import SwiftUI

struct PlayerView: View {
    @StateObject private var viewModel: PlayerViewModel
    @Environment(\.dismiss) private var dismiss
    
    init(podcast: Podcast, episode: Episode? = nil) {
        _viewModel = StateObject(wrappedValue: PlayerViewModel(podcast: podcast, episode: episode))
    }
    
    var body: some View {
        VStack(spacing: 0) {
            // Main Content
            ScrollView {
                VStack(spacing: 24) {
                    // Header with artwork
                    PodcastHeaderView(podcast: viewModel.podcast)
                        .padding(.top)
                    
                    // Player Controls
                    PlayerControlsView(viewModel: viewModel)
                    
                    // Transcript Section
                    if let transcript = viewModel.currentEpisode.transcript,
                       let transcriptData = transcript.data(using: .utf8),
                       let segments = try? JSONDecoder().decode([TranscriptSegment].self, from: transcriptData) {
                        TranscriptView(
                            segments: segments,
                            currentTime: viewModel.currentTime
                        ) { time in
                            viewModel.seek(to: time)
                        }
                        .padding(.horizontal)
                    } else {
                        // Fallback: Show episode info
                        VStack(alignment: .leading, spacing: 12) {
                            Text("About This Episode")
                                .font(.headline)
                            
                            Text(viewModel.currentEpisode.description)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                        }
                        .padding()
                        .frame(maxWidth: .infinity, alignment: .leading)
                    }
                }
                .padding(.bottom, 120) // Space for fixed chat input
            }
            
            Divider()
            
            // Fixed Chat Input at Bottom
            ChatInputView(viewModel: viewModel)
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .principal) {
                VStack(spacing: 2) {
                    Text(viewModel.podcast.title)
                        .font(.headline)
                        .lineLimit(1)
                    Text(viewModel.currentEpisode.title)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }
            
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    viewModel.showVoiceChat = true
                } label: {
                    Image(systemName: "waveform.circle.fill")
                        .font(.title3)
                        .foregroundStyle(
                            LinearGradient(
                                colors: [.blue, .purple],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                }
            }
        }
        .sheet(isPresented: $viewModel.showVoiceChat) {
            VoiceChatView(viewModel: viewModel)
        }
    }
}

// MARK: - Podcast Header View

struct PodcastHeaderView: View {
    let podcast: Podcast
    
    var body: some View {
        VStack(spacing: 16) {
            // Artwork
            RoundedRectangle(cornerRadius: 20)
                .fill(
                    LinearGradient(
                        colors: [.blue, .purple],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 280, height: 280)
                .overlay {
                    Image(systemName: "waveform")
                        .font(.system(size: 80))
                        .foregroundStyle(.white.opacity(0.8))
                }
                .shadow(radius: 20)
            
            // Title and info
            VStack(spacing: 8) {
                Text(podcast.title)
                    .font(.title2)
                    .fontWeight(.bold)
                    .multilineTextAlignment(.center)
                
                Text(podcast.interests.joined(separator: " • "))
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.horizontal)
        }
    }
}

// MARK: - Player Controls View

struct PlayerControlsView: View {
    @ObservedObject var viewModel: PlayerViewModel
    
    var body: some View {
        VStack(spacing: 20) {
            // Progress Bar
            VStack(spacing: 8) {
                ProgressView(value: viewModel.progress)
                    .tint(.blue)
                
                HStack {
                    Text(viewModel.formattedCurrentTime)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    
                    Spacer()
                    
                    Text(viewModel.formattedDuration)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(.horizontal)
            
            // Playback Controls
            HStack(spacing: 40) {
                Button {
                    viewModel.skip(seconds: -15)
                } label: {
                    Image(systemName: "gobackward.15")
                        .font(.title)
                }
                
                Button {
                    viewModel.togglePlayPause()
                } label: {
                    Image(systemName: viewModel.isPlaying ? "pause.circle.fill" : "play.circle.fill")
                        .font(.system(size: 64))
                }
                
                Button {
                    viewModel.skip(seconds: 30)
                } label: {
                    Image(systemName: "goforward.30")
                        .font(.title)
                }
            }
            .foregroundStyle(.primary)
            
            // Playback Speed
            Menu {
                ForEach([0.5, 0.75, 1.0, 1.25, 1.5, 2.0], id: \.self) { speed in
                    Button {
                        viewModel.changePlaybackRate(Float(speed))
                    } label: {
                        HStack {
                            Text("\(speed, specifier: "%.2f")x")
                            if viewModel.playbackRate == Float(speed) {
                                Image(systemName: "checkmark")
                            }
                        }
                    }
                }
            } label: {
                Text("\(viewModel.playbackRate, specifier: "%.2f")x")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
    }
}

// MARK: - Transcript View

struct TranscriptView: View {
    let segments: [TranscriptSegment]
    let currentTime: TimeInterval
    let onSeek: (TimeInterval) -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            HStack {
                Text("Transcript")
                    .font(.headline)
                
                Spacer()
                
                Image(systemName: "doc.text")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            
            VStack(alignment: .leading, spacing: 12) {
                ForEach(Array(segments.enumerated()), id: \.offset) { index, segment in
                    TranscriptSegmentRow(
                        segment: segment,
                        isActive: currentTime >= segment.startTime && currentTime < segment.endTime,
                        onTap: {
                            onSeek(segment.startTime)
                        }
                    )
                }
            }
        }
        .padding()
        .background(Color(uiColor: .secondarySystemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 16))
    }
}

struct TranscriptSegmentRow: View {
    let segment: TranscriptSegment
    let isActive: Bool
    let onTap: () -> Void
    
    var body: some View {
        Button(action: onTap) {
            HStack(alignment: .top, spacing: 12) {
                // Timestamp
                Text(formatTime(segment.startTime))
                    .font(.caption)
                    .foregroundStyle(isActive ? .blue : .secondary)
                    .frame(width: 50, alignment: .leading)
                    .fontWeight(isActive ? .semibold : .regular)
                
                // Text
                Text(segment.text)
                    .font(.subheadline)
                    .foregroundStyle(isActive ? .primary : .secondary)
                    .multilineTextAlignment(.leading)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .fontWeight(isActive ? .medium : .regular)
            }
            .padding(.vertical, 8)
            .padding(.horizontal, 12)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(isActive ? Color.blue.opacity(0.1) : Color.clear)
            )
        }
        .buttonStyle(.plain)
    }
    
    private func formatTime(_ time: TimeInterval) -> String {
        let minutes = Int(time) / 60
        let seconds = Int(time) % 60
        return String(format: "%d:%02d", minutes, seconds)
    }
}

// MARK: - Chat Input View (Fixed at Bottom)

struct ChatInputView: View {
    @ObservedObject var viewModel: PlayerViewModel
    @State private var showMessages = false
    
    var body: some View {
        VStack(spacing: 0) {
            // Messages overlay (appears above input)
            if showMessages {
                VStack(spacing: 0) {
                    // Header
                    HStack {
                        Text("Chat with AI")
                            .font(.headline)
                        
                        Spacer()
                        
                        Button {
                            withAnimation {
                                showMessages = false
                            }
                        } label: {
                            Image(systemName: "chevron.down.circle.fill")
                                .font(.title3)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding()
                    .background(.ultraThinMaterial)
                    
                    // Messages
                    ScrollViewReader { proxy in
                        ScrollView {
                            LazyVStack(spacing: 12) {
                                ForEach(viewModel.messages) { message in
                                    ChatMessageBubble(message: message)
                                        .id(message.id)
                                }
                            }
                            .padding()
                        }
                        .onChange(of: viewModel.messages.count) { _, _ in
                            if let lastMessage = viewModel.messages.last {
                                withAnimation {
                                    proxy.scrollTo(lastMessage.id, anchor: .bottom)
                                }
                            }
                        }
                    }
                    .frame(height: 300)
                }
                .background(.regularMaterial)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
            
            // Input field (always visible)
            HStack(spacing: 12) {
                Button {
                    withAnimation {
                        showMessages.toggle()
                    }
                } label: {
                    Image(systemName: showMessages ? "chevron.down" : "message")
                        .font(.title3)
                        .foregroundStyle(.blue)
                        .frame(width: 32, height: 32)
                }
                
                TextField("Ask about this podcast...", text: $viewModel.messageText, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(1...3)
                
                Button {
                    viewModel.sendMessage()
                    if !showMessages {
                        withAnimation {
                            showMessages = true
                        }
                    }
                } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                        .foregroundStyle(viewModel.messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? .gray : .blue)
                }
                .disabled(viewModel.messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSendingMessage)
            }
            .padding()
            .background(.ultraThinMaterial)
        }
    }
}

// MARK: - Chat Message Bubble

struct ChatMessageBubble: View {
    let message: ChatMessage
    
    var body: some View {
        HStack {
            if message.sender == .user {
                Spacer()
            }
            
            VStack(alignment: message.sender == .user ? .trailing : .leading, spacing: 4) {
                Text(message.content)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(
                        message.sender == .user ? Color.blue : Color.gray.opacity(0.15)
                    )
                    .foregroundStyle(message.sender == .user ? .white : .primary)
                    .clipShape(RoundedRectangle(cornerRadius: 16))
                
                Text(message.timestamp, style: .time)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
            
            if message.sender == .ai {
                Spacer()
            }
        }
    }
}

#Preview {
    NavigationStack {
        PlayerView(podcast: Podcast(
            title: "Test Podcast",
            description: "A test podcast",
            episodes: [
                Episode(title: "Episode 1", description: "First episode", duration: 600)
            ]
        ))
    }
}

