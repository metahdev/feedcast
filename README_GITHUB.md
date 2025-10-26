# Feedcast 🎙️

> AI-personalized podcast app that generates custom content daily based on your interests

<div align="center">

![Swift](https://img.shields.io/badge/Swift-5.9-orange)
![iOS](https://img.shields.io/badge/iOS-17.0+-blue)
![SwiftUI](https://img.shields.io/badge/SwiftUI-Latest-green)
![Supabase](https://img.shields.io/badge/Supabase-Integrated-success)

**Built for Hackathon 2025**

</div>

## 🌟 Features

- 🎨 **Beautiful Onboarding** - 5-page interactive onboarding flow
- 🔐 **Secure Authentication** - Email/password with Supabase
- ⭐ **Interest Management** - 20+ topics across multiple categories
- 🎙️ **AI-Generated Podcasts** - Personalized content (ready for FetchAI)
- 💬 **Interactive Chat** - Ask questions about podcast content
- 📱 **Modern iOS Design** - SwiftUI with Apple-inspired UI
- 🔒 **Data Security** - Row Level Security with Supabase

## 📱 Screenshots

*Coming soon - add your app screenshots here!*

## 🚀 Quick Start

### Prerequisites

- macOS Ventura (13.0) or later
- Xcode 15.0+
- iOS 17.0+ device or simulator
- [Supabase](https://supabase.com) account (free tier works!)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/feedcast.git
   cd feedcast
   ```

2. **Set up configuration**
   ```bash
   cp feedcast/Config.swift.example feedcast/Config.swift
   ```
   
   Then open `Config.swift` and add your Supabase credentials:
   ```swift
   static let supabaseURL = "https://xxxxx.supabase.co"
   static let supabaseAnonKey = "your-anon-key-here"
   ```

3. **Add Supabase SDK**
   - Open `feedcast.xcodeproj` in Xcode
   - File → Add Package Dependencies
   - Enter: `https://github.com/supabase/supabase-swift`
   - Click Add Package

4. **Set up Supabase database**
   - See [SUPABASE_SETUP.md](SUPABASE_SETUP.md) for SQL schema
   - Run the provided SQL in your Supabase dashboard

5. **Build and run**
   ```
   Press ⌘ + R in Xcode
   ```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get running in minutes
- **[SUPABASE_SETUP.md](SUPABASE_SETUP.md)** - Complete backend setup
- **[INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)** - FetchAI & LiveKit integration
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Technical deep dive
- **[GITHUB_SETUP.md](GITHUB_SETUP.md)** - Security best practices

## 🏗️ Architecture

```
feedcast/
├── Models/          # Data structures
├── Services/        # Business logic & API calls
├── ViewModels/      # State management (MVVM)
├── Views/           # SwiftUI interfaces
└── Config.swift     # Configuration (not committed)
```

**Design Pattern:** MVVM (Model-View-ViewModel)
**Backend:** Supabase (Auth + PostgreSQL)
**Future:** FetchAI for content, LiveKit for streaming

## 🔧 Tech Stack

- **Language:** Swift 5.9
- **UI Framework:** SwiftUI
- **Architecture:** MVVM
- **Backend:** Supabase
- **Database:** PostgreSQL (via Supabase)
- **Auth:** Supabase Auth
- **Future:** FetchAI, LiveKit

## 🎯 Roadmap

### ✅ Phase 1: Core App (Complete)
- [x] MVVM architecture
- [x] Beautiful UI/UX
- [x] Onboarding flow
- [x] Authentication
- [x] Interest management
- [x] Player with chat interface

### 🚧 Phase 2: Backend Integration (In Progress)
- [x] Supabase authentication
- [x] User profiles
- [ ] Podcast persistence
- [ ] Chat history persistence

### 🎯 Phase 3: AI Integration (Planned)
- [ ] FetchAI content generation
- [ ] Intelligent chat responses
- [ ] Cross-conversation learning
- [ ] Daily podcast automation

### 🎵 Phase 4: Audio Streaming (Planned)
- [ ] LiveKit integration
- [ ] Real-time audio playback
- [ ] Background audio support
- [ ] Offline caching

## 🤝 Contributing

This is a hackathon project, but contributions are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

**Note:** Never commit `Config.swift` with real credentials!

## 🔒 Security

- API keys are kept in `Config.swift` (git-ignored)
- Row Level Security (RLS) enabled on all tables
- User data is isolated per user
- See [GITHUB_SETUP.md](GITHUB_SETUP.md) for security best practices

## 📝 License

This project is created for hackathon purposes. Feel free to use and modify.

## 🙏 Acknowledgments

- **Supabase** - Amazing backend platform
- **Apple** - SwiftUI and design inspiration
- **FetchAI** - AI agent framework (integration pending)
- **LiveKit** - Real-time audio streaming (integration pending)

## 👥 Team

Built with ❤️ for Hackathon 2025

## 📧 Contact

For questions or collaboration opportunities:
- Open an issue on GitHub
- Reach out to the team

---

<div align="center">

**⭐ Star this repo if you found it helpful!**

Made with SwiftUI | Powered by Supabase

</div>

