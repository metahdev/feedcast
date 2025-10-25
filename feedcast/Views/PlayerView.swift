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
        ZStack(alignment: .bottom) {
            // Main Content
            ScrollView {
                VStack(spacing: 0) {
                    // Header with artwork
                    PodcastHeaderView(podcast: viewModel.podcast)
                        .padding(.top)
                    
                    // Player Controls
                    PlayerControlsView(viewModel: viewModel)
                        .padding(.vertical, 24)
                    
                    // Episodes List
                    EpisodesListView(
                        episodes: viewModel.podcast.episodes,
                        currentEpisode: viewModel.currentEpisode
                    ) { episode in
                        viewModel.selectEpisode(episode)
                    }
                    .padding(.horizontal)
                    
                    // Podcast Info
                    PodcastInfoView(podcast: viewModel.podcast)
                        .padding()
                }
                .padding(.bottom, viewModel.isChatVisible ? 400 : 100)
            }
            
            // Chat Overlay
            if viewModel.isChatVisible {
                ChatView(viewModel: viewModel)
                    .transition(.move(edge: .bottom))
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    viewModel.toggleChat()
                } label: {
                    Image(systemName: viewModel.isChatVisible ? "message.fill" : "message")
                        .font(.title3)
                }
            }
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

// MARK: - Episodes List View

struct EpisodesListView: View {
    let episodes: [Episode]
    let currentEpisode: Episode
    let onSelect: (Episode) -> Void
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Episodes")
                .font(.headline)
            
            ForEach(episodes) { episode in
                Button {
                    onSelect(episode)
                } label: {
                    HStack(spacing: 12) {
                        // Episode indicator
                        Circle()
                            .fill(episode.id == currentEpisode.id ? Color.blue : Color.gray.opacity(0.3))
                            .frame(width: 8, height: 8)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text(episode.title)
                                .font(.subheadline)
                                .fontWeight(.medium)
                                .foregroundStyle(.primary)
                            
                            Text(episode.description)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                                .lineLimit(2)
                        }
                        
                        Spacer()
                        
                        Text(episode.formattedDuration)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .padding()
                    .background(
                        RoundedRectangle(cornerRadius: 12)
                            .fill(episode.id == currentEpisode.id ? Color.blue.opacity(0.1) : Color.clear)
                    )
                }
            }
        }
    }
}

// MARK: - Podcast Info View

struct PodcastInfoView: View {
    let podcast: Podcast
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("About")
                .font(.headline)
            
            Text(podcast.description)
                .font(.subheadline)
                .foregroundStyle(.secondary)
            
            HStack {
                Text("Generated")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                
                Text(podcast.createdAt, style: .date)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

// MARK: - Chat View

struct ChatView: View {
    @ObservedObject var viewModel: PlayerViewModel
    
    var body: some View {
        VStack(spacing: 0) {
            // Header
            HStack {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Ask About This Podcast")
                        .font(.headline)
                    Text("Chat with AI assistant")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                
                Spacer()
                
                Button {
                    viewModel.toggleChat()
                } label: {
                    Image(systemName: "xmark.circle.fill")
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
            .frame(height: 280)
            
            // Input
            HStack(spacing: 12) {
                TextField("Ask a question...", text: $viewModel.messageText, axis: .vertical)
                    .textFieldStyle(.roundedBorder)
                    .lineLimit(1...3)
                
                Button {
                    viewModel.sendMessage()
                } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.title2)
                }
                .disabled(viewModel.messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || viewModel.isSendingMessage)
            }
            .padding()
            .background(.ultraThinMaterial)
        }
        .background(.regularMaterial)
        .clipShape(RoundedRectangle(cornerRadius: 20))
        .shadow(radius: 20)
        .padding(.horizontal)
        .padding(.bottom, 80)
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
                        message.sender == .user ? Color.blue : Color.gray.opacity(0.2)
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

