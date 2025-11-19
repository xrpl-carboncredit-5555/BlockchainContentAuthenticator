# Fetching Scheduled Videos Guide

## Overview

The YouTube video fetching system has been enhanced to support fetching **scheduled videos** in addition to public videos. The system uses OAuth to access scheduled videos, then **automatically filters out** private, unlisted, and drafted videos, keeping only:

✅ **Public videos** (already published)
✅ **Scheduled videos** (set to publish in the future)

This uses the existing OAuth authentication system that's already set up for updating video descriptions.

## What's New

### Features Added
- ✅ Fetch scheduled videos using OAuth authentication
- ✅ Automatic filtering to remove private, unlisted, and drafted videos
- ✅ Privacy status tracking for public vs scheduled videos
- ✅ Command-line flags to control behavior
- ✅ Automatic fallback to public-only if OAuth fails
- ✅ Clear reporting of filtered videos

### Files Modified
1. **`src/services/youtube_service.py`**
   - Added `oauth_token` parameter to `YouTubeService` class
   - Added `fetch_all_videos_authenticated()` method for OAuth-based fetching
   - Modified `fetch_all_videos_from_channel()` to support `include_private` flag
   - Updated `create_youtube_service()` factory function

2. **`fetch_complete_videos.py`**
   - Added OAuth authentication integration
   - Added `--include-private` command-line flag to fetch scheduled videos
   - Added automatic filtering to keep only public + scheduled videos
   - Enhanced progress reporting with filter statistics
   - Added automatic OAuth token retrieval

## How It Works

### Public Videos (Default Behavior)
By default, the script uses the YouTube Data API with an API key to fetch only **public** videos from the channel's uploads playlist. This doesn't require OAuth authentication.

### Scheduled Videos (New Behavior)
When you enable `--include-private`:
1. The script retrieves your OAuth token from the existing authentication system
2. Uses the YouTube `search` endpoint with `forMine=true` parameter
3. Fetches ALL videos regardless of privacy status
4. **Automatically filters the results** to keep only:
   - ✅ Public videos (already live)
   - ✅ Scheduled videos (private with `publishAt` date)
5. **Removes** from final output:
   - ❌ Private videos (without schedule date)
   - ❌ Unlisted videos
   - ❌ Drafted videos (not yet uploaded)

## Prerequisites

### For Public Videos Only
- YouTube Data API key (already configured in `.env`)

### For Scheduled Videos
- OAuth 2.0 credentials (already configured via `client_secrets.json`)
- Valid OAuth token (obtain via `python get_youtube_oauth_token.py`)

**Note:** The OAuth authentication system is already set up for updating video descriptions, so you should already have everything configured!

### What Videos Will Be Included

| Video Type | Default Mode | With `--include-private` |
|-----------|--------------|-------------------------|
| Public (Live) | ✅ Yes | ✅ Yes |
| Scheduled (Future) | ❌ No | ✅ Yes |
| Private (Not Scheduled) | ❌ No | ❌ No (Filtered Out) |
| Unlisted | ❌ No | ❌ No (Filtered Out) |
| Drafted | ❌ No | ❌ No (Filtered Out) |

## Usage

### Option 1: Fetch Public Videos Only (Default)

```bash
# Fetch only public videos (no OAuth needed)
python fetch_complete_videos.py
```

### Option 2: Fetch Public + Scheduled Videos

```bash
# Fetch public + scheduled videos (filters out private/unlisted/drafted)
python fetch_complete_videos.py --include-private
```

### Additional Options

```bash
# Custom channel ID
python fetch_complete_videos.py \
    --channel-id UCxxxxxxxxxxxxx \
    --include-private

# Custom output file
python fetch_complete_videos.py \
    --include-private \
    --output my_videos.json

# View help
python fetch_complete_videos.py --help
```

## Authentication Setup

If you haven't set up OAuth yet (or if your token expired):

### Step 1: Get OAuth Token

```bash
python get_youtube_oauth_token.py
```

This will:
1. Open a browser window for authentication
2. Ask you to sign in with your YouTube account
3. Save the token to `token.json` and `.env`

### Step 2: Run Fetch with Private Access

```bash
python fetch_complete_videos.py --include-private
```

## Output Differences

### Public-Only Output

```
FINAL VIDEO ANALYSIS
================================================================================

Total Videos in Final Output: 1467

By Type:
  Shorts: 5
  Regular Videos: 1458
  Live Streams: 4

By Status:
  Public (Live Now): 1467
  Scheduled (Future): 0
```

### With --include-private (Public + Scheduled)

```
[3/4] Filtering videos...
   🔍 Filtering: Keeping public and scheduled videos only
   🗑️  Removing: private, unlisted, and drafted videos
   ✓ Kept 1470 videos
   ✓ Scheduled videos found: 3
   ✗ Removed 2 private
   ✗ Removed 1 unlisted
   ✗ Removed 0 drafted

FINAL VIDEO ANALYSIS
(After filtering - Public + Scheduled only)
================================================================================

Total Videos in Final Output: 1470

By Type:
  Shorts: 5
  Regular Videos: 1461
  Live Streams: 4

By Status:
  Public (Live Now): 1467
  Scheduled (Future): 3

📅 Note: Scheduled videos will be published at their set dates
```

## Video Privacy Status Values

Each video in the output JSON includes a `status` object with `privacyStatus`:

**Videos included in output:**
- **`public`**: Visible to everyone - these are included
- **`private` with `publishAt`**: Scheduled videos - these are included

**Videos filtered out (not in output):**
- **`private` without `publishAt`**: Regular private videos - filtered out
- **`unlisted`**: Not listed publicly but accessible via link - filtered out
- **Draft videos** (`uploadStatus: "draft"`): Not yet uploaded - filtered out

## Technical Details

### API Endpoints Used

**Public Videos:**
- `playlistItems.list` - Fetches videos from uploads playlist
- Uses API key authentication
- Quota cost: 1 unit per request

**Private Videos:**
- `search.list` with `forMine=true` - Fetches all videos owned by authenticated user
- Uses OAuth Bearer token authentication
- Quota cost: 100 units per request (higher!)

### OAuth Scopes Required

```python
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
```

This scope is already configured in `youtube_auth.py` and provides full read/write access to your YouTube channel.

## Troubleshooting

### Error: "OAuth token required"

**Solution:** Run the OAuth setup:
```bash
python get_youtube_oauth_token.py
```

### Error: "Token expired"

The token automatically refreshes, but if it fails:
```bash
# Re-authenticate
python get_youtube_oauth_token.py
```

### Error: "Failed to fetch videos with OAuth"

**Possible causes:**
1. Invalid or expired token
2. API quota exceeded
3. Insufficient permissions

**Solution:**
1. Re-authenticate: `python get_youtube_oauth_token.py`
2. Check quota in [Google Cloud Console](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)
3. Verify your OAuth client has YouTube Data API access

### Script Falls Back to Public Videos

If OAuth authentication fails, the script automatically falls back to fetching only public videos. You'll see:

```
❌ Failed to get OAuth token. Private videos will not be fetched.
   Run: python get_youtube_oauth_token.py
   Falling back to public videos only...
```

## Integration with Existing Scripts

The changes are backward compatible. All existing scripts that use `YouTubeService` will continue to work:

```python
# Existing usage (public only)
youtube = create_youtube_service()
videos = youtube.fetch_all_videos_from_channel(channel_id)

# New usage (with private videos)
from src.services.youtube_auth import get_youtube_token

oauth_token = get_youtube_token()
youtube = create_youtube_service(oauth_token=oauth_token)
videos = youtube.fetch_all_videos_from_channel(
    channel_id,
    include_private=True
)
```

## API Quota Considerations

Fetching private videos uses more quota:

| Method | Endpoint | Quota Cost | Videos per Request |
|--------|----------|------------|-------------------|
| Public | playlistItems.list | 1 unit | Up to 50 |
| Private | search.list | 100 units | Up to 50 |

**Daily quota limit:** 10,000 units by default

**Example calculations:**
- Fetching 1500 public videos: ~30 requests × 1 unit = **30 units**
- Fetching 1500 private videos: ~30 requests × 100 units = **3,000 units**

## Best Practices

1. **Use public-only mode when possible** to conserve quota
2. **Fetch private videos only when needed** (e.g., for complete analysis)
3. **Save the output** to avoid re-fetching (output includes all video details)
4. **Monitor your quota** in Google Cloud Console
5. **Keep your OAuth token secure** (it's saved in `token.json` and `.env`)

## Examples

### Example 1: Complete Channel Data (Public + Scheduled)

```bash
python fetch_complete_videos.py \
    --include-private \
    --output complete_videos_$(date +%Y%m%d).json
```

### Example 2: Public Videos Only (Fast, Low Quota)

```bash
python fetch_complete_videos.py \
    --output public_videos.json
```

### Example 3: Check Scheduled Video Count

```bash
python fetch_complete_videos.py --include-private | grep "Scheduled"
```

### Example 4: Verify Filter Results

```bash
# Run the fetch
python fetch_complete_videos.py --include-private

# Check the output JSON
python -c "
import json
with open('complete_videos.json') as f:
    videos = json.load(f)
    print(f'Total videos: {len(videos)}')
    
    # Count by privacy status
    public = sum(1 for v in videos if v.get('status', {}).get('privacyStatus') == 'public')
    scheduled = sum(1 for v in videos if v.get('status', {}).get('publishAt'))
    
    print(f'Public: {public}')
    print(f'Scheduled: {scheduled}')
    
    # Verify no unwanted videos
    private = sum(1 for v in videos if v.get('status', {}).get('privacyStatus') == 'private' and not v.get('status', {}).get('publishAt'))
    unlisted = sum(1 for v in videos if v.get('status', {}).get('privacyStatus') == 'unlisted')
    
    print(f'\\nFiltered out (should be 0):')
    print(f'  Private (non-scheduled): {private}')
    print(f'  Unlisted: {unlisted}')
"
```

## Support

For issues related to:
- **OAuth Setup:** See existing docs in `docs/YOUTUBE_DESCRIPTION_UPDATER.md`
- **API Quotas:** See `docs/YOUTUBE_QUOTA_GUIDE.md`
- **YouTube API:** [YouTube Data API Documentation](https://developers.google.com/youtube/v3)

## Summary

The fetch videos system now seamlessly integrates with your existing OAuth authentication to provide access to scheduled videos while automatically filtering out private, unlisted, and drafted videos. The system:

✅ Fetches **public** and **scheduled** videos only
❌ Automatically filters out **private** (non-scheduled), **unlisted**, and **drafted** videos
🔐 Uses your existing OAuth setup
📊 Provides clear reporting of what was kept and filtered

Simply add `--include-private` flag to fetch public + scheduled videos!

