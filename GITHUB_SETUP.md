# GitHub Setup Guide - Keeping Your Credentials Safe 🔒

## ✅ Your Project is Now Secure!

I've configured your project to **prevent leaking Supabase credentials** to GitHub.

## 🛡️ What's Protected

### Files That Won't Be Committed:
- ❌ `Config.swift` (contains your real API keys)
- ❌ `.env` files
- ❌ `APIKeys.plist`

### Files That Will Be Committed:
- ✅ `Config.swift.example` (template with placeholders)
- ✅ All documentation
- ✅ All code files
- ✅ `.gitignore` (updated)

## 📋 Before You Push to GitHub

### Step 1: Verify Config.swift is Ignored

```bash
cd /Users/metah/Desktop/feedcast
git status
```

You should **NOT** see `Config.swift` in the list. If you do:

```bash
git rm --cached feedcast/Config.swift
```

### Step 2: Commit the Template

```bash
git add feedcast/Config.swift.example
git add .gitignore
git commit -m "Add config template and update gitignore"
```

### Step 3: Push Safely

```bash
git push origin main
```

## 🔧 Setup for Other Developers (or You on Another Machine)

When someone clones your repo:

### 1. Copy the Template
```bash
cd feedcast
cp feedcast/Config.swift.example feedcast/Config.swift
```

### 2. Add Their Credentials

Open `Config.swift` and replace:
```swift
static let supabaseURL = "YOUR_SUPABASE_URL"
static let supabaseAnonKey = "YOUR_SUPABASE_ANON_KEY"
```

With real values from their Supabase dashboard.

### 3. Never Commit Config.swift

Git will automatically ignore it (thanks to `.gitignore`).

## 🎯 Quick Reference

### Commands You'll Use

```bash
# Check what will be committed
git status

# If Config.swift appears (shouldn't happen):
git rm --cached feedcast/Config.swift

# Add changes
git add .

# Commit
git commit -m "Your message"

# Push
git push
```

## 🚨 What If I Already Committed My Keys?

If you accidentally pushed your Supabase credentials:

### 1. Rotate Your Keys IMMEDIATELY

1. Go to your Supabase Dashboard
2. Settings → API
3. Generate new keys
4. Update your local `Config.swift`

### 2. Remove from Git History

```bash
# Remove the file from history
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch feedcast/Config.swift" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (be careful!)
git push origin --force --all
```

**Note:** This rewrites history. Coordinate with team members if you're not working alone.

### 3. Alternative: BFG Repo-Cleaner

```bash
# Install BFG (if not installed)
brew install bfg

# Clone a fresh copy
git clone --mirror https://github.com/yourusername/feedcast.git

# Remove the file
bfg --delete-files Config.swift feedcast.git

# Clean up
cd feedcast.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push
git push
```

## 🔐 Best Practices

### ✅ DO:
- Keep `Config.swift` in `.gitignore`
- Use the `.example` template
- Share setup instructions, not credentials
- Rotate keys if they're ever exposed
- Use environment variables in production

### ❌ DON'T:
- Commit files with real API keys
- Share credentials in Slack/Discord/Email
- Hard-code secrets in any committed file
- Remove `.gitignore` entries

## 📱 For Production Apps

When you deploy to the App Store:

### Option 1: Build Configurations
Create different configs for Development/Production:
- `Config.swift` (local development)
- `Config-Production.swift` (production keys, never committed)

### Option 2: Xcode Environment Variables
Set secrets in Xcode scheme:
1. Edit Scheme → Run
2. Arguments → Environment Variables
3. Add keys there

### Option 3: Secrets Management Service
Use services like:
- AWS Secrets Manager
- HashiCorp Vault
- 1Password for Teams

## 🎓 Understanding the Security

### Why the `anon` key should be private:

Even though it's called "anonymous" and is meant for client-side use:
- It can still be rate-limited if abused
- It identifies YOUR specific Supabase project
- Bad actors could spam your database
- RLS policies are your main protection, but obscurity helps

### What's Actually Safe:

With Row Level Security (RLS) enabled:
- Users can only access their own data
- The `anon` key + RLS = secure
- But still, don't publish it publicly

## 🆘 Need Help?

### Common Issues:

**Q: I see Config.swift in `git status`**
A: Run `git rm --cached feedcast/Config.swift`

**Q: I already pushed it!**
A: Rotate your keys immediately, then clean history (see above)

**Q: My teammate can't build the app**
A: They need to copy `Config.swift.example` to `Config.swift` and add their keys

**Q: Where do I get Supabase keys?**
A: Dashboard → Settings → API → Copy "anon public" key

## ✅ You're All Set!

Your project is now safe to push to GitHub. The template file will help anyone set up their own environment without exposing your credentials.

**Ready to push?**

```bash
git add .
git commit -m "Initial commit with secure configuration"
git push origin main
```

🎉 **Your secrets are safe!**

