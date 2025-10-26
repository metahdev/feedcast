# Feedcast - Quick Start Guide 🚀

Get up and running with Feedcast in minutes!

## Prerequisites

- **macOS**: Ventura (13.0) or later
- **Xcode**: 15.0 or later
- **iOS Device/Simulator**: iOS 17.0+

## Installation

### 1. Clone or Open Project

```bash
cd /Users/metah/Desktop/feedcast
```

### 2. Open in Xcode

```bash
open feedcast.xcodeproj
```

### 3. Build and Run

1. Select your target device (iPhone 15 or later recommended)
2. Press `⌘ + R` or click the ▶️ Run button
3. Wait for the build to complete

**That's it!** The app will launch with demo data.

## First Launch

On first launch, you'll see:
- ✅ Pre-populated podcast library with 4 podcasts
- ✅ 6 default interests (AI, ML, Space, Business, Fitness, Climate)
- ✅ Fully functional UI with dummy data

## Exploring the App

### 1. Library View (Home)

The main screen shows your podcast collection:
- **Today's Podcast**: Featured at the top
- **Your Library**: Grid of all podcasts
- **Search**: Find podcasts by title or interest
- **Sort**: Change order (newest, oldest, duration, title)
- **+** button: Generate new podcast (mock)
- **⭐** button: Manage interests

**Try this:**
1. Tap any podcast card to open the player
2. Use pull-to-refresh to reload
3. Long-press a podcast for delete option

### 2. Player View

Tap any podcast to see the player:
- **Playback Controls**: Play/pause, skip 15s back, 30s forward
- **Speed Control**: Tap the speed indicator (e.g., "1.00x") to change
- **Episodes List**: Tap to switch between episodes
- **Chat Button** (top-right): Open AI assistant chat

**Try this:**
1. Press play and watch the progress bar move
2. Skip forward/back with the buttons
3. Tap the message icon to open chat
4. Ask: "What is this podcast about?"

### 3. Chat Interface

While in player view:
1. Tap the message icon (top-right)
2. Chat panel slides up from bottom
3. Type a question and press send
4. AI responds with context-aware answers (simulated)

**Example questions:**
- "Summarize this podcast"
- "How long is this?"
- "When was this created?"
- "What topics are covered?"

### 4. Interests Management

From library, tap ⭐ or use the Interests tab:
- **Active Interests**: Currently enabled
- **Inactive Interests**: Disabled but saved
- **Add New**: + button to add interests
- **Toggle**: Switch to enable/disable
- **Delete**: Swipe left to remove

**Try this:**
1. Tap + to add a new interest
2. Enter "Quantum Physics"
3. Select category: Science
4. Tap Add
5. Toggle interests on/off

## Demo Features

Currently working with **dummy data**:

| Feature | Status | Notes |
|---------|--------|-------|
| Browse podcasts | ✅ Working | 4 demo podcasts |
| Play controls | ✅ Simulated | Timer-based, not real audio |
| Chat interface | ✅ Working | Rule-based responses |
| Interests CRUD | ✅ Working | In-memory only |
| Search/Filter | ✅ Working | Local filtering |
| Playback state | ✅ Working | Saved locally |

## What's NOT Connected Yet

These require backend integration:

- ❌ Real audio playback (needs LiveKit)
- ❌ AI podcast generation (needs FetchAI)
- ❌ Intelligent chat (needs FetchAI)
- ❌ User authentication (needs Supabase)
- ❌ Cloud sync (needs Supabase)
- ❌ Daily auto-generation

**See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for setup instructions.**

## Project Structure

```
feedcast/
├── Models/           # Data structures
├── Services/         # Business logic (dummy data)
├── ViewModels/       # State management
└── Views/            # SwiftUI interfaces
```

## Development Workflow

### Making Changes

1. **Edit any Swift file** in Xcode
2. **Build** (`⌘ + B`) to check for errors
3. **Run** (`⌘ + R`) to test

### Adding New Features

1. Create model in `Models/`
2. Add service logic in `Services/`
3. Create ViewModel in `ViewModels/`
4. Build UI in `Views/`

### Debugging

- **Print statements**: Use `print()` for console output
- **Breakpoints**: Click line number gutter in Xcode
- **SwiftUI Previews**: Check `#Preview` at bottom of view files

## Common Issues

### Build Errors

**Error**: Missing files
- **Fix**: Ensure all files are added to target
- Check File Inspector → Target Membership

**Error**: Module not found
- **Fix**: Clean build folder (`⌘ + Shift + K`)
- Rebuild (`⌘ + B`)

### Runtime Issues

**App crashes on launch**
- Check Console for error messages
- Ensure iOS deployment target is 17.0+

**UI not updating**
- Check `@Published` properties in ViewModels
- Verify `@StateObject` / `@ObservedObject` usage

**Chat not responding**
- This is expected - responses are simulated
- Check `ChatService.generateDummyResponse()` for logic

## Next Steps

### For Hackathon Demo

1. ✅ App is demo-ready with current features
2. Customize dummy data in services
3. Add your branding/colors
4. Practice the user flow

### For Production

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md):
1. Set up Supabase backend
2. Integrate FetchAI for content
3. Add LiveKit for audio
4. Deploy and test

## Customization

### Change Colors

Edit `Assets.xcassets/AccentColor.colorset/Contents.json`

### Modify Dummy Data

Edit these files:
- `Services/PodcastService.swift` → `loadDummyData()`
- `Services/UserService.swift` → `loadDummyUser()`
- `Services/ChatService.swift` → `loadDummyConversations()`

### Add New Interests

In `Services/UserService.swift`, update `loadDummyUser()`:

```swift
interests: [
    Interest(name: "Your Interest", category: .technology),
    // Add more...
]
```

## Testing Checklist

Before demo/presentation:

- [ ] App launches successfully
- [ ] Library shows podcasts
- [ ] Can tap and open player
- [ ] Play button works
- [ ] Chat opens and responds
- [ ] Can add/remove interests
- [ ] Search works
- [ ] UI looks good on target device

## Resources

- **Full Documentation**: [README.md](README.md)
- **Integration Guide**: [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Xcode Help**: Help → Xcode Help in menu
- **SwiftUI Docs**: [developer.apple.com/documentation/swiftui](https://developer.apple.com/documentation/swiftui)

## Support

For questions:
1. Check TODO comments in code
2. Review architecture in README.md
3. Consult integration guide for backend setup

---

**You're all set!** 🎉

The app is ready for hackathon demo. For production features, follow the integration guide.

Happy coding! 👨‍💻👩‍💻

