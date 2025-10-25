//
//  LibraryView.swift
//  feedcast
//
//  Main library view displaying all podcasts in a grid layout.
//  Inspired by Apple Books and Podcasts apps.
//

import SwiftUI

struct LibraryView: View {
    @StateObject private var viewModel = LibraryViewModel()
    @State private var showingInterests = false
    @State private var showingNewPodcast = false
    
    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Daily Podcast Section
                    if let daily = viewModel.dailyPodcast {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Today's Podcast")
                                .font(.title2)
                                .fontWeight(.bold)
                                .padding(.horizontal)
                            
                            NavigationLink(destination: PlayerView(podcast: daily)) {
                                DailyPodcastCard(podcast: daily)
                                    .padding(.horizontal)
                            }
                        }
                        .padding(.top)
                    }
                    
                    // Recent Podcasts Grid
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("Your Library")
                                .font(.title2)
                                .fontWeight(.bold)
                            
                            Spacer()
                            
                            Menu {
                                Picker("Sort", selection: $viewModel.sortOption) {
                                    ForEach(SortOption.allCases, id: \.self) { option in
                                        Text(option.rawValue).tag(option)
                                    }
                                }
                            } label: {
                                Image(systemName: "arrow.up.arrow.down.circle")
                                    .font(.title3)
                            }
                        }
                        .padding(.horizontal)
                        
                        LazyVGrid(columns: [
                            GridItem(.flexible(), spacing: 16),
                            GridItem(.flexible(), spacing: 16)
                        ], spacing: 20) {
                            ForEach(viewModel.filteredPodcasts) { podcast in
                                NavigationLink(destination: PlayerView(podcast: podcast)) {
                                    PodcastCard(podcast: podcast)
                                }
                                .contextMenu {
                                    Button(role: .destructive) {
                                        viewModel.deletePodcast(podcast)
                                    } label: {
                                        Label("Delete", systemImage: "trash")
                                    }
                                }
                            }
                        }
                        .padding(.horizontal)
                    }
                }
                .padding(.bottom, 100)
            }
            .navigationTitle("Feedcast")
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button {
                        showingInterests = true
                    } label: {
                        Image(systemName: "star.circle.fill")
                            .font(.title3)
                    }
                }
                
                ToolbarItem(placement: .topBarTrailing) {
                    Button {
                        showingNewPodcast = true
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.title3)
                    }
                }
            }
            .searchable(text: $viewModel.searchText, prompt: "Search podcasts")
            .refreshable {
                await viewModel.refreshPodcasts()
            }
            .sheet(isPresented: $showingInterests) {
                InterestsView()
            }
            .sheet(isPresented: $showingNewPodcast) {
                NewPodcastView { interests in
                    viewModel.generateNewPodcast(interests: interests)
                }
            }
        }
    }
}

// MARK: - Daily Podcast Card

struct DailyPodcastCard: View {
    let podcast: Podcast
    
    var body: some View {
        ZStack(alignment: .bottomLeading) {
            RoundedRectangle(cornerRadius: 16)
                .fill(
                    LinearGradient(
                        colors: [.blue, .purple],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(height: 200)
            
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    Image(systemName: "sparkles")
                        .font(.caption)
                    Text("AI Generated Today")
                        .font(.caption)
                        .fontWeight(.medium)
                }
                .foregroundStyle(.white.opacity(0.9))
                
                Text(podcast.title)
                    .font(.title3)
                    .fontWeight(.bold)
                    .foregroundStyle(.white)
                    .lineLimit(2)
                
                Text("\(podcast.episodes.count) episodes • \(podcast.formattedDuration)")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.8))
            }
            .padding()
        }
    }
}

// MARK: - Podcast Card

struct PodcastCard: View {
    let podcast: Podcast
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Cover Image
            RoundedRectangle(cornerRadius: 12)
                .fill(
                    LinearGradient(
                        colors: gradientColors,
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .aspectRatio(1, contentMode: .fit)
                .overlay {
                    VStack {
                        Image(systemName: "waveform")
                            .font(.system(size: 40))
                            .foregroundStyle(.white.opacity(0.8))
                    }
                }
            
            // Info
            VStack(alignment: .leading, spacing: 4) {
                Text(podcast.title)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(.primary)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)
                
                Text("\(podcast.episodes.count) episodes")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                
                Text(podcast.formattedDuration)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
    }
    
    private var gradientColors: [Color] {
        let hash = abs(podcast.id.hashValue)
        let colorPairs: [[Color]] = [
            [.blue, .cyan],
            [.purple, .pink],
            [.orange, .red],
            [.green, .mint],
            [.indigo, .blue],
            [.pink, .purple]
        ]
        return colorPairs[hash % colorPairs.count]
    }
}

// MARK: - New Podcast View

struct NewPodcastView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var interestsViewModel = InterestsViewModel()
    @State private var selectedInterests: Set<String> = []
    
    let onGenerate: ([Interest]) -> Void
    
    var body: some View {
        NavigationStack {
            List {
                Section {
                    Text("Select interests for your new AI-generated podcast")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                
                Section("Your Interests") {
                    ForEach(interestsViewModel.activeInterests) { interest in
                        Button {
                            if selectedInterests.contains(interest.id) {
                                selectedInterests.remove(interest.id)
                            } else {
                                selectedInterests.insert(interest.id)
                            }
                        } label: {
                            HStack {
                                Text(interest.category.emoji)
                                Text(interest.name)
                                    .foregroundStyle(.primary)
                                Spacer()
                                if selectedInterests.contains(interest.id) {
                                    Image(systemName: "checkmark.circle.fill")
                                        .foregroundStyle(.blue)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("New Podcast")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        dismiss()
                    }
                }
                
                ToolbarItem(placement: .confirmationAction) {
                    Button("Generate") {
                        let selected = interestsViewModel.activeInterests.filter {
                            selectedInterests.contains($0.id)
                        }
                        onGenerate(selected)
                        dismiss()
                    }
                    .disabled(selectedInterests.isEmpty)
                }
            }
        }
    }
}

#Preview {
    LibraryView()
}

