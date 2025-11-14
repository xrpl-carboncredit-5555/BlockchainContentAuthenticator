# YouTube API Quota Management Guide

## Understanding YouTube API Quotas

### Default Quota Limits

YouTube Data API v3 has strict quota limits:
- **Default quota**: 10,000 units per day
- **Quota reset**: Midnight Pacific Time (PT) daily
- **Video update cost**: ~50 units per video

**Maximum videos you can update per day: ~200 videos**

---

## Quota Cost Breakdown

### Common Operations

| Operation | Quota Cost | Videos per 10k quota |
|-----------|------------|---------------------|
| Read video details | 1 unit | 10,000 |
| Update video description | 50 units | 200 |
| List videos | 1 unit | 10,000 |

### Your Script's Quota Usage

For each video update, the script performs:
1. **Fetch video details** (snippet): 1 unit
2. **Update video description**: 50 units

**Total per video**: ~51 units
**Maximum videos per day**: ~196 videos (10,000 ÷ 51)

---

## What Happens When Quota is Exhausted

### Symptoms

1. **403 Forbidden Error**:
   ```
   403 Client Error: Forbidden for url: https://www.googleapis.com/youtube/v3/videos?part=snippet
   ```

2. **Script behavior**:
   - First ~200 videos update successfully
   - Subsequent videos all fail with 403 errors
   - Script automatically stops after 5 consecutive 403 errors

### Example Log Output

```
[198/580] Processing video: abc123...
  ✅ Successfully updated video

[199/580] Processing video: def456...
  ✅ Successfully updated video

[200/580] Processing video: ghi789...
  ❌ 403 Forbidden Error - Likely API quota exhausted
  ⚠️  Quota failure #1

[201/580] Processing video: jkl012...
  ❌ 403 Forbidden Error - Likely API quota exhausted
  ⚠️  Quota failure #2

...

⚠️  Quota failure #5
🛑 STOPPING: 5 consecutive quota failures detected
   YouTube API quota appears to be exhausted
   Successfully updated 198 videos before quota exhaustion
   Remaining videos will be skipped
```

---

## Solutions

### Solution 1: Wait for Quota Reset (Free)

**Best for:** Most users with occasional updates

**Steps:**
1. Note how many videos were successfully updated (e.g., 198 videos)
2. Wait until midnight Pacific Time for quota reset
3. Resume updates using `--skip` to start where you left off:
   ```bash
   # Skip first 198 videos and continue from video 199
   python update_youtube_descriptions.py --execute --skip 198 --rate-limit 1.5
   ```

**Why use `--skip`?**
- ✅ Saves quota by not checking already-updated videos
- ✅ Starts exactly where you left off
- ✅ Faster processing (no wasted API calls)
- ✅ Clear progress tracking shows actual position (e.g., [199/580])

**Example Multi-Day Workflow:**
- **Day 1**: Updated videos 1-198 ✅
- **Day 2**: `--skip 198` → Update videos 199-388 ✅
- **Day 3**: `--skip 388` → Update remaining videos 389-580 ✅

**Quota Reset Times:**
- **Pacific Time (PT)**: 12:00 AM (midnight)
- **Eastern Time (ET)**: 3:00 AM
- **UTC**: 8:00 AM (7:00 AM during DST)
- **India (IST)**: 1:30 PM

### Solution 2: Request Quota Increase (Recommended for Scale)

**Best for:** Channels with 500+ videos or frequent updates

**Steps:**

1. **Go to Google Cloud Console**:
   - Visit: https://console.cloud.google.com/
   - Select your project

2. **Navigate to API Quotas**:
   - Go to: **APIs & Services** > **YouTube Data API v3** > **Quotas**
   - Or direct link: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas

3. **Request Quota Increase**:
   - Click on "Queries per day" quota
   - Click "EDIT QUOTAS" or "ALL QUOTAS"
   - Enter new quota amount (e.g., 50,000 for ~1,000 videos/day)
   - Fill out the form explaining your use case
   - Submit request

4. **Justification Example**:
   ```
   Project Name: YouTube NFT Content Verification

   Use Case: We are minting NFTs for YouTube video content verification
   and need to update video descriptions with blockchain validation links.

   Current Limitation: We have 580 videos to update but can only update
   200 per day with the default quota.

   Requested Quota: 50,000 units/day (allows ~1,000 video updates)

   Business Impact: This is a one-time bulk update for adding blockchain
   validation to our video library. After initial update, we'll only need
   to update new videos periodically.
   ```

5. **Wait for Approval**:
   - Usually responds within 1-2 business days
   - May be instant for reasonable increases
   - You'll receive email notification

### Solution 3: Batch Processing Over Multiple Days

**Best for:** No urgency, free solution

**Strategy:**
1. Update 190 videos per day (leave buffer for other operations)
2. Use `--skip` to start where you left off
3. Resume next day without wasting quota on already-updated videos

**Example Workflow (RECOMMENDED - Uses `--skip`):**

**Day 1:**
```bash
# Update first 190 videos
python update_youtube_descriptions.py --execute --limit 190 --rate-limit 1.5
# Results: [1/580] to [190/580] processed
```

**Day 2 (after quota reset):**
```bash
# Skip first 190, update next 190 videos (191-380)
python update_youtube_descriptions.py --execute --skip 190 --limit 190 --rate-limit 1.5
# Results: [191/580] to [380/580] processed
```

**Day 3:**
```bash
# Skip first 380, update remaining videos (381-580)
python update_youtube_descriptions.py --execute --skip 380 --rate-limit 1.5
# Results: [381/580] to [580/580] processed
```

**Alternative (without `--skip` - relies on duplicate detection):**
```bash
# Day 1
python update_youtube_descriptions.py --execute --limit 190

# Day 2 - script checks all videos but skips already-updated ones
python update_youtube_descriptions.py --execute --limit 190
# This works but wastes ~190 API calls checking already-updated videos

# Better: Use --skip as shown above!
```

---

## Checking Your Current Quota Usage

### Via Google Cloud Console

1. Go to: https://console.cloud.google.com/apis/dashboard
2. Select YouTube Data API v3
3. Click "Quotas" tab
4. View current usage and limits

### Via Script Logs

The script automatically tracks and reports:
- Number of successful updates
- Number of quota failures
- Estimated quota used

---

## Best Practices

### 1. Use Check-Only Mode First

Before executing, check how many videos need updates:

```bash
python update_youtube_descriptions.py --check-only
```

**Output:**
```
Total videos processed: 580
Already correct: 80
Need update: 500
```

**Quota estimate:** 500 videos × 51 units = 25,500 units needed
**Days needed:** 3 days with default quota

### 2. Start with Dry Run

Test the update logic without using quota:

```bash
python update_youtube_descriptions.py --dry-run --limit 5
```

This uses minimal quota (only reads, ~5 units total)

### 3. Use Rate Limiting

Protect against accidental quota waste:

```bash
python update_youtube_descriptions.py --execute --rate-limit 1.5
```

This ensures controlled, measurable usage.

### 4. Process in Batches

For large channels, use `--limit`:

```bash
# Day 1: First 190 videos
python update_youtube_descriptions.py --execute --limit 190

# Day 2: Next 190 videos
python update_youtube_descriptions.py --execute --limit 190

# Day 3: Remaining videos
python update_youtube_descriptions.py --execute
```

### 5. Monitor Quota Usage

- Check Google Cloud Console regularly
- Review script output for quota warnings
- Keep track of successful update count

---

## Quota Error Messages Explained

### 403 Forbidden

**Error:**
```
403 Client Error: Forbidden for url: https://www.googleapis.com/youtube/v3/videos
```

**Meaning:** Quota exhausted OR insufficient OAuth permissions

**Check:**
1. Is quota exhausted? (Check Google Cloud Console)
2. Does OAuth token have `youtube.force-ssl` scope?

**Solution:** Wait for quota reset or request increase

### 429 Too Many Requests

**Error:**
```
429 Too Many Requests
```

**Meaning:** Rate limiting (too many requests too quickly)

**Solution:** Script automatically retries with 30-second delay

### 401 Unauthorized

**Error:**
```
401 Unauthorized
```

**Meaning:** OAuth token expired or invalid

**Solution:** Script automatically refreshes token

---

## FAQ

### Q: How do I know if I've hit the quota limit?

**A:** Look for these signs:
- 403 Forbidden errors in logs
- Script stops after ~200 video updates
- Message: "YouTube API quota appears to be exhausted"

### Q: Will the script resume where it left off?

**A:** Yes! The script tracks which videos are already updated:
- Videos already updated will show: "Already correct (NFT verified) ✓"
- Only videos needing updates will consume quota

### Q: Can I update videos on multiple channels?

**A:** Yes, but:
- Quota is shared across all projects using same API credentials
- Each channel update counts toward your daily quota
- Consider separate projects for separate channels if needed

### Q: Does check-only mode use quota?

**A:** Yes, but minimal:
- Each video check: ~1 unit
- 580 videos checked: ~580 units (6% of daily quota)
- Safe to use for planning

### Q: Does dry-run mode use quota?

**A:** Yes, but minimal:
- Reads video descriptions: ~1 unit per video
- Does NOT execute updates (saves 50 units per video)
- Safe to use for testing

### Q: How long does quota increase approval take?

**A:** Typically:
- Small increases (< 100,000): Often instant or within hours
- Medium increases (< 1,000,000): 1-2 business days
- Large increases: Up to 5 business days
- You'll receive email notification

---

## Summary

### Current Situation
- ✅ Successfully updated ~198 videos
- ❌ Hit quota limit (403 Forbidden errors)
- ⏳ Remaining ~382 videos need updates

### Recommended Action Plan

**Option A: Free (3-day approach)**
```bash
# Day 1 (today): Already updated 198 videos ✓
# Day 2 (tomorrow): Update next 190 videos
python update_youtube_descriptions.py --execute --limit 190

# Day 3: Update remaining ~192 videos
python update_youtube_descriptions.py --execute
```

**Option B: Fast (quota increase)**
1. Request quota increase to 50,000 units
2. Wait 1-2 days for approval
3. Update all remaining videos in one run

**Option C: Hybrid**
1. Continue with daily batches while waiting for quota increase
2. Once approved, process any remaining videos

---

## Getting Help

If you encounter issues:
1. Check logs: `youtube_description_updates.log`
2. View quota usage: Google Cloud Console
3. Review error messages in script output
4. Verify OAuth token has correct scopes

---

**Last Updated:** 2025-11-09
