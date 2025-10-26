# Troubleshooting - Podcast Generation Issues

## Overview

If podcast generation isn't working, follow this guide to identify and fix the issue.

## Diagnostic Logging

I've added extensive logging to help debug issues. Open Xcode's **Console** (`Cmd+Shift+Y`) and look for these emoji-prefixed logs:

### Step-by-Step Logging

When you open the Library view with no podcasts, you should see:

```
📊 Debug: Found X active interests
📊 Debug: User authenticated: true/false
📊 Debug: Current user: user@email.com

📻 Library is empty. Auto-generating daily podcast...
📻 Using interests: AI, Technology, Science

🎙️ Starting podcast generation...
🎙️ Interests: AI, Technology, Science
🎙️ Is daily: true

✅ All checks passed, proceeding with generation
👤 User demographics: male, 22, United States

📡 Progress: Generating content with AI...
🤖 Calling OpenAI GPT...
✅ API key looks valid (length: XXX)
📤 Sending request to OpenAI GPT API...
📥 Received response with status code: 200
✅ Successfully decoded GPT response
✅ Got script text (length: XXXX characters)

🎤 Starting TTS conversion...
📤 Sending TTS request to OpenAI...
📥 TTS response status: 200
✅ TTS successful, audio data size: XXXXX bytes

✅ Daily podcast generated successfully!
```

## Common Issues & Solutions

### Issue 1: No Active Interests

**Symptoms:**
```
⚠️ No active interests found. Skipping auto-generation.
💡 Tip: Make sure you selected interests during onboarding
```

**Solution:**
1. User hasn't selected interests during onboarding
2. **Fix:** Delete the app and reinstall, or manually add interests:
   - Go to Profile tab (if available)
   - Add at least 1 interest
   - Make sure it's marked as active

**Quick Fix in Supabase:**
1. Open Supabase dashboard
2. Go to Table Editor → `interests`
3. Add a row:
   - `user_id`: your user's ID
   - `name`: "Artificial Intelligence"
   - `category`: "technology"
   - `is_active`: true

---

### Issue 2: User Not Authenticated

**Symptoms:**
```
📊 Debug: User authenticated: false
📊 Debug: Current user: nil
⚠️ User not authenticated. Skipping auto-generation.
```

**Solution:**
User hasn't completed onboarding/signup

**Fix:**
1. Check if `UserService.shared.isAuthenticated` is true
2. Check if onboarding was completed
3. Try logging out and back in
4. Check Supabase auth status

---

### Issue 3: OpenAI API Key Not Configured

**Symptoms:**
```
❌ OpenAI not configured
❌ API Key check: isEmpty=false, contains YOUR=true
```

**Solution:**
The OpenAI API key in Config.swift still contains placeholder text

**Fix:**
1. Open `/Users/metah/Desktop/feedcast/feedcast/Config.swift`
2. Find the line:
```swift
static let openAIAPIKey = "YOUR_OPENAI_API_KEY"
```
3. Replace with your actual key (already done):
```swift
static let openAIAPIKey = "sk-proj-49IPZ..."
```
4. Clean build folder: `Product → Clean Build Folder` (`Cmd+Shift+K`)
5. Rebuild: `Product → Build` (`Cmd+B`)

---

### Issue 4: OpenAI API Invalid Key Error

**Symptoms:**
```
❌ GPT Error (401): {
  "error": {
    "message": "Incorrect API key provided...",
    "type": "invalid_request_error"
  }
}
```

**Solution:**
The API key is invalid or expired

**Fix:**
1. Go to https://platform.openai.com/api-keys
2. Check if the key is still active
3. Generate a new key if needed
4. Update `Config.swift` with the new key
5. Clean and rebuild

---

### Issue 5: OpenAI Rate Limit Exceeded

**Symptoms:**
```
❌ GPT Error (429): {
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error"
  }
}
```

**Solution:**
You've exceeded OpenAI's rate limits

**Fix:**
1. Wait a few minutes
2. Check your OpenAI usage limits at https://platform.openai.com/usage
3. Upgrade your OpenAI plan if needed
4. For testing, try generating manually (+ button) with fewer interests

---

### Issue 6: Insufficient OpenAI Credits

**Symptoms:**
```
❌ GPT Error (429): {
  "error": {
    "message": "You exceeded your current quota",
    "type": "insufficient_quota"
  }
}
```

**Solution:**
Your OpenAI account has no credits

**Fix:**
1. Go to https://platform.openai.com/account/billing
2. Add a payment method
3. Add credits to your account
4. Wait a few minutes for credits to be available

---

### Issue 7: Network Connection Error

**Symptoms:**
```
❌ Failed to auto-generate podcast: NSURLErrorDomain Code=-1009
```

**Solution:**
No internet connection or network blocked

**Fix:**
1. Check internet connection
2. Try accessing https://api.openai.com in Safari
3. Check if firewall/VPN is blocking OpenAI
4. Try on a different network

---

### Issue 8: Supabase Connection Error

**Symptoms:**
```
❌ Supabase not configured
```
or
```
❌ Failed to save podcast to database
```

**Solution:**
Supabase isn't properly configured

**Fix:**
1. Check `Config.swift` has correct Supabase URL and key
2. Verify Supabase project is active
3. Check database tables exist (podcasts, episodes, interests)
4. Run SUPABASE_MIGRATION.sql if tables are missing

---

### Issue 9: Empty Library But No Auto-Generation

**Symptoms:**
- Library is empty
- No loading overlay appears
- No console logs at all

**Possible Causes:**

**A. Generation already attempted:**
Check for this log:
```
📊 Debug: hasCheckedForEmptyLibrary flag already set
```
**Fix:** Kill and restart the app completely

**B. LibraryViewModel not initialized:**
**Fix:** Check that LibraryView creates viewModel:
```swift
@StateObject private var viewModel = LibraryViewModel()
```

**C. Initial load hasn't completed:**
Wait a few seconds for `loadPodcasts()` to complete

---

### Issue 10: Generation Starts But Fails Silently

**Symptoms:**
- Loading overlay appears briefly
- Then disappears with no podcast created
- Error logs in console

**Solution:**
Check the specific error in console logs:
```
❌ Failed to auto-generate podcast: [error details]
```

**Common sub-issues:**
1. File permission error saving audio
2. Supabase insert error
3. Invalid audio data from TTS

**General Fix:**
1. Look at the specific error message
2. Check file permissions in Documents directory
3. Verify Supabase schema matches expected structure
4. Try manual generation (+ button) to isolate issue

---

## Debugging Checklist

Use this checklist to diagnose issues:

### Prerequisites
- [ ] Config.swift has valid OpenAI API key (not "YOUR_...")
- [ ] Config.swift has valid Supabase credentials
- [ ] Internet connection is working
- [ ] OpenAI account has credits
- [ ] Supabase database tables exist

### User State
- [ ] User completed onboarding
- [ ] User is authenticated (`UserService.shared.isAuthenticated == true`)
- [ ] User has at least 1 active interest
- [ ] User profile has data (gender, age, country)

### App State
- [ ] Library is actually empty (no podcasts in Supabase)
- [ ] Not already generating (`isGeneratingPodcast == false`)
- [ ] First load (`hasCheckedForEmptyLibrary == false`)

### Console Logs
- [ ] See "📊 Debug:" logs with correct info
- [ ] See "📻 Library is empty" message
- [ ] See "🎙️ Starting podcast generation" message
- [ ] See progress updates ("📡 Progress:")
- [ ] No error messages ("❌")

---

## Manual Test Steps

If auto-generation isn't working, try manual generation to isolate the issue:

1. **Open the app** and go to Library
2. **Tap the + button** in top right
3. **Select 2-3 interests**
4. **Tap "Generate"**
5. **Watch the console** for logs

If manual generation works but auto-generation doesn't:
- Check the `hasCheckedForEmptyLibrary` flag logic
- Verify `loadPodcasts()` completes before checking if empty
- Check that podcasts array is truly empty

---

## Testing in Isolation

### Test OpenAI API Key
```swift
// In OpenAIService
print("API Key: \(Config.openAIAPIKey.prefix(20))...")
print("Is configured: \(Config.isOpenAIConfigured)")
```

### Test User Interests
```swift
// In LibraryViewModel
let interests = UserService.shared.getInterests()
print("All interests: \(interests.count)")
print("Active interests: \(interests.filter { $0.isActive }.count)")
interests.forEach { print("  - \($0.name): active=\($0.isActive)") }
```

### Test Supabase Connection
```swift
// Try a simple query
let client = SupabaseManager.shared.client
let podcasts: [Podcast] = try await client
    .from("podcasts")
    .select()
    .execute()
    .value
print("Found \(podcasts.count) podcasts in database")
```

---

## Getting More Help

### Enable Verbose Logging

All the detailed logging is already enabled in the code. Just:
1. Open Xcode Console (`Cmd+Shift+Y`)
2. Run the app
3. Navigate to Library
4. Copy all console output
5. Look for error patterns

### Check API Status

- OpenAI: https://status.openai.com
- Supabase: https://status.supabase.com

### Verify API Keys

1. **OpenAI:**
   - Go to https://platform.openai.com/api-keys
   - Check key status
   - Test with curl:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer YOUR_KEY"
   ```

2. **Supabase:**
   - Go to Supabase dashboard → Settings → API
   - Verify URL and anon key match Config.swift

---

## Quick Fixes

### Reset Everything
```bash
# 1. Delete app from simulator
# 2. Delete derived data
rm -rf ~/Library/Developer/Xcode/DerivedData/feedcast-*

# 3. Clean and rebuild in Xcode
# Product → Clean Build Folder (Cmd+Shift+K)
# Product → Build (Cmd+B)

# 4. Run again
```

### Clear Supabase Data
```sql
-- In Supabase SQL Editor
DELETE FROM episodes;
DELETE FROM podcasts;
DELETE FROM interests;
-- User will remain, but library will be empty
```

### Fresh Start
1. Delete all data in Supabase
2. Delete app from simulator
3. Clean build folder
4. Run app
5. Complete onboarding with 3+ interests
6. Library should auto-generate

---

## Expected Behavior

When working correctly, you should see:

1. **App opens** → User authenticated
2. **Navigate to Library** → Podcasts array is empty
3. **Auto-generation starts** → Loading overlay appears
4. **Progress updates** every few seconds
5. **Generation completes** in 20-50 seconds
6. **Podcast appears** in library
7. **Can tap podcast** to play

---

## Still Not Working?

If you've tried everything above and it still doesn't work:

1. **Copy all console logs** from Xcode
2. **Note exact error messages**
3. **Check which step fails**:
   - Does it even detect empty library?
   - Does it start generation?
   - Does GPT call succeed?
   - Does TTS call succeed?
   - Does it fail saving?

4. **Look for the first ❌ in console logs**
   - That's usually where the problem is

5. **Verify all configurations**:
   - OpenAI API key is correct
   - Supabase credentials are correct
   - User has interests
   - Network is working

---

## Common Configuration Mistakes

### 1. Wrong Config File
**Problem:** Editing `Config.swift.example` instead of `Config.swift`
**Fix:** Make sure you're editing `/feedcast/Config.swift` (not the .example file)

### 2. API Key Has Spaces/Newlines
**Problem:** Copying API key added extra whitespace
**Fix:** API key should be one continuous string with no spaces

### 3. Supabase URL Wrong
**Problem:** Using project ref instead of full URL
**Fix:** Should be `https://[ref].supabase.co` not just `[ref]`

### 4. Wrong Supabase Key
**Problem:** Using service role key instead of anon key
**Fix:** Use the anon/public key from Supabase dashboard

---

## Success Indicators

When everything is working, you'll see:

```
📊 Debug: Found 3 active interests
📊 Debug: User authenticated: true
📊 Debug: Current user: user@example.com
📻 Library is empty. Auto-generating daily podcast...
📻 Using interests: AI, Space, Philosophy
🎙️ Starting podcast generation...
✅ All checks passed, proceeding with generation
👤 User demographics: male, 22, United States
🤖 Calling OpenAI GPT...
✅ API key looks valid (length: 164)
📤 Sending request to OpenAI GPT API...
📥 Received response with status code: 200
✅ Successfully decoded GPT response
✅ Got script text (length: 2847 characters)
📝 Full script length: 2847 characters
🎤 Starting TTS conversion...
📤 Sending TTS request to OpenAI...
📥 TTS response status: 200
✅ TTS successful, audio data size: 567234 bytes
💾 Saving to database...
✅ Daily podcast generated successfully!
```

That's the happy path! 🎉

