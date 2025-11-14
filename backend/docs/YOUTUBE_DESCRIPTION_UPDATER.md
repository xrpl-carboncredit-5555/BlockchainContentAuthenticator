# YouTube Description Updater for NFT Minted Videos

## Overview

This tool automatically updates YouTube video descriptions to include BCA (Blockchain Content Authenticator) validation information after NFTs are minted on the XRP Ledger.

### What it does:

1. ✅ Queries MongoDB for all minted NFTs
2. ✅ **Verifies NFT exists before attempting updates** (CRITICAL)
3. ✅ Syncs latest description from YouTube API to MongoDB
4. ✅ Checks current YouTube video descriptions
5. ✅ Identifies if BCA validation text already exists
6. ✅ Validates NFToken ID matches between YouTube and database
7. ✅ Updates or adds BCA validation text at the top of description
8. ✅ Validates 5000 character limit (skips if exceeded)
9. ✅ Provides dry-run mode for safe testing
10. ✅ Comprehensive logging of all operations
11. ✅ Skips videos without minted NFTs with clear warnings
12. ✅ **Automatic OAuth token refresh** for long-running operations
13. ✅ **Retry logic with exponential backoff** for transient errors
14. ✅ **Rate limiting** to avoid API quota issues at scale
15. ✅ **Progress tracking with ETA** for large batches
16. ✅ **Detailed timing statistics** for performance monitoring

---

## BCA Validation Text Format

The following text is added to video descriptions:

```
This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger — proof it's the genuine article from the official series run. BCA: https://bca.jimflint.com/verify/{NFTokenId}
```

The text is placed:
- **At the very top** of the description (first line)
- Original description content preserved below
- **Character limit**: Videos with descriptions exceeding 5000 characters are skipped

---

## Prerequisites

### 1. Python Dependencies

Install the required OAuth library:

```bash
pip install google-auth-oauthlib python-dotenv
```

### 2. Google Cloud Project Setup

#### Step 1: Enable YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (or create a new one)
3. Navigate to **APIs & Services > Library**
4. Search for "YouTube Data API v3"
5. Click **Enable**

#### Step 2: Create OAuth 2.0 Credentials
1. Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **+ CREATE CREDENTIALS**
3. Select **OAuth client ID**
4. If prompted, configure the OAuth consent screen:
   - User Type: **External** (for testing) or **Internal** (if G Suite)
   - App name: "YouTube NFT Manager" (or your choice)
   - Add your email as developer contact
   - Scopes: Add `https://www.googleapis.com/auth/youtube.force-ssl`
5. Application type: **Desktop app**
6. Name: "YouTube Description Updater"
7. Click **Create**
8. **Download** the JSON file
9. Save it as `client_secrets.json` in your project directory

---

## Getting Started

### Step 1: Generate OAuth Token

Run the OAuth helper script:

```bash
python get_youtube_oauth_token.py
```

This will:
1. Open a browser for Google authentication
2. Request permission to manage your YouTube videos
3. Save the access token to your `.env` file

**Note:** OAuth tokens typically expire after 1 hour. You'll need to regenerate them periodically.

### Step 2: Verify Setup

Check that your `.env` file contains:

```bash
YOUTUBE_OAUTH_TOKEN=your_access_token_here
YOUTUBE_API_KEY=your_api_key_here
MONGODB_URI=your_mongodb_connection_string
```

---

## Usage

### Check Status Only

See which videos need updates without making changes:

```bash
python update_youtube_descriptions.py --check-only
```

Output:
```
[1/10] Processing video: dQw4w9WgXcQ
  Status: BCA text not found
[2/10] Processing video: 9bZkp7q19f0
  Status: BCA text exists and matches ✓
...
```

### Dry Run (Simulate Updates)

Test the update logic without modifying descriptions:

```bash
python update_youtube_descriptions.py --dry-run
```

Output:
```
[DRY RUN] Would update video dQw4w9WgXcQ: Added before metadata tags
[DRY RUN] New description preview:
Amazing video content...

This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger — proof it's the genuine article from the official series run. BCA: https://bca.jimflint.com/verify/000...

#hashtag #tags #here
```

### Execute Updates

Actually update video descriptions:

```bash
python update_youtube_descriptions.py --execute
```

⚠️ **Warning:** This will modify your YouTube video descriptions!

### Limit Number of Videos

Process only a specific number of videos:

```bash
python update_youtube_descriptions.py --execute --limit 5
```

### Skip Already-Processed Videos

Resume from a specific position (useful after hitting quota limits):

```bash
# Skip first 180 videos, start from video 181
python update_youtube_descriptions.py --execute --skip 180

# Combine with limit to process a specific range
# Process videos 181-200 (skip 180, then process 20)
python update_youtube_descriptions.py --execute --skip 180 --limit 20
```

**Why use `--skip`?**
- ✅ **Save quota**: Don't waste API calls checking already-updated videos
- ✅ **Resume exactly**: Start from where you left off after quota exhaustion
- ✅ **Clear progress**: Shows actual position like `[181/580]` instead of `[1/400]`
- ✅ **Faster**: No need to check videos you know are already updated

**Common scenarios:**
```bash
# Day 1: Updated 198 videos, then hit quota limit
python update_youtube_descriptions.py --execute --rate-limit 1.5

# Day 2: Resume from video 199
python update_youtube_descriptions.py --execute --skip 198 --rate-limit 1.5

# Alternative: Process in planned batches
# Day 1: Videos 1-190
python update_youtube_descriptions.py --execute --limit 190

# Day 2: Videos 191-380
python update_youtube_descriptions.py --execute --skip 190 --limit 190

# Day 3: Videos 381-end
python update_youtube_descriptions.py --execute --skip 380
```

### Manual OAuth Token

Provide OAuth token via command line:

```bash
python update_youtube_descriptions.py --execute --oauth-token "ya29.a0AfH6..."
```

### Rate Limiting for Scale Operations

Control the delay between API requests (default 1.0 second):

```bash
# Faster processing (use with caution - may hit rate limits)
python update_youtube_descriptions.py --execute --rate-limit 0.5

# Conservative rate limiting (safer for large batches)
python update_youtube_descriptions.py --execute --rate-limit 2.0

# Default (1 second delay)
python update_youtube_descriptions.py --execute
```

**Recommended rate limits:**
- **Small batches (< 50 videos):** 0.5-1.0 seconds
- **Medium batches (50-200 videos):** 1.0-1.5 seconds
- **Large batches (200+ videos):** 1.5-2.0 seconds

---

## How It Works

### 1. Database Query
```python
# Fetch all minted NFTs from MongoDB
nfts = mongodb_service.get_all_nfts()
# Returns: [{"video_id": "...", "nft_id": "...", ...}, ...]
```

### 2. NFT Verification (CRITICAL)
```python
# BEFORE attempting any update, verify NFT exists
nft_exists, nft_id, error_msg = verify_nft_exists(video_id)

if not nft_exists:
    logger.warning(f"⚠️  SKIPPED: {error_msg}")
    # Skip this video, move to next
    continue

# Validation checks:
# 1. NFT record exists in MongoDB
# 2. NFT has valid nft_id field
# 3. nft_id is correct format (hex string, min 10 chars)
```

### 3. Sync from YouTube API
```python
# Fetch latest description from YouTube
latest_description = youtube.get_video_description(video_id)

# Update MongoDB with latest version
mongodb.update_video_description(video_id, latest_description)
```

### 4. Description Analysis
```python
# Check if BCA text exists
current_nft_id = extract_nft_id_from_description(description)

# Compare with database
if current_nft_id != expected_nft_id:
    # Update needed
```

### 5. BCA Text Placement (Always at Top)
```python
# Remove existing BCA text if present
description_without_bca = BCA_PATTERN.sub('', description).strip()

# Add BCA text at the very top
new_description = bca_text + "\n\n" + description_without_bca
```

### 6. Character Limit Validation
```python
# YouTube max is 5000 characters
if len(new_description) > 5000:
    logger.warning(f"Skipping: Description exceeds 5000 chars")
    return False, "SKIPPED: Character limit exceeded"
```

### 7. YouTube API Update
```python
# Update using OAuth
youtube.update_video_description(
    video_id=video_id,
    new_description=new_description,
    oauth_token=oauth_token
)
```

---

## Robust Error Handling for Scale Operations

### Automatic OAuth Token Refresh

The script now automatically handles OAuth token expiration during long-running operations:

```python
# Automatic token refresh on 401 errors
if "401" in error or "Unauthorized" in error:
    logger.info("Token expired, refreshing...")
    if self.refresh_oauth_token():
        # Retry with new token
        return self.update_description(video_id, nft_token_id, dry_run)
```

**Benefits:**
- No need to regenerate tokens manually during long batches
- Seamless operation even for 500+ video updates
- Automatic recovery from token expiration

### Retry Logic with Exponential Backoff

Each update attempt includes smart retry logic:

```python
# Retry up to 3 times with increasing delays
for attempt in range(3):
    try:
        return update_video(video_id)
    except Exception as e:
        if attempt < 2:
            delay = 2 ** attempt  # 1s, 2s, 4s
            time.sleep(delay)
            continue
        raise
```

**Handles:**
- Transient network errors
- API rate limiting (429 errors)
- Temporary service unavailability
- OAuth token expiration (automatic refresh)

### Progress Tracking for Large Batches

Real-time progress monitoring during execution:

```
[1/500] Progress: 0.2% | ETA: 45.2 min
Processing video: dQw4w9WgXcQ
  Status: BCA text not found

[2/500] Progress: 0.4% | ETA: 44.8 min
Processing video: 9bZkp7q19f0
  Status: BCA text exists and matches ✓
...
```

**Provides:**
- Current progress percentage
- Estimated time to completion
- Average time per video
- Real-time status updates

### Performance Statistics

Detailed timing information after completion:

```
======================================================================
Processing complete!
Total time: 45.3 minutes
Average: 5.43 seconds per video
======================================================================

YOUTUBE DESCRIPTION UPDATE SUMMARY
======================================================================
⏱️  Total time: 45.3 minutes
⏱️  Average: 5.43 seconds per video
----------------------------------------------------------------------
📊 Total videos processed: 500
✅ Already correct (NFT verified): 450
🔄 Need update: 50
✅ Updated successfully: 48
❌ Update failed: 2
======================================================================
```

---

## Output Files

### 1. Log File
`youtube_description_updates.log`
- Real-time logging of all operations
- Error tracking
- Detailed progress information

### 2. Results File
`youtube_update_results_YYYYMMDD_HHMMSS.log`
- Comprehensive report of all processed videos
- Status of each video
- Actions taken
- Generated after each run

Example:
```
Video ID: dQw4w9WgXcQ
Title: Amazing Video Title
NFT Token ID: 000B0F5...
Status: BCA text not found
Needs Update: True
Action: Updated: Added before metadata tags
----------------------------------------------------------------------
```

---

## Workflow Integration

### After Minting NFTs

1. **Mint NFTs** using existing script:
   ```bash
   python mint_nfts.py mint 10
   ```

2. **Check which videos need description updates**:
   ```bash
   python update_youtube_descriptions.py --check-only
   ```

3. **Test with dry-run**:
   ```bash
   python update_youtube_descriptions.py --dry-run --limit 1
   ```

4. **Execute updates**:
   ```bash
   python update_youtube_descriptions.py --execute
   ```

### Automated Workflow

Create a bash script to automate the process:

```bash
#!/bin/bash
# auto_update_descriptions.sh

echo "Generating fresh OAuth token..."
python get_youtube_oauth_token.py

echo "Checking video status..."
python update_youtube_descriptions.py --check-only

echo "Ready to update. Press Enter to continue or Ctrl+C to cancel..."
read

echo "Executing updates..."
python update_youtube_descriptions.py --execute

echo "Done! Check youtube_update_results_*.log for details"
```

---

## Safety Features

### 1. Dry-Run Mode (Default)
- Simulates all operations without making changes
- Shows exactly what would be updated
- Safe for testing

### 2. Check-Only Mode
- Only reads descriptions and reports status
- No modifications attempted
- Fastest way to audit current state

### 3. Validation Checks
- Verifies NFToken ID matches database
- Detects existing BCA text
- Prevents duplicate entries

### 4. Error Handling
- Continues processing even if individual videos fail
- Logs all errors with details
- Provides summary statistics

### 5. Comprehensive Logging
- All operations logged to file
- Timestamps for audit trail
- Debug information for troubleshooting

---

## Common Scenarios

### Scenario 1: First Time Adding BCA Text

**Situation:** Videos have been minted but descriptions don't have BCA text yet.

**Steps:**
```bash
# Check how many need updates
python update_youtube_descriptions.py --check-only

# Test with one video
python update_youtube_descriptions.py --dry-run --limit 1

# Update all
python update_youtube_descriptions.py --execute
```

### Scenario 2: NFT Was Re-Minted (New NFToken ID)

**Situation:** NFT was re-minted with a new ID, but description has old ID.

**Detection:** Script automatically detects mismatch:
```
Status: BCA text exists but NFT ID mismatch
Expected NFT: 000B0F5ABC123...
Current NFT: 000A0E4DEF456...
```

**Action:** Script replaces old URL with new one:
```bash
python update_youtube_descriptions.py --execute
```

### Scenario 3: Verifying Current State

**Situation:** Want to verify all descriptions are correct without making changes.

**Steps:**
```bash
python update_youtube_descriptions.py --check-only
```

**Output:**
```
Total videos processed: 50
Already correct: 45
Need update: 5
```

### Scenario 4: Batch Processing Large Channel

**Situation:** Channel has 500+ videos, want to update all at once.

**Steps:**
```bash
# Check status first
python update_youtube_descriptions.py --check-only

# Process all videos with appropriate rate limiting
# The script will automatically refresh OAuth tokens as needed
python update_youtube_descriptions.py --execute --rate-limit 1.5

# Monitor progress in real-time
# [1/500] Progress: 0.2% | ETA: 45.2 min
# [2/500] Progress: 0.4% | ETA: 44.8 min
# ...
```

**Benefits of new scale features:**
- ✅ Automatic OAuth token refresh (no manual intervention)
- ✅ Real-time progress and ETA display
- ✅ Retry logic handles transient errors
- ✅ Rate limiting prevents API quota issues
- ✅ Detailed timing statistics at completion

**Alternative (Manual Batching):**
If you prefer to process in smaller batches:
```bash
# Process in batches of 50
python update_youtube_descriptions.py --execute --limit 50 --rate-limit 1.0
# Wait a few minutes (respect rate limits)
python update_youtube_descriptions.py --execute --limit 50 --rate-limit 1.0
# Repeat...
```

---

## Troubleshooting

### Issue: "OAuth token required for --execute mode"

**Solution:** Generate a fresh OAuth token:
```bash
python get_youtube_oauth_token.py
```

### Issue: "Token has expired"

**Cause:** OAuth tokens expire after ~1 hour.

**Solution (Automatic):** The script now automatically refreshes expired tokens! You should see:
```
🔄 Token expired, refreshing...
✅ Token refreshed successfully
```

**Manual Solution (if automatic refresh fails):**
```bash
python get_youtube_oauth_token.py
python update_youtube_descriptions.py --execute
```

**Note:** For long-running operations (500+ videos), the script will automatically refresh tokens multiple times as needed.

### Issue: "client_secrets.json not found"

**Solution:**
1. Download OAuth credentials from Google Cloud Console
2. Save as `client_secrets.json` in project directory

### Issue: "Rate limit exceeded"

**Solution:**
1. YouTube API has quota limits
2. Process videos in smaller batches with `--limit`
3. Wait a few minutes between batches

### Issue: "Failed to update video description"

**Possible causes:**
- Video is private or unlisted (requires additional permissions)
- OAuth scope doesn't include video editing
- Network connectivity issues

**Check logs:**
```bash
tail -f youtube_description_updates.log
```

---

## API Quota Considerations

YouTube Data API v3 has daily quota limits:
- **Default quota:** 10,000 units per day
- **Update operation:** ~50 units per video

**Calculation:**
- Maximum ~200 video updates per day with default quota

**Tips:**
1. Use `--check-only` first (minimal quota usage)
2. Use `--dry-run` to verify before executing
3. Process videos in batches if you have many
4. Request quota increase from Google if needed

---

## Advanced Usage

### Custom OAuth Token Source

```python
from update_youtube_descriptions import YouTubeDescriptionUpdater
from src.services import create_youtube_service, create_mongodb_service

# Your custom token retrieval
oauth_token = get_token_from_custom_source()

youtube = create_youtube_service()
mongodb = create_mongodb_service()

updater = YouTubeDescriptionUpdater(youtube, mongodb, oauth_token)
stats = updater.process_all_videos(dry_run=False)
```

### Filter Specific Videos

```python
# Process only videos from specific date range
nfts = mongodb.get_all_nfts()
filtered_nfts = [nft for nft in nfts if is_in_date_range(nft)]

for nft in filtered_nfts:
    updater.update_description(nft['video_id'], nft['nft_id'], dry_run=False)
```

### Custom BCA Text Format

Modify the template in `update_youtube_descriptions.py`:

```python
class YouTubeDescriptionUpdater:
    BCA_TEMPLATE = """Your custom text here
BCA Reference: https://your-custom-url.com/{nft_token_id}"""
```

---

## Security Best Practices

1. **Never commit OAuth tokens to git**
   - Add to `.gitignore`: `client_secrets.json`, `.env`

2. **Rotate tokens regularly**
   - Regenerate OAuth tokens periodically

3. **Use environment variables**
   - Store sensitive data in `.env` file

4. **Limit OAuth scope**
   - Only request necessary permissions

5. **Monitor API usage**
   - Check Google Cloud Console for quota usage

---

## Summary

This tool provides a safe, controlled way to update YouTube video descriptions with blockchain validation information after NFT minting.

### Key Features:

#### Core Functionality
- ✅ **Safe:** Dry-run and check-only modes
- ✅ **Smart:** Detects existing text and metadata tags
- ✅ **Integrated:** Works with existing MongoDB and YouTube services

#### Scale & Robustness (NEW)
- ✅ **Automatic Token Refresh:** No manual intervention for long-running batches
- ✅ **Retry Logic:** Exponential backoff handles transient errors
- ✅ **Rate Limiting:** Configurable delays prevent API quota issues
- ✅ **Progress Tracking:** Real-time ETA and completion estimates
- ✅ **Performance Stats:** Detailed timing and success metrics

#### Built for Scale
- ✅ Process 500+ videos in a single run
- ✅ Automatic OAuth token refresh every ~1 hour
- ✅ Retry failed updates with intelligent backoff
- ✅ Monitor progress and estimate completion time
- ✅ Detailed performance metrics and logging

**Ready for production-scale operations on large YouTube channels!**

For questions or issues, check the logs or review the source code comments.
