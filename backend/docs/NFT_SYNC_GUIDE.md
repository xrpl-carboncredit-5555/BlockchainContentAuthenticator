# NFT Blockchain Sync Guide

Complete guide for syncing NFTs from XRPL blockchain to MongoDB database.

---

## 🎯 Purpose

The `sync-nfts` command reconciles NFTs that exist on the XRPL blockchain with your MongoDB database. This is useful when:

- NFTs were minted but database wasn't updated (network failures)
- Database was accidentally cleared or corrupted
- Migrating from another system
- Auditing blockchain vs database consistency

---

## 🚀 Quick Start

### Run Sync Command

```bash
python mint_nfts.py sync-nfts
```

### What Happens

1. **Fetches all NFTs** from your XRPL wallet
2. **Compares** with NFTs in MongoDB
3. **Shows analytics** (matched, missing, orphaned)
4. **Prompts for action** if discrepancies found
5. **Updates database** based on your selection

---

## 📊 Example Output

### Step 1: Fetching Data

```
======================================================================
🔄 NFT Blockchain → MongoDB Sync
======================================================================

📡 Step 1: Fetching NFTs from XRPL blockchain...
   ✅ Found 580 NFTs on blockchain

💾 Step 2: Fetching NFTs from MongoDB...
   ✅ Found 579 NFTs in database

🔍 Step 3: Comparing blockchain vs database...
```

### Step 2: Analytics

```
======================================================================
📊 SYNC ANALYTICS
======================================================================
📡 NFTs on Blockchain:     580
💾 NFTs in Database:       579
✅ Matched (in sync):      579
⚠️  Missing in DB:         1
======================================================================
```

### Step 3: Missing NFTs Details

```
⚠️  1 NFT(s) on blockchain but NOT in database:
======================================================================

1. NFT ID: 000800003C85C18E326460579DA9BDCE1F96691820E14C8A169D304200B2CFA7
   URI: ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o...
   📺 Associated Video: dQw4w9WgXcQ - Rick Astley - Never Gonna Give You Up

======================================================================
```

### Step 4: User Prompt

```
❓ What would you like to do?
   1. Update ALL missing NFTs to database
   2. Select specific NFTs to update
   3. Show detailed info for each missing NFT
   4. Export missing NFT list to file
   5. Skip update (view only)

Enter choice (1/2/3/4/5):
```

---

## 🎛️ Options Explained

### Option 1: Update ALL Missing NFTs

**When to use:**
- You trust all blockchain NFTs are valid
- Want to quickly sync everything

**What happens:**
```
🔄 Updating 1 NFT(s) to database...

[1/1] Updating 000800003C85C18E...
   ✅ Found associated video: dQw4w9WgXcQ
   ✅ Saved to MongoDB

======================================================================
📊 UPDATE RESULTS
======================================================================
✅ Successfully updated: 1
❌ Failed: 0
======================================================================
```

### Option 2: Select Specific NFTs

**When to use:**
- Only want to sync certain NFTs
- Want to review each NFT before syncing

**Example:**
```
📝 Select NFTs to update (enter numbers separated by comma, or 'all'):
   1. 000800003C85C18E... - ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaM...
   2. 000800003C85C18F... - ipfs://QmXXXXXXXXXXXXXXXXXXXXXXXXX...
   3. 000800003C85C190... - ipfs://QmYYYYYYYYYYYYYYYYYYYYYYYYY...

Enter selection: 1,3

🔄 Updating 2 NFT(s) to database...
[1/2] Updating 000800003C85C18E...
   ✅ Saved to MongoDB
[2/2] Updating 000800003C85C190...
   ✅ Saved to MongoDB
```

### Option 3: Show Detailed Info

**When to use:**
- Want to inspect each NFT before deciding
- Need to verify NFT data

**Example:**
```
======================================================================
📋 DETAILED NFT INFORMATION
======================================================================

======================================================================
NFT #1
======================================================================
NFT ID:       000800003C85C18E326460579DA9BDCE1F96691820E14C8A169D304200B2CFA7
URI:          ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o
Issuer:       rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp
Taxon:        0
Transfer Fee: 0
Flags:        8

📺 Associated Video:
   Video ID: dQw4w9WgXcQ
   Title:    Rick Astley - Never Gonna Give You Up
   URL:      https://www.youtube.com/watch?v=dQw4w9WgXcQ

Press Enter for next NFT...
```

### Option 4: Export to File

**When to use:**
- Want to analyze offline
- Need to share with team
- Keep audit trail

**What happens:**
```
✅ Exported 1 missing NFTs to: missing_nfts_20251109_153045.json
```

**File contents:**
```json
[
  {
    "nft_id": "000800003C85C18E326460579DA9BDCE1F96691820E14C8A169D304200B2CFA7",
    "uri": "ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o",
    "flags": 8,
    "issuer": "rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp",
    "nft_taxon": 0,
    "transfer_fee": 0
  }
]
```

### Option 5: Skip Update (View Only)

**When to use:**
- Just want to check sync status
- Not ready to update yet
- Investigating discrepancies

**What happens:**
```
✅ Skipping update - view only mode
```

---

## 🔍 How Video Association Works

The sync process tries to find the associated YouTube video:

1. **Extracts CID** from NFT URI (`ipfs://QmXXX...`)
2. **Searches videos** collection for matching `metadata_ipfs_hash`
3. **If found:** Links NFT to video
4. **If not found:** Creates placeholder video ID

### Example: Video Found

```
[1/1] Updating 000800003C85C18E...
   ✅ Found associated video: dQw4w9WgXcQ
   ✅ Saved to MongoDB
```

**NFT saved with:**
```json
{
  "nft_id": "000800003C85C18E...",
  "video_id": "dQw4w9WgXcQ",
  "tx_hash": "RECOVERED_FROM_BLOCKCHAIN",
  "synced_from_blockchain": true
}
```

### Example: Video Not Found

```
[1/1] Updating 000800003C85C18E...
   ⚠️  No associated video found - using placeholder: unknown_000800003C85C18E
   ✅ Saved to MongoDB
```

**NFT saved with:**
```json
{
  "nft_id": "000800003C85C18E...",
  "video_id": "unknown_000800003C85C18E",
  "tx_hash": "RECOVERED_FROM_BLOCKCHAIN",
  "synced_from_blockchain": true
}
```

---

## 📝 Synced NFT Fields

NFTs recovered from blockchain have these fields:

```javascript
{
  nft_id: "000800003C85C18E...",              // NFT Token ID from blockchain
  video_id: "dQw4w9WgXcQ",                    // Associated video or placeholder
  tx_hash: "RECOVERED_FROM_BLOCKCHAIN",       // Special marker
  uri: "ipfs://QmYjtig7VJQ6...",              // From blockchain
  metadata_ipfs_hash: "QmYjtig7VJQ6...",      // Extracted from URI
  image_ipfs_hash: "",                        // Unknown (not in blockchain data)
  taxon: 0,                                   // From blockchain
  account: "rBCA9v3tQMLSnRdEFqN5...",         // Issuer from blockchain
  minted_at: ISODate("2025-11-09..."),        // Current time (original unknown)
  metadata: {},                               // Empty (would need IPFS fetch)
  memo_data: "",                              // Not available
  network: "mainnet",                         // Based on current network
  synced_from_blockchain: true,               // Flag indicating synced
  sync_date: ISODate("2025-11-09...")         // When synced
}
```

---

## 🎯 Use Cases

### Use Case 1: Network Failure Recovery

**Scenario:** NFT was minted but network failed before updating MongoDB

```bash
python mint_nfts.py sync-nfts
```

**Result:**
- Detects missing NFT
- Finds associated video
- Recovers and links correctly

### Use Case 2: Database Migration

**Scenario:** Moving to new MongoDB cluster

**Steps:**
1. Export videos to new cluster
2. Run `sync-nfts` to recover all NFTs
3. All NFTs linked to videos

### Use Case 3: Audit Blockchain vs Database

**Scenario:** Want to verify data integrity

```bash
python mint_nfts.py sync-nfts
# Choose option 5 (view only)
```

**Result:**
- Shows sync analytics
- No changes made
- Audit trail of differences

### Use Case 4: Orphaned NFT Detection

**Scenario:** NFTs in database but not on blockchain (transferred/burned)

**Analytics shows:**
```
🔍 Extra in DB (orphaned): 5
```

**Action:** Manual review needed for orphaned entries

---

## 🛠️ Advanced Usage

### Scripted Sync (No Interaction)

For automated syncing, you can modify the code or use expect:

```bash
# This is conceptual - would need implementation
echo "1" | python mint_nfts.py sync-nfts
```

### Filtering Synced NFTs

Query NFTs that were synced from blockchain:

```javascript
// MongoDB query
db.nfts.find({ synced_from_blockchain: true })
```

### Finding Placeholder Videos

Find NFTs without real video association:

```javascript
// MongoDB query
db.nfts.find({ video_id: /^unknown_/ })
```

### Re-linking Placeholder Videos

If you later add the video to database:

```python
from src.services import create_mongodb_service

mongodb = create_mongodb_service()

# Update NFT with correct video_id
mongodb.nfts.update_one(
    {"video_id": "unknown_000800003C85C18E"},
    {"$set": {"video_id": "dQw4w9WgXcQ"}}
)
```

---

## 📊 Understanding Analytics

### Matched NFTs

```
✅ Matched (in sync): 579
```

**Meaning:** These NFTs exist on both blockchain and database with matching IDs.
**Action:** None needed - these are in sync.

### Missing in Database

```
⚠️  Missing in DB: 1
```

**Meaning:** NFT exists on blockchain but not in MongoDB.
**Possible causes:**
- Network failure during minting
- Database corruption/loss
- NFT minted externally

**Action:** Sync to database

### Extra in Database (Orphaned)

```
🔍 Extra in DB (orphaned): 5
```

**Meaning:** NFT in database but not on blockchain.
**Possible causes:**
- NFT was burned
- NFT was transferred to another wallet
- Wrong wallet being checked
- Database has stale data

**Action:** Manual review - may need cleanup

### Parse Errors

```
❌ Parse Errors: 2
```

**Meaning:** Could not decode NFT URI from hex.
**Action:** Manual investigation needed

---

## ⚠️ Important Notes

### Limitations

1. **No transaction history** - Synced NFTs don't have original transaction hash
2. **No metadata** - Would need separate IPFS fetch to get full metadata
3. **No memo data** - AccountNFTs response doesn't include memos
4. **Estimated mint time** - Uses sync time, not original mint time

### Data Accuracy

Synced fields that are **accurate:**
- ✅ NFT ID
- ✅ URI / CID
- ✅ Issuer
- ✅ Taxon
- ✅ Flags

Synced fields that are **approximations:**
- ⚠️ minted_at (uses current time)
- ⚠️ tx_hash (marked as "RECOVERED_FROM_BLOCKCHAIN")

Synced fields that are **empty/unavailable:**
- ❌ metadata (needs IPFS fetch)
- ❌ memo_data (not in AccountNFTs response)
- ❌ image_ipfs_hash (not determinable)

### Safety

- **Read-only until you choose** - No changes until you select option
- **Selective updates** - Can choose specific NFTs
- **Non-destructive** - Only adds missing data, doesn't modify existing
- **Audit trail** - Synced NFTs flagged with `synced_from_blockchain: true`

---

## 🔧 Troubleshooting

### Q: "Could not fetch NFTs from XRPL"

**Cause:** Network connection issue or XRPL node unavailable

**Solution:**
```bash
# Verify network connection
python verify_network.py

# Try different XRPL node
# Update XRPL_NODE_URL in .env
```

### Q: No associated video found for all NFTs

**Cause:** Videos collection is empty or metadata_ipfs_hash not stored

**Solution:**
1. Check if videos exist in database
2. Verify videos have `metadata_ipfs_hash` field
3. May need to re-sync videos first

### Q: Analytics shows many orphaned NFTs

**Possible causes:**
1. NFTs were transferred to another wallet
2. NFTs were burned
3. Checking wrong wallet address

**Solution:**
1. Verify wallet address matches
2. Check NFT history on XRPL explorer
3. Clean up database if confirmed

### Q: Sync creates duplicate NFTs

**Cause:** `save_nft()` doesn't check for existing NFT ID

**Prevention:** The sync process checks before updating

---

## 📈 Best Practices

### Before Syncing

1. **Backup database** - Just in case
2. **Verify network** - Run `python verify_network.py`
3. **Check wallet** - Ensure correct wallet address
4. **Review analytics** - Use option 5 (view only) first

### During Syncing

1. **Review missing NFTs** - Check if they make sense
2. **Use selective update** - If unsure, sync one at a time
3. **Check video associations** - Verify linkages are correct

### After Syncing

1. **Verify counts** - Run `python mint_nfts.py status`
2. **Check synced NFTs** - Query flagged entries
3. **Update placeholders** - Link unknown_* videos if possible

---

## 🎯 Quick Reference

| Command | Purpose |
|---------|---------|
| `python mint_nfts.py sync-nfts` | Run blockchain sync |
| `Option 1` | Update all missing NFTs |
| `Option 2` | Select specific NFTs to update |
| `Option 3` | Review detailed NFT info |
| `Option 4` | Export missing list to JSON |
| `Option 5` | View only (no changes) |

| Field | Accurate? | Notes |
|-------|-----------|-------|
| `nft_id` | ✅ Yes | From blockchain |
| `uri` | ✅ Yes | From blockchain |
| `video_id` | ⚠️ Maybe | If found, otherwise placeholder |
| `minted_at` | ❌ No | Uses current time |
| `tx_hash` | ❌ No | Marked as "RECOVERED" |
| `metadata` | ❌ No | Empty (needs IPFS) |

---

**Last Updated:** 2025-11-09
**Version:** 2.0
