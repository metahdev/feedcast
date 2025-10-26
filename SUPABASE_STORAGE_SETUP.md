# Supabase Storage Setup for Audio Files

## Overview

Audio files are now uploaded to **Supabase Storage** (cloud storage) instead of being saved locally. This allows:
- ✅ Audio accessible from any device
- ✅ Streaming from cloud URLs
- ✅ No local storage issues
- ✅ Survives app reinstalls
- ✅ Works across multiple devices

## Setup Steps

### 1. Create Storage Bucket

1. **Go to your Supabase Dashboard**
   - Navigate to: https://supabase.com/dashboard

2. **Open your project**
   - Select the feedcast project

3. **Go to Storage**
   - Click "Storage" in the left sidebar

4. **Create New Bucket**
   - Click "New bucket" button
   - **Bucket name:** `podcast-audio`
   - **Public bucket:** ✅ **YES** (Check this!)
   - Click "Create bucket"

### 2. Set Bucket Policies

The bucket needs to be publicly readable so audio can stream.

1. **Click on the `podcast-audio` bucket**

2. **Go to Policies tab**

3. **Add Policy for SELECT (Read)**
   - Click "New Policy"
   - Select "Create a custom policy"
   - **Policy name:** `Public read access`
   - **Allowed operation:** SELECT
   - **Policy definition:**
   ```sql
   ((bucket_id = 'podcast-audio'::text) AND (auth.role() = 'anon'::text))
   ```
   - Or simply enable: "Allow public access"

4. **Add Policy for INSERT (Upload)**
   - Click "New Policy"
   - Select "Create a custom policy"  
   - **Policy name:** `Authenticated users can upload`
   - **Allowed operation:** INSERT
   - **Policy definition:**
   ```sql
   ((bucket_id = 'podcast-audio'::text) AND (auth.role() = 'authenticated'::text))
   ```

5. **Add Policy for DELETE**
   - Click "New Policy"
   - **Policy name:** `Users can delete own files`
   - **Allowed operation:** DELETE
   - **Policy definition:**
   ```sql
   ((bucket_id = 'podcast-audio'::text) AND (auth.role() = 'authenticated'::text))
   ```

### 3. Quick Setup (SQL Editor)

Alternatively, run this in the Supabase SQL Editor:

```sql
-- Create the storage bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('podcast-audio', 'podcast-audio', true)
ON CONFLICT (id) DO NOTHING;

-- Allow public read access
CREATE POLICY "Public read access"
ON storage.objects FOR SELECT
USING (bucket_id = 'podcast-audio');

-- Allow authenticated users to upload
CREATE POLICY "Authenticated users can upload"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'podcast-audio' AND
  auth.role() = 'authenticated'
);

-- Allow users to delete their own files
CREATE POLICY "Users can delete own files"
ON storage.objects FOR DELETE
USING (
  bucket_id = 'podcast-audio' AND
  auth.role() = 'authenticated'
);
```

## What Happens Now

### During Podcast Generation

1. **GPT generates script** → Text content
2. **TTS converts to audio** → MP3 data (in chunks if needed)
3. **Upload to Supabase Storage** → `podcast-audio/podcasts/[filename].mp3`
4. **Get public URL** → `https://[project].supabase.co/storage/v1/object/public/podcast-audio/podcasts/[filename].mp3`
5. **Save URL to database** → `episodes.audio_url`

### Console Output

You'll see:
```
☁️ Uploading audio to Supabase Storage...
📤 Uploading to: podcasts/abc123_def456.mp3
📊 File size: 1523456 bytes (1.52 MB)
✅ Audio uploaded successfully
🔗 Public URL: https://[project].supabase.co/storage/v1/object/public/podcast-audio/podcasts/abc123_def456.mp3
```

## File Structure in Storage

```
podcast-audio/
  └── podcasts/
      ├── [podcastId]_[uuid1].mp3
      ├── [podcastId]_[uuid2].mp3
      └── [podcastId]_[uuid3].mp3
```

## Benefits

### Before (Local Storage)
❌ Files only on device
❌ Lost on reinstall
❌ Can't access from other devices
❌ Local file path in database

### After (Cloud Storage)
✅ Files in cloud
✅ Persistent across reinstalls
✅ Access from any device
✅ Public URL for streaming
✅ Can implement caching later
✅ Can download for offline use

## Testing

After setup:

1. **Clean and rebuild** the app
2. **Generate a podcast**
3. **Check console** for upload logs
4. **Verify in Supabase:**
   - Go to Storage → podcast-audio
   - You should see uploaded MP3 files
   - Click a file to get its public URL
   - Paste URL in browser to test playback

## Storage Limits

### Free Tier
- **Storage:** 1 GB
- **Bandwidth:** 2 GB/month
- **File size:** 50 MB max per file

### Typical Podcast Sizes
- 5-minute podcast: ~1-2 MB
- You can store ~500-1000 podcasts in free tier

### If You Exceed Limits
1. Upgrade Supabase plan
2. Implement auto-deletion of old podcasts
3. Compress audio more (use lower bitrate)

## Troubleshooting

### Error: "Bucket 'podcast-audio' not found"

**Solution:** Create the bucket as described in Step 1 above.

### Error: "new row violates row-level security policy"

**Solution:** Make sure policies are set up correctly (Step 2 above).

### Error: "The resource already exists"

**Solution:** File with same name exists. This shouldn't happen with UUID filenames, but you can:
- Delete old file first
- Use a different filename

### Audio won't play in app

**Check:**
1. Is bucket public? (Check bucket settings)
2. Is URL valid? (Paste in browser to test)
3. Is file actually uploaded? (Check Storage in dashboard)
4. Check network connectivity

## Advanced: Custom Storage Backend

If you want to use a different storage provider:

1. Replace `uploadAudioToSupabase()` in `PodcastService.swift`
2. Upload to AWS S3, Cloudflare R2, etc.
3. Return the public URL
4. Rest of the code works the same!

## Security Note

Audio files are **publicly accessible** by design (anyone with the URL can stream them). This is normal for podcast audio. If you need private podcasts:

1. Set bucket to private (`public: false`)
2. Generate signed URLs with expiration
3. Update policies for user-specific access
4. Modify `getPublicURL()` to `createSignedUrl()`

---

**Status:** ✅ Cloud storage setup complete!

Now audio files are properly stored in the cloud and accessible from anywhere! 🎉

