# Quick Start: YouTube Description Updater

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get YouTube OAuth Credentials

**Option A: Use Existing Credentials**
If you already have `client_secrets.json`, skip to step 3.

**Option B: Create New Credentials**
1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID → Desktop app
3. Download JSON → Save as `client_secrets.json`

### 3. Generate OAuth Token
```bash
python get_youtube_oauth_token.py
```
- Browser will open
- Sign in with your YouTube account
- Token saved to `.env` automatically

### 4. Check Which Videos Need Updates
```bash
python update_youtube_descriptions.py --check-only
```

### 5. Test with Dry Run
```bash
python update_youtube_descriptions.py --dry-run --limit 1
```

### 6. Execute Updates
```bash
python update_youtube_descriptions.py --execute
```

---

## 📋 Common Commands

### Check Status (No Changes)
```bash
python update_youtube_descriptions.py --check-only
```

### Dry Run (Simulate)
```bash
python update_youtube_descriptions.py --dry-run
```

### Update First 10 Videos
```bash
python update_youtube_descriptions.py --execute --limit 10
```

### Update All Videos
```bash
python update_youtube_descriptions.py --execute
```

---

## ⚠️ Important Notes

1. **NFT must be minted first** (CRITICAL)
   - Script verifies NFT exists before updating
   - Videos without minted NFTs are skipped with warning
   - ✓ checkmark only appears when NFT is verified

2. **OAuth tokens expire after ~1 hour**
   - Regenerate with: `python get_youtube_oauth_token.py`

3. **Always test with --dry-run first**
   - See what would change before executing

4. **Check quota limits**
   - YouTube API: 10,000 units/day
   - Each update: ~50 units
   - Max ~200 updates/day

5. **Character limit**
   - YouTube max: 5000 characters
   - Videos exceeding limit are automatically skipped

6. **Description format** (BCA text added at top)
   ```
   This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger — proof it's the genuine article from the official series run. BCA: https://bca.jimflint.com/verify/{NFTokenId}

   [Your existing video description content here...]

   #your #hashtags
   ```

---

## 🔄 Complete Workflow

### After Minting NFTs
```bash
# 1. Mint NFTs
python mint_nfts.py mint 10

# 2. Get fresh OAuth token
python get_youtube_oauth_token.py

# 3. Check which need updates
python update_youtube_descriptions.py --check-only

# 4. Test with one video
python update_youtube_descriptions.py --dry-run --limit 1

# 5. Update all
python update_youtube_descriptions.py --execute
```

---

## 🐛 Troubleshooting

### "OAuth token required"
```bash
python get_youtube_oauth_token.py
```

### "Token expired"
Tokens expire after 1 hour. Regenerate:
```bash
python get_youtube_oauth_token.py
```

### "client_secrets.json not found"
1. Download from Google Cloud Console
2. Save in project root directory

### "No NFT found in database for this video"
Video doesn't have a minted NFT. You must:
1. Mint an NFT for this video first
   ```bash
   python mint_nfts.py mint 1
   ```
2. Then run the description updater

### "Description exceeds 5000 characters"
Video has a very long description. Options:
- Manually shorten the description
- Accept that this video will be skipped
- Check logs for character count details

### Check logs
```bash
tail -f youtube_description_updates.log
```

---

## 📊 Understanding Output

```
[1/50] Processing video: dQw4w9WgXcQ
  Status: BCA text not found
  Updated: Added at top

[2/50] Processing video: 9bZkp7q19f0
  Status: BCA text exists and matches ✓ (NFT verified)

[3/50] Processing video: jNQXAC9IVRw
  Status: BCA text exists but NFT ID mismatch
  Updated: Replaced at top

[4/50] Processing video: ABC123XYZ
  ⚠️  SKIPPED: No NFT found in database for this video
```

**Status meanings:**
- ✅ "exists and matches ✓ (NFT verified)" → No action needed, NFT confirmed
- ⚠️ "not found" → Will add BCA text (NFT must exist first)
- 🔄 "mismatch" → Will update NFT ID to correct one
- ⚠️ "SKIPPED: No NFT" → Video has no minted NFT, cannot update

---

## 📁 Generated Files

- `youtube_description_updates.log` → Real-time log
- `youtube_update_results_YYYYMMDD_HHMMSS.log` → Detailed report

---

For detailed documentation, see: [YOUTUBE_DESCRIPTION_UPDATER.md](./YOUTUBE_DESCRIPTION_UPDATER.md)
