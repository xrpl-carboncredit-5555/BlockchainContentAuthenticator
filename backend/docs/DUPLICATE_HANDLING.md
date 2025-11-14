# Duplicate Detection & Transaction Verification

This document explains the duplicate CID detection and failed transaction recovery features.

---

## 🔍 Problem 1: Network Failures with Successful Transactions

### Issue
Sometimes XRPL transactions succeed on-chain but the response fails to return due to network issues. This causes:
- NFT is actually minted on blockchain
- MongoDB not updated (thinks it failed)
- Video marked as "unminted"
- System tries to mint duplicate on next run

### Solution: Transaction Verification

The system now verifies transaction success even when errors occur:

1. **Transaction submitted but response failed?**
   - System verifies transaction hash on-chain
   - Checks if transaction actually succeeded
   - Extracts NFT ID from verified transaction

2. **No transaction hash but metadata uploaded?**
   - Searches wallet for NFT with matching URI/CID
   - If found, recovers NFT ID
   - Updates MongoDB with correct data

### How It Works

```python
# In mint_nfts.py:86-233

if not mint_result['success']:
    # Transaction appears to have failed

    if 'tx_hash' in mint_result:
        # Verify if transaction actually succeeded
        verified_nft_id = xrpl.verify_transaction_success(tx_hash)

        if verified_nft_id:
            # Transaction succeeded despite error!
            # Continue with saving to MongoDB
        else:
            # Check if NFT exists with this URI
            existing_nft = xrpl.find_nft_by_uri(uri)
            if existing_nft:
                # Found from previous attempt!
                # Recover and save
```

### New XRPL Service Methods

**`verify_transaction_success(tx_hash)`**
- Queries XRPL for transaction details
- Verifies if transaction result is `tesSUCCESS`
- Extracts and returns NFT ID
- Returns `None` if transaction actually failed

**`find_nft_by_uri(uri)`**
- Fetches all NFTs from wallet
- Decodes URIs from hex format
- Matches against provided CID/URI
- Returns NFT data if found

---

## 🚫 Problem 2: Duplicate CID Detection

### Issue
If you upload metadata to IPFS and get the same CID, attempting to mint creates a duplicate NFT with identical content.

### Solution: Pre-Mint & Runtime Duplicate Detection

The system checks for duplicates at two levels:

#### Level 1: Pre-Minting Batch Check

Before starting batch minting:

```bash
python mint_nfts.py mint 10
```

```
🔍 Pre-minting duplicate check...
🔍 Fetching existing NFTs from XRPL to check for duplicates...
   Found 47 existing NFTs on XRPL
   Indexed 47 unique CIDs
```

This builds a map of all existing CIDs for fast lookup during minting.

#### Level 2: Runtime Check Before Each Mint

Before minting each video:

```
🔍 Checking for duplicate CID on XRPL...
```

If duplicate found:

```
⚠️  DUPLICATE DETECTED!
   CID: QmXXXXXXXXXXXXXXXXXXXXXXXXX
   Existing NFT ID: 000800003C85C18E326460579DA9BDCE1F96691820E14C8A...
   This CID is already minted on XRPL
   Found in database for video: abc123XYZ

❓ What would you like to do?
   1. Skip this video (will not retry)
   2. Continue anyway (will attempt to mint duplicate)
   3. Abort minting process

Enter choice (1/2/3):
```

#### User Options

**Option 1: Skip**
- Marks video with `skip_minting: true` in MongoDB
- Records skip reason: "Duplicate CID: QmXXX..."
- Video will not appear in unminted list on future runs
- Can be unskipped later if needed

**Option 2: Continue Anyway**
- Proceeds with minting
- Will create duplicate NFT (XRPL allows this)
- Useful if you want multiple NFTs with same content

**Option 3: Abort**
- Stops entire minting process
- Allows you to investigate the issue
- No data changed

---

## 📝 MongoDB Tracking

### New Fields in Videos Collection

```javascript
{
  video_id: "abc123",
  title: "Video Title",
  skip_minting: true,          // NEW: Skip flag
  skip_reason: "Duplicate CID: QmXXX...",  // NEW: Why skipped
  skipped_at: ISODate("..."),  // NEW: When skipped
  // ... other fields
}
```

### New MongoDB Methods

**`mark_video_skipped(video_id, reason)`**
```python
mongodb.mark_video_skipped("abc123", "Duplicate CID: QmXXX")
```

**`unmark_video_skipped(video_id)`**
```python
# To re-enable minting for a skipped video
mongodb.unmark_video_skipped("abc123")
```

**`get_unminted_videos(limit, include_skipped=False)`**
```python
# Default: excludes skipped videos
unminted = mongodb.get_unminted_videos(limit=10)

# Include skipped videos
all_unminted = mongodb.get_unminted_videos(limit=10, include_skipped=True)
```

---

## 📊 Status Display Updates

The status command now shows skipped videos:

```bash
python mint_nfts.py status
```

```
📊 YouTube NFT Minting Status
======================================================================
📺 Total Videos: 100
✅ Minted NFTs: 45
⏳ Unminted: 50
⏭️  Skipped: 5
======================================================================
```

---

## 🔧 Usage Examples

### Example 1: Handle Network Failure

**Scenario:** Transaction succeeds but network fails during response

```
⛓️  Minting on XRPL...
❌ Minting appears to have failed: Connection timeout

🔍 Transaction was submitted, verifying on-chain status...
🔍 Verifying transaction A1B2C3D4...
✅ Transaction actually SUCCEEDED on-chain!
   NFT ID: 000800003C85C18E326460579DA9BDCE1F96691820E14C8A...
   TX Hash: A1B2C3D4E5F6...

💾 Saving to MongoDB...
✅ Saved to MongoDB
```

**Result:** NFT correctly recorded despite network error

### Example 2: Recover from Previous Failed Attempt

**Scenario:** Previous attempt minted NFT but didn't save to DB

```
⛓️  Minting on XRPL...
❌ Minting appears to have failed: tecDUPLICATE

🔍 Checking if NFT already exists with this URI...
✅ Found existing NFT with matching URI!
   NFT ID: 000800003C85C18E326460579DA9BDCE1F96691820E14C8A...
   This was likely minted in a previous attempt

💾 Saving to MongoDB...
✅ Saved to MongoDB
```

**Result:** Orphaned NFT recovered and linked to video

### Example 3: Duplicate CID Detection

**Scenario:** Same metadata uploaded twice (same CID)

```
🔍 Checking for duplicate CID on XRPL...
⚠️  DUPLICATE DETECTED!
   CID: QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o
   Existing NFT ID: 000800003C85C18E326460579DA9BDCE1F96691820E14C8A...
   This CID is already minted on XRPL
   Found in database for video: xyz789

❓ What would you like to do?
   1. Skip this video (will not retry)
   2. Continue anyway (will attempt to mint duplicate)
   3. Abort minting process

Enter choice (1/2/3): 1

⏭️  Skipping video abc123
```

**Result:** Video marked as skipped, won't appear in unminted list

---

## 🛠️ Managing Skipped Videos

### View Skipped Videos

```python
# Using MongoDB directly
from src.services import create_mongodb_service

mongodb = create_mongodb_service()
skipped = list(mongodb.videos.find({"skip_minting": True}))

for video in skipped:
    print(f"{video['video_id']}: {video.get('skip_reason', 'No reason')}")
```

### Unskip a Video

```python
from src.services import create_mongodb_service

mongodb = create_mongodb_service()
mongodb.unmark_video_skipped("abc123")
print("Video abc123 unmarked - will appear in unminted list")
```

### Unskip All Videos

```python
from src.services import create_mongodb_service

mongodb = create_mongodb_service()

# Remove skip flag from all videos
result = mongodb.videos.update_many(
    {"skip_minting": True},
    {"$unset": {"skip_minting": "", "skip_reason": "", "skipped_at": ""}}
)

print(f"Unskipped {result.modified_count} videos")
```

---

## ⚙️ Configuration

### Disable Duplicate Detection (Not Recommended)

If you want to disable duplicate detection (e.g., for testing):

Comment out lines 159-192 in `mint_nfts.py`:

```python
# # 4a. Check for duplicate CID on-chain
# print(f"   🔍 Checking for duplicate CID on XRPL...")
# existing_onchain_nft = xrpl.find_nft_by_uri(uri)
# if existing_onchain_nft:
#     ... [duplicate handling code]
```

**Warning:** This will allow duplicate NFTs to be created.

### Include Skipped Videos in Unminted List

Modify the mint command to include skipped videos:

In `mint_nfts.py`, change:
```python
unminted = mongodb.get_unminted_videos(limit=count)
```

To:
```python
unminted = mongodb.get_unminted_videos(limit=count, include_skipped=True)
```

---

## 📈 Best Practices

### When to Skip
- ✅ Duplicate CID detected for different video
- ✅ Metadata error discovered after upload
- ✅ Video should not be minted (removed from channel, copyright issue, etc.)

### When to Continue Anyway
- ⚠️ You intentionally want duplicate NFTs
- ⚠️ Testing duplicate handling
- ⚠️ You're certain it's a false positive

### When to Abort
- 🛑 Unexpected duplicate pattern (investigate)
- 🛑 Database inconsistency detected
- 🛑 Need to review situation before proceeding

---

## 🔍 Troubleshooting

### Q: Transaction failed but NFT shows in wallet?

**A:** This is normal! The new verification system will:
1. Detect the existing NFT
2. Recover the NFT ID
3. Update MongoDB correctly

### Q: Same CID for different videos?

**A:** This means both videos have identical metadata. Possible causes:
- Same title, description, thumbnail
- Re-uploaded video
- Duplicate entry in database

**Fix:** Check video data and decide to skip or mint duplicate

### Q: How to re-mint a skipped video?

**A:** Unskip it first:
```python
from src.services import create_mongodb_service
mongodb = create_mongodb_service()
mongodb.unmark_video_skipped("video_id")
```

### Q: Transaction verification taking too long?

**A:** Network latency to XRPL node. Consider:
- Using different XRPL node URL
- Checking network connectivity
- Waiting a few seconds and trying again

---

## 🎯 Summary

### Problems Solved

✅ **Network failures with successful transactions**
- Automatic verification of transaction status
- Recovery of orphaned NFTs
- Prevention of duplicate minting attempts

✅ **Duplicate CID detection**
- Pre-minting batch check
- Runtime duplicate detection
- User prompt for handling
- Permanent skip tracking

### Key Features

- 🔍 Transaction verification after failures
- 🔍 Duplicate CID detection before minting
- 💾 Skip tracking in MongoDB
- ❓ Interactive user prompts
- 📊 Enhanced status reporting
- 🔄 Recovery of orphaned NFTs

---

**Last Updated:** 2025-11-08
**Version:** 2.0
