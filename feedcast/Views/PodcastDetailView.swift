//
//  PodcastDetailView.swift
//  feedcast
//
//  Podcast detail page showing episodes list, description, and metadata
//

import SwiftUI

struct PodcastDetailView: View {
    let podcast: Podcast
    @Environment(\.dismiss) private var dismiss
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                // Header with artwork
                VStack(spacing: 16) {
                    // Artwork
                    RoundedRectangle(cornerRadius: 20)
                        .fill(
                            LinearGradient(
                                colors: gradientColors,
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .frame(width: 200, height: 200)
                        .overlay {
                            Image(systemName: "waveform")
                                .font(.system(size: 60))
                                .foregroundStyle(.white.opacity(0.8))
                        }
                        .shadow(radius: 15)
                    
                    // Title and metadata
                    VStack(spacing: 8) {
                        Text(podcast.title)
                            .font(.title)
                            .fontWeight(.bold)
                            .multilineTextAlignment(.center)
                        
                        if podcast.isDaily {
                            HStack {
                                Image(systemName: "sparkles")
                                Text("Daily Podcast")
                            }
                            .font(.subheadline)
                            .foregroundStyle(.blue)
                        }
                        
                        HStack(spacing: 12) {
                            Label("\(podcast.episodes.count) episodes", systemImage: "list.bullet")
                            Text("•")
                            Label(podcast.formattedDuration, systemImage: "clock")
                        }
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    }
                    .padding(.horizontal)
                }
                .frame(maxWidth: .infinity)
                .padding(.top)
                
                // About Section
                VStack(alignment: .leading, spacing: 12) {
                    Text("About")
                        .font(.headline)
                    
                    Text(podcast.description)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    
                    // Interests
                    if !podcast.interests.isEmpty {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Topics")
                                .font(.subheadline)
                                .fontWeight(.medium)
                            
                            FlowLayout(spacing: 8) {
                                ForEach(podcast.interests, id: \.self) { interest in
                                    Text(interest)
                                        .font(.caption)
                                        .padding(.horizontal, 12)
                                        .padding(.vertical, 6)
                                        .background(Color.blue.opacity(0.1))
                                        .foregroundStyle(.blue)
                                        .clipShape(Capsule())
                                }
                            }
                        }
                    }
                    
                    // Created date
                    HStack {
                        Text("Created")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                        
                        Text(podcast.createdAt, style: .date)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.horizontal)
                
                Divider()
                
                // Episodes List
                VStack(alignment: .leading, spacing: 16) {
                    Text("Episodes")
                        .font(.headline)
                        .padding(.horizontal)
                    
                    ForEach(podcast.episodes) { episode in
                        NavigationLink(destination: PlayerView(podcast: podcast, episode: episode)) {
                            EpisodeRow(episode: episode)
                        }
                    }
                }
                
                Spacer(minLength: 100)
            }
        }
        .navigationBarTitleDisplayMode(.inline)
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

// MARK: - Episode Row

struct EpisodeRow: View {
    let episode: Episode
    
    var body: some View {
        HStack(spacing: 16) {
            // Episode artwork
            RoundedRectangle(cornerRadius: 8)
                .fill(
                    LinearGradient(
                        colors: [.blue.opacity(0.6), .purple.opacity(0.6)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 60, height: 60)
                .overlay {
                    Image(systemName: "play.circle.fill")
                        .font(.title2)
                        .foregroundStyle(.white)
                }
            
            VStack(alignment: .leading, spacing: 6) {
                Text(episode.title)
                    .font(.subheadline)
                    .fontWeight(.semibold)
                    .foregroundStyle(.primary)
                    .lineLimit(2)
                
                Text(episode.description)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
                
                HStack(spacing: 8) {
                    Label(episode.formattedDuration, systemImage: "clock")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    
                    if episode.audioURL != nil {
                        Image(systemName: "checkmark.circle.fill")
                            .font(.caption2)
                            .foregroundStyle(.green)
                    }
                }
            }
            
            Spacer()
            
            Image(systemName: "chevron.right")
                .font(.caption)
                .foregroundStyle(.tertiary)
        }
        .padding()
        .background(Color(uiColor: .systemBackground))
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.05), radius: 5, y: 2)
        .padding(.horizontal)
    }
}

// MARK: - Flow Layout (for tags)

struct FlowLayout: Layout {
    var spacing: CGFloat = 8
    
    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let rows = computeRows(proposal: proposal, subviews: subviews)
        return rows.size
    }
    
    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let rows = computeRows(proposal: proposal, subviews: subviews)
        var y = bounds.minY
        
        for row in rows.rows {
            var x = bounds.minX
            for index in row {
                let size = subviews[index].sizeThatFits(.unspecified)
                subviews[index].place(at: CGPoint(x: x, y: y), proposal: .unspecified)
                x += size.width + spacing
            }
            y += rows.rowHeight + spacing
        }
    }
    
    private func computeRows(proposal: ProposedViewSize, subviews: Subviews) -> (rows: [[Int]], size: CGSize, rowHeight: CGFloat) {
        var rows: [[Int]] = [[]]
        var currentRow = 0
        var x: CGFloat = 0
        var maxWidth: CGFloat = 0
        var rowHeight: CGFloat = 0
        
        let width = proposal.width ?? .infinity
        
        for (index, subview) in subviews.enumerated() {
            let size = subview.sizeThatFits(.unspecified)
            rowHeight = max(rowHeight, size.height)
            
            if x + size.width > width && !rows[currentRow].isEmpty {
                currentRow += 1
                rows.append([])
                x = 0
            }
            
            rows[currentRow].append(index)
            x += size.width + spacing
            maxWidth = max(maxWidth, x - spacing)
        }
        
        let height = CGFloat(rows.count) * rowHeight + CGFloat(rows.count - 1) * spacing
        return (rows, CGSize(width: maxWidth, height: height), rowHeight)
    }
}

#Preview {
    NavigationStack {
        PodcastDetailView(podcast: Podcast(
            title: "Daily Tech Briefing",
            description: "Your personalized daily podcast covering AI, technology, and innovation.",
            interests: ["AI", "Technology", "Space"],
            episodes: [
                Episode(title: "Episode 1", description: "Introduction to AI trends", duration: 360, audioURL: "https://example.com/audio.mp3"),
                Episode(title: "Episode 2", description: "Space exploration updates", duration: 420)
            ],
            isDaily: true
        ))
    }
}

