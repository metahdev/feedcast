//
//  OnboardingView.swift
//  feedcast
//
//  Onboarding flow for new users
//

import SwiftUI

struct OnboardingView: View {
    @StateObject private var viewModel = OnboardingViewModel()
    @State private var currentPage = 0
    let onComplete: () -> Void
    
    var body: some View {
        ZStack {
            // Background gradient
            LinearGradient(
                colors: [.blue, .purple],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            TabView(selection: $currentPage) {
                // Page 1: Welcome
                WelcomePageView()
                    .tag(0)
                
                // Page 2: How it works
                HowItWorksPageView()
                    .tag(1)
                
                // Page 3: Basic info
                BasicInfoPageView(viewModel: viewModel)
                    .tag(2)
                
                // Page 4: Select interests
                SelectInterestsPageView(viewModel: viewModel)
                    .tag(3)
                
                // Page 5: News sources
                NewsSourcesPageView(viewModel: viewModel)
                    .tag(4)
                
                // Page 6: Daily podcast setup
                DailyPodcastPageView(viewModel: viewModel)
                    .tag(5)
                
                // Page 7: Get started
                GetStartedPageView(viewModel: viewModel, onComplete: onComplete)
                    .tag(6)
            }
            .tabViewStyle(.page(indexDisplayMode: .always))
            .indexViewStyle(.page(backgroundDisplayMode: .always))
        }
    }
}

// MARK: - Page 1: Welcome

struct WelcomePageView: View {
    var body: some View {
        VStack(spacing: 30) {
            Spacer()
            
            // App icon/logo
            ZStack {
                Circle()
                    .fill(.white.opacity(0.2))
                    .frame(width: 150, height: 150)
                
                Image(systemName: "waveform.circle.fill")
                    .font(.system(size: 80))
                    .foregroundStyle(.white)
            }
            
            VStack(spacing: 16) {
                Text("Welcome to Feedcast")
                    .font(.system(size: 40, weight: .bold))
                    .foregroundStyle(.white)
                    .multilineTextAlignment(.center)
                
                Text("Your AI-Powered Personal Podcast")
                    .font(.title3)
                    .foregroundStyle(.white.opacity(0.9))
                    .multilineTextAlignment(.center)
            }
            
            VStack(spacing: 12) {
                FeatureBadge(icon: "sparkles", text: "AI Generated Content")
                FeatureBadge(icon: "person.fill", text: "Personalized for You")
                FeatureBadge(icon: "bubble.left.and.bubble.right.fill", text: "Interactive Chat")
            }
            .padding(.top, 20)
            
            Spacer()
            
            Text("Swipe to continue")
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.7))
                .padding(.bottom, 50)
        }
        .padding()
    }
}

// MARK: - Page 2: How It Works

struct HowItWorksPageView: View {
    var body: some View {
        VStack(spacing: 40) {
            Spacer()
            
            Text("How It Works")
                .font(.system(size: 36, weight: .bold))
                .foregroundStyle(.white)
            
            VStack(spacing: 30) {
                StepCard(
                    number: "1",
                    icon: "star.fill",
                    title: "Choose Your Interests",
                    description: "Tell us what topics you care about"
                )
                
                StepCard(
                    number: "2",
                    icon: "sparkles",
                    title: "AI Creates Your Podcast",
                    description: "We generate personalized content daily"
                )
                
                StepCard(
                    number: "3",
                    icon: "headphones",
                    title: "Listen & Chat",
                    description: "Enjoy your podcast and ask questions"
                )
            }
            
            Spacer()
            
            Text("Swipe to continue")
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.7))
                .padding(.bottom, 50)
        }
        .padding()
    }
}

// MARK: - Page 3: Basic Info

struct BasicInfoPageView: View {
    @ObservedObject var viewModel: OnboardingViewModel
    
    var body: some View {
        VStack(spacing: 30) {
            VStack(spacing: 12) {
                Text("Tell us about yourself")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundStyle(.white)
                    .multilineTextAlignment(.center)
                
                Text("This helps us personalize your content")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.9))
                    .multilineTextAlignment(.center)
            }
            .padding(.top, 60)
            
            ScrollView {
                VStack(spacing: 20) {
                    // Country Picker
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Country")
                            .font(.subheadline)
                            .foregroundStyle(.white)
                        
                        Menu {
                            ForEach(OnboardingViewModel.countries, id: \.self) { country in
                                Button(country) {
                                    viewModel.country = country
                                }
                            }
                        } label: {
                            HStack {
                                Text(viewModel.country.isEmpty ? "Select country" : viewModel.country)
                                    .foregroundStyle(viewModel.country.isEmpty ? .gray : .primary)
                                Spacer()
                                Image(systemName: "chevron.down")
                                    .foregroundStyle(.gray)
                            }
                            .padding()
                            .background(.white.opacity(0.95))
                            .cornerRadius(12)
                        }
                    }
                    
                    // Age Field
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Age")
                            .font(.subheadline)
                            .foregroundStyle(.white)
                        
                        TextField("Enter your age", text: $viewModel.age)
                            .keyboardType(.numberPad)
                            .padding()
                            .background(.white.opacity(0.95))
                            .cornerRadius(12)
                    }
                    
                    // Gender Picker
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Gender")
                            .font(.subheadline)
                            .foregroundStyle(.white)
                        
                        Menu {
                            ForEach(OnboardingViewModel.genders, id: \.self) { gender in
                                Button(gender) {
                                    viewModel.gender = gender
                                }
                            }
                        } label: {
                            HStack {
                                Text(viewModel.gender.isEmpty ? "Select gender" : viewModel.gender)
                                    .foregroundStyle(viewModel.gender.isEmpty ? .gray : .primary)
                                Spacer()
                                Image(systemName: "chevron.down")
                                    .foregroundStyle(.gray)
                            }
                            .padding()
                            .background(.white.opacity(0.95))
                            .cornerRadius(12)
                        }
                    }
                    
                    // Occupation Field
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Occupation")
                            .font(.subheadline)
                            .foregroundStyle(.white)
                        
                        TextField("e.g., Software Engineer", text: $viewModel.occupation)
                            .textInputAutocapitalization(.words)
                            .padding()
                            .background(.white.opacity(0.95))
                            .cornerRadius(12)
                    }
                }
                .padding(.horizontal)
            }
            
            Spacer()
            
            Text("Swipe to continue")
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.7))
                .padding(.bottom, 50)
        }
    }
}

// MARK: - Page 4: Select Interests

struct SelectInterestsPageView: View {
    @ObservedObject var viewModel: OnboardingViewModel
    
    var body: some View {
        VStack(spacing: 30) {
            VStack(spacing: 12) {
                Text("What interests you?")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundStyle(.white)
                    .multilineTextAlignment(.center)
                
                Text("Select at least 3 topics to personalize your podcasts")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.9))
                    .multilineTextAlignment(.center)
            }
            .padding(.top, 60)
            
            ScrollView {
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: 12) {
                    ForEach(OnboardingViewModel.availableInterests) { interest in
                        InterestChip(
                            interest: interest,
                            isSelected: viewModel.selectedInterests.contains(interest.id)
                        ) {
                            viewModel.toggleInterest(interest)
                        }
                    }
                }
                .padding(.horizontal)
            }
            
            Spacer()
            
            VStack(spacing: 12) {
                Text("\(viewModel.selectedInterests.count) selected")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.7))
                
                if viewModel.selectedInterests.count < 3 {
                    Text("Select at least 3 to continue")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.6))
                }
            }
            .padding(.bottom, 50)
        }
    }
}

// MARK: - Page 5: News Sources

struct NewsSourcesPageView: View {
    @ObservedObject var viewModel: OnboardingViewModel
    
    var body: some View {
        VStack(spacing: 30) {
            VStack(spacing: 12) {
                Text("What do you read?")
                    .font(.system(size: 32, weight: .bold))
                    .foregroundStyle(.white)
                    .multilineTextAlignment(.center)
                
                Text("Select news sources you follow")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.9))
                    .multilineTextAlignment(.center)
            }
            .padding(.top, 60)
            
            ScrollView {
                LazyVGrid(columns: [
                    GridItem(.flexible()),
                    GridItem(.flexible())
                ], spacing: 12) {
                    ForEach(OnboardingViewModel.availableNewsSources, id: \.self) { source in
                        NewsSourceChip(
                            source: source,
                            isSelected: viewModel.selectedNewsSources.contains(source)
                        ) {
                            viewModel.toggleNewsSource(source)
                        }
                    }
                }
                .padding(.horizontal)
            }
            
            Spacer()
            
            VStack(spacing: 12) {
                Text("\(viewModel.selectedNewsSources.count) selected")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.7))
                
                Text("Select your preferred news sources")
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.6))
            }
            .padding(.bottom, 50)
        }
    }
}

// MARK: - Page 6: Daily Podcast

struct DailyPodcastPageView: View {
    @ObservedObject var viewModel: OnboardingViewModel
    
    var body: some View {
        VStack(spacing: 40) {
            Spacer()
            
            Image(systemName: "sunrise.fill")
                .font(.system(size: 80))
                .foregroundStyle(.white)
            
            VStack(spacing: 16) {
                Text("Daily Podcast")
                    .font(.system(size: 36, weight: .bold))
                    .foregroundStyle(.white)
                
                Text("Get a fresh, personalized podcast every day")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.9))
                    .multilineTextAlignment(.center)
            }
            
            VStack(spacing: 20) {
                Toggle(isOn: $viewModel.dailyPodcastEnabled) {
                    HStack {
                        Image(systemName: "calendar.badge.clock")
                            .foregroundStyle(.white)
                        Text("Enable Daily Podcasts")
                            .foregroundStyle(.white)
                    }
                }
                .toggleStyle(SwitchToggleStyle(tint: .white))
                .padding()
                .background(.white.opacity(0.2))
                .cornerRadius(12)
                
                if viewModel.dailyPodcastEnabled {
                    DatePicker(
                        "Preferred Time",
                        selection: $viewModel.dailyPodcastTime,
                        displayedComponents: .hourAndMinute
                    )
                    .datePickerStyle(.wheel)
                    .labelsHidden()
                    .colorScheme(.dark)
                    .padding()
                    .background(.white.opacity(0.2))
                    .cornerRadius(12)
                }
            }
            .padding(.horizontal, 30)
            
            Spacer()
            
            Text("Swipe to continue")
                .font(.subheadline)
                .foregroundStyle(.white.opacity(0.7))
                .padding(.bottom, 50)
        }
        .padding()
    }
}

// MARK: - Page 5: Get Started

struct GetStartedPageView: View {
    @ObservedObject var viewModel: OnboardingViewModel
    @EnvironmentObject var userService: UserService
    @State private var isLoading = false
    @State private var errorMessage: String?
    let onComplete: () -> Void
    
    var body: some View {
        VStack(spacing: 40) {
            Spacer()
            
            Image(systemName: "checkmark.circle.fill")
                .font(.system(size: 80))
                .foregroundStyle(.white)
            
            VStack(spacing: 16) {
                Text("You're All Set!")
                    .font(.system(size: 36, weight: .bold))
                    .foregroundStyle(.white)
                
                Text("Ready to experience AI-powered podcasts?")
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.9))
                    .multilineTextAlignment(.center)
            }
            
            VStack(spacing: 16) {
                InfoRow(icon: "star.fill", text: "\(viewModel.selectedInterests.count) interests selected")
                InfoRow(icon: "calendar", text: viewModel.dailyPodcastEnabled ? "Daily podcasts enabled" : "Daily podcasts disabled")
            }
            .padding(.vertical, 20)
            
            if let error = errorMessage {
                Text(error)
                    .font(.subheadline)
                    .foregroundStyle(.red)
                    .padding(.horizontal)
            }
            
            Spacer()
            
            Button {
                Task {
                    await savePreferences()
                }
            } label: {
                Group {
                    if isLoading {
                        ProgressView()
                            .tint(.white)
                    } else {
                        Text("Continue to App")
                            .font(.headline)
                    }
                }
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .padding()
                .background(.blue)
                .cornerRadius(12)
            }
            .disabled(isLoading)
            .padding(.horizontal, 30)
            .padding(.bottom, 50)
        }
    }
    
    private func savePreferences() async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }
        
        guard let user = userService.currentUser else {
            errorMessage = "User not found"
            return
        }
        
        print("💾 Saving user preferences from onboarding...")
        
        do {
            // Add selected interests to user profile
            let interestObjects = OnboardingViewModel.availableInterests.filter { 
                viewModel.selectedInterests.contains($0.id) 
            }
            
            for interest in interestObjects {
                try await userService.addInterest(interest)
            }
            
            // Update user profile with all information
            let updatedUser = User(
                id: user.id,
                name: user.name,
                email: user.email,
                country: viewModel.country.isEmpty ? nil : viewModel.country,
                age: viewModel.ageInt,
                gender: viewModel.gender.isEmpty ? nil : viewModel.gender,
                occupation: viewModel.occupation.isEmpty ? nil : viewModel.occupation,
                newsSources: Array(viewModel.selectedNewsSources),
                interests: interestObjects,
                dailyPodcastEnabled: viewModel.dailyPodcastEnabled,
                dailyPodcastTime: viewModel.dailyPodcastTime,
                createdAt: user.createdAt
            )
            
            try await userService.updateUser(updatedUser)
            
            print("✅ User preferences saved")
            onComplete()
        } catch {
            print("❌ Failed to save preferences: \(error)")
            errorMessage = "Failed to save preferences: \(error.localizedDescription)"
        }
    }
}

// MARK: - Supporting Components

struct FeatureBadge: View {
    let icon: String
    let text: String
    
    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: icon)
                .font(.title3)
            Text(text)
                .font(.subheadline)
        }
        .foregroundStyle(.white)
        .padding(.horizontal, 20)
        .padding(.vertical, 10)
        .background(.white.opacity(0.2))
        .cornerRadius(20)
    }
}

struct StepCard: View {
    let number: String
    let icon: String
    let title: String
    let description: String
    
    var body: some View {
        HStack(spacing: 16) {
            ZStack {
                Circle()
                    .fill(.white.opacity(0.3))
                    .frame(width: 50, height: 50)
                
                Text(number)
                    .font(.title2)
                    .fontWeight(.bold)
                    .foregroundStyle(.white)
            }
            
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Image(systemName: icon)
                    Text(title)
                        .fontWeight(.semibold)
                }
                .foregroundStyle(.white)
                
                Text(description)
                    .font(.subheadline)
                    .foregroundStyle(.white.opacity(0.8))
            }
            
            Spacer()
        }
        .padding()
        .background(.white.opacity(0.15))
        .cornerRadius(16)
        .padding(.horizontal, 30)
    }
}

struct InterestChip: View {
    let interest: Interest
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            VStack(spacing: 8) {
                Text(interest.category.emoji)
                    .font(.system(size: 30))
                
                Text(interest.name)
                    .font(.caption)
                    .fontWeight(.medium)
                    .lineLimit(2)
                    .multilineTextAlignment(.center)
            }
            .foregroundStyle(isSelected ? .blue : .white)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 16)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isSelected ? .white : .white.opacity(0.2))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? .white : .clear, lineWidth: 2)
            )
        }
    }
}

struct NewsSourceChip: View {
    let source: String
    let isSelected: Bool
    let action: () -> Void
    
    var body: some View {
        Button(action: action) {
            HStack(spacing: 8) {
                Image(systemName: "newspaper.fill")
                    .font(.caption)
                
                Text(source)
                    .font(.caption)
                    .fontWeight(.medium)
                    .lineLimit(2)
                    .multilineTextAlignment(.leading)
            }
            .foregroundStyle(isSelected ? .blue : .white)
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 12)
            .padding(.vertical, 12)
            .background(
                RoundedRectangle(cornerRadius: 12)
                    .fill(isSelected ? .white : .white.opacity(0.2))
            )
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? .white : .clear, lineWidth: 2)
            )
        }
    }
}

struct InfoRow: View {
    let icon: String
    let text: String
    
    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundStyle(.white)
            Text(text)
                .foregroundStyle(.white.opacity(0.9))
        }
    }
}

// MARK: - ViewModel

@MainActor
class OnboardingViewModel: ObservableObject {
    // Basic Info
    @Published var country = ""
    @Published var age = ""
    @Published var gender = ""
    @Published var occupation = ""
    
    // Interests
    @Published var selectedInterests: Set<String> = []
    
    // News Sources
    @Published var selectedNewsSources: Set<String> = []
    
    // Daily Podcast
    @Published var dailyPodcastEnabled = true
    @Published var dailyPodcastTime = Calendar.current.date(bySettingHour: 8, minute: 0, second: 0, of: Date()) ?? Date()
    
    static let availableInterests: [Interest] = [
        Interest(name: "Artificial Intelligence", category: .technology),
        Interest(name: "Machine Learning", category: .technology),
        Interest(name: "Space Exploration", category: .science),
        Interest(name: "Climate Change", category: .science),
        Interest(name: "Quantum Physics", category: .science),
        Interest(name: "Startup Strategy", category: .business),
        Interest(name: "Leadership", category: .business),
        Interest(name: "Investing", category: .business),
        Interest(name: "Fitness", category: .health),
        Interest(name: "Nutrition", category: .health),
        Interest(name: "Mental Health", category: .health),
        Interest(name: "Philosophy", category: .education),
        Interest(name: "History", category: .education),
        Interest(name: "Literature", category: .arts),
        Interest(name: "Music", category: .arts),
        Interest(name: "Football", category: .sports),
        Interest(name: "Basketball", category: .sports),
        Interest(name: "Movies", category: .entertainment),
        Interest(name: "Gaming", category: .entertainment),
        Interest(name: "Politics", category: .politics)
    ]
    
    static let availableNewsSources = [
        "BBC News",
        "CNN",
        "The New York Times",
        "The Guardian",
        "Reuters",
        "Al Jazeera",
        "NPR",
        "Bloomberg",
        "The Wall Street Journal",
        "The Economist",
        "Associated Press",
        "Financial Times",
        "Fox News",
        "MSNBC",
        "The Washington Post",
        "Politico",
        "Vice News",
        "TechCrunch",
        "Wired",
        "The Verge"
    ]
    
    static let countries = [
        "Afghanistan", "Albania", "Algeria", "Andorra", "Angola",
        "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan",
        "Bahamas", "Bahrain", "Bangladesh", "Barbados", "Belarus",
        "Belgium", "Belize", "Benin", "Bhutan", "Bolivia",
        "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
        "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada",
        "Cape Verde", "Central African Republic", "Chad", "Chile", "China",
        "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia",
        "Cuba", "Cyprus", "Czech Republic", "Denmark", "Djibouti",
        "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador",
        "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia",
        "Fiji", "Finland", "France", "Gabon", "Gambia",
        "Georgia", "Germany", "Ghana", "Greece", "Grenada",
        "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti",
        "Honduras", "Hungary", "Iceland", "India", "Indonesia",
        "Iran", "Iraq", "Ireland", "Israel", "Italy",
        "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya",
        "Kiribati", "Kosovo", "Kuwait", "Kyrgyzstan", "Laos",
        "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya",
        "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar", "Malawi",
        "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands",
        "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova",
        "Monaco", "Mongolia", "Montenegro", "Morocco", "Mozambique",
        "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands",
        "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea",
        "North Macedonia", "Norway", "Oman", "Pakistan", "Palau",
        "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru",
        "Philippines", "Poland", "Portugal", "Qatar", "Romania",
        "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia", "Saint Vincent and the Grenadines",
        "Samoa", "San Marino", "Saudi Arabia", "Senegal", "Serbia",
        "Seychelles", "Sierra Leone", "Singapore", "Slovakia", "Slovenia",
        "Solomon Islands", "Somalia", "South Africa", "South Korea", "South Sudan",
        "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden",
        "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania",
        "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago",
        "Tunisia", "Turkey", "Turkmenistan", "Tuvalu", "Uganda",
        "Ukraine", "United Arab Emirates", "United Kingdom", "United States", "Uruguay",
        "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam",
        "Yemen", "Zambia", "Zimbabwe"
    ]
    
    static let genders = ["Male", "Female", "Non-binary", "Prefer not to say"]
    
    func toggleInterest(_ interest: Interest) {
        if selectedInterests.contains(interest.id) {
            selectedInterests.remove(interest.id)
        } else {
            selectedInterests.insert(interest.id)
        }
    }
    
    func toggleNewsSource(_ source: String) {
        if selectedNewsSources.contains(source) {
            selectedNewsSources.remove(source)
        } else {
            selectedNewsSources.insert(source)
        }
    }
    
    var canProceed: Bool {
        selectedInterests.count >= 3
    }
    
    var ageInt: Int? {
        Int(age)
    }
}

#Preview {
    OnboardingView(onComplete: {})
}

