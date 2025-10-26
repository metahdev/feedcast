# Supabase Setup Guide for Feedcast 🚀

## Quick Setup (3 Steps)

### Step 1: Add Supabase SDK to Xcode

1. Open your project in Xcode
2. Go to **File → Add Package Dependencies...**
3. Enter this URL: `https://github.com/supabase/supabase-swift`
4. Click **Add Package**
5. Select **Supabase** library and click **Add Package**

### Step 2: Run SQL in Supabase

1. Go to [supabase.com](https://supabase.com) and sign in
2. Create a new project (or use existing)
3. Go to **SQL Editor** in left sidebar
4. Click **New Query**
5. Copy and paste this SQL:

```sql
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT,
    email TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Interests table
CREATE TABLE interests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    is_active BOOLEAN DEFAULT true
);

-- Podcasts table
CREATE TABLE podcasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    interests TEXT[] DEFAULT '{}',
    is_daily BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Episodes table
CREATE TABLE episodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    duration REAL NOT NULL,
    audio_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Chat messages table
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    episode_id UUID REFERENCES episodes(id),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    sender TEXT NOT NULL CHECK (sender IN ('user', 'ai')),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_interests_user_id ON interests(user_id);
CREATE INDEX idx_podcasts_user_id ON podcasts(user_id);
CREATE INDEX idx_episodes_podcast_id ON episodes(podcast_id);
CREATE INDEX idx_chat_messages_podcast_id ON chat_messages(podcast_id);
CREATE INDEX idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp DESC);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE interests ENABLE ROW LEVEL SECURITY;
ALTER TABLE podcasts ENABLE ROW LEVEL SECURITY;
ALTER TABLE episodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY "Users can manage own data" ON users
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "Users can manage own interests" ON interests
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own podcasts" ON podcasts
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own episodes" ON episodes
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM podcasts 
            WHERE podcasts.id = episodes.podcast_id 
            AND podcasts.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can manage own chat messages" ON chat_messages
    FOR ALL USING (auth.uid() = user_id);
```

6. Click **Run** or press `Ctrl/Cmd + Enter`
7. You should see "Success. No rows returned"

### Step 3: Configure Your App

1. In Supabase, go to **Settings → API**
2. Copy your **Project URL** (looks like: `https://xxxxx.supabase.co`)
3. Copy your **anon public** key (long JWT token)
4. Open `feedcast/Config.swift` in Xcode
5. Replace the placeholder values:

```swift
static let supabaseURL = "https://xxxxx.supabase.co"  // Your Project URL
static let supabaseAnonKey = "eyJhbGc..."              // Your anon key
```

6. Save the file

## ✅ You're Done!

Run the app (`⌘ + R`) and you'll see the onboarding flow!

## 🎯 What Works Now

### With Supabase Configured:
✅ Beautiful onboarding flow (5 pages)
✅ Interest selection
✅ Sign up with email/password
✅ Sign in for returning users
✅ User data saved to Supabase
✅ Interests saved to database
✅ Row Level Security protecting user data

### Still Using Dummy Data (for now):
⚠️ Podcasts (not connected to Supabase yet)
⚠️ Chat messages (not persisted yet)
⚠️ Audio playback (simulated)

## 📱 Testing the Flow

### New User Experience:
1. Launch app → See onboarding
2. Page 1: Welcome screen
3. Page 2: How it works
4. Page 3: Select interests (choose at least 3)
5. Page 4: Daily podcast settings
6. Page 5: Create account or Sign in
7. Enter email + password + name
8. Tap "Create Account"
9. You're in! 🎉

### Returning User:
1. Launch app → See auth screen
2. Enter your email + password
3. Tap "Sign In"
4. Your interests and data are loaded from Supabase!

### Demo Mode (No Supabase):
If you don't configure Supabase:
- App detects this and uses dummy data
- You can still see the full onboarding UX
- Click "Continue without account (Demo)"
- Everything works with local data

## 🔍 Verify It's Working

### Check Supabase Dashboard:
1. Go to **Table Editor** in Supabase
2. Click on **users** table → You should see your user!
3. Click on **interests** table → You should see your selected interests!

### Check in App:
1. After signing up, go to Interests tab
2. Your selected interests should be there
3. Sign out and sign back in
4. Your data should persist!

## 🎨 Onboarding Features

### Page 1: Welcome
- App branding
- Feature badges
- Gradient background

### Page 2: How It Works
- 3-step visual guide
- Clear value proposition

### Page 3: Interest Selection
- 20 pre-defined interests
- Category-based organization
- Visual selection with emojis
- Minimum 3 required

### Page 4: Daily Podcast
- Toggle for daily generation
- Time picker for preferred delivery
- Saves preferences

### Page 5: Get Started
- Summary of selections
- Create account or Sign in
- Skip option for demo

## 🐛 Troubleshooting

### App won't build after adding Supabase:
- Make sure you added the package to the correct target
- Clean build folder (`⌘ + Shift + K`)
- Rebuild (`⌘ + B`)

### "Supabase not configured" error:
- Check Config.swift has real values (not "YOUR_...")
- Make sure you saved the file
- Rebuild the project

### Sign up fails:
- Check your Supabase project is active
- Verify SQL ran successfully (check Tables in dashboard)
- Check email format is valid
- Password must be at least 6 characters

### User data not persisting:
- Check RLS policies in Supabase (Settings → Policies)
- Make sure you're signed in (check Supabase Auth dashboard)
- Check table has data (Table Editor)

### Can't see onboarding again:
- Delete app from simulator/device
- Or: Change `@AppStorage("hasCompletedOnboarding")` to `false` in feedcastApp.swift

## 🔒 Security Notes

### Safe to commit:
✅ Config.swift structure (with placeholders)
✅ All code files
✅ SQL schema

### DO NOT commit:
❌ Real Supabase URL
❌ Real API keys
❌ Add Config.swift to .gitignore if you fill in real values

### For production:
- Use environment variables
- Enable email verification in Supabase
- Set up proper password reset flow
- Add rate limiting
- Configure CORS properly

## 📈 Next Steps

After Supabase is working:
1. ✅ Connect PodcastService to Supabase (save generated podcasts)
2. ✅ Connect ChatService to Supabase (persist conversations)
3. ✅ Integrate FetchAI for content generation
4. ✅ Add LiveKit for audio streaming

## 💡 Tips

- **Use a test email** for development (e.g., `test@example.com`)
- **Passwords are real** - Supabase sends verification emails
- **Disable email verification** in Supabase for faster testing:
  - Settings → Auth → Enable Email Confirmations → OFF
- **Check Supabase logs** if something fails:
  - Logs & Analytics → View logs

## ✨ You're Ready!

Your app now has:
- Professional onboarding
- Real authentication
- Database-backed user profiles
- Secure data storage
- Beautiful UX

Run the app and enjoy your fully functional onboarding experience! 🎉

