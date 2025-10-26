//
//  ProfileView.swift
//  feedcast
//
//  User profile and settings view
//

import SwiftUI

struct ProfileView: View {
    @EnvironmentObject var userService: UserService
    @State private var showingSignOutAlert = false
    
    var body: some View {
        NavigationStack {
            List {
                // User Info Section
                if let user = userService.currentUser {
                    Section {
                        HStack(spacing: 16) {
                            // Avatar
                            Circle()
                                .fill(
                                    LinearGradient(
                                        colors: [.blue, .purple],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    )
                                )
                                .frame(width: 70, height: 70)
                                .overlay {
                                    Text(user.name.prefix(1).uppercased())
                                        .font(.title)
                                        .fontWeight(.bold)
                                        .foregroundStyle(.white)
                                }
                            
                            VStack(alignment: .leading, spacing: 4) {
                                Text(user.name)
                                    .font(.title3)
                                    .fontWeight(.semibold)
                                
                                Text(user.email)
                                    .font(.subheadline)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .padding(.vertical, 8)
                    }
                    
                    // Profile Details
                    Section("About") {
                        if let country = user.country {
                            ProfileInfoRow(icon: "globe", label: "Country", value: country)
                        }
                        
                        if let age = user.age {
                            ProfileInfoRow(icon: "calendar", label: "Age", value: "\(age)")
                        }
                        
                        if let gender = user.gender {
                            ProfileInfoRow(icon: "person.fill", label: "Gender", value: gender)
                        }
                        
                        if let occupation = user.occupation {
                            ProfileInfoRow(icon: "briefcase.fill", label: "Occupation", value: occupation)
                        }
                    }
                    
                    // Interests Section
                    Section("Interests") {
                        NavigationLink {
                            InterestsView()
                        } label: {
                            HStack {
                                Image(systemName: "star.fill")
                                    .foregroundStyle(.yellow)
                                Text("\(user.interests.count) interests")
                                Spacer()
                            }
                        }
                    }
                    
                    // News Sources Section
                    if !user.newsSources.isEmpty {
                        Section("News Sources") {
                            ForEach(user.newsSources.prefix(3), id: \.self) { source in
                                HStack {
                                    Image(systemName: "newspaper.fill")
                                        .foregroundStyle(.blue)
                                    Text(source)
                                }
                            }
                            
                            if user.newsSources.count > 3 {
                                Text("+ \(user.newsSources.count - 3) more")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                    
                    // Settings Section
                    Section("Preferences") {
                        Toggle(isOn: .constant(user.dailyPodcastEnabled)) {
                            HStack {
                                Image(systemName: "calendar.badge.clock")
                                    .foregroundStyle(.green)
                                Text("Daily Podcast")
                            }
                        }
                        .disabled(true) // TODO: Make functional
                        
                        if let time = user.dailyPodcastTime {
                            HStack {
                                Image(systemName: "clock.fill")
                                    .foregroundStyle(.orange)
                                Text("Preferred Time")
                                Spacer()
                                Text(time.formatted(date: .omitted, time: .shortened))
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
                
                // Account Actions
                Section {
                    Button(role: .destructive) {
                        showingSignOutAlert = true
                    } label: {
                        HStack {
                            Image(systemName: "arrow.right.square.fill")
                            Text("Sign Out")
                        }
                    }
                }
                
                // App Info
                Section {
                    HStack {
                        Text("Version")
                        Spacer()
                        Text("1.0.0")
                            .foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle("Profile")
            .alert("Sign Out", isPresented: $showingSignOutAlert) {
                Button("Cancel", role: .cancel) { }
                Button("Sign Out", role: .destructive) {
                    Task {
                        try? await userService.signOut()
                    }
                }
            } message: {
                Text("Are you sure you want to sign out?")
            }
        }
    }
}

// MARK: - Supporting Views

struct ProfileInfoRow: View {
    let icon: String
    let label: String
    let value: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundStyle(.blue)
                .frame(width: 24)
            Text(label)
            Spacer()
            Text(value)
                .foregroundStyle(.secondary)
        }
    }
}

#Preview {
    ProfileView()
        .environmentObject(UserService.shared)
}

