# YouTube NFT Minting Platform
## Complete Backend Documentation

**Version:** 3.0
**Last Updated:** November 14, 2025
**Status:** Production Ready

---

## Document Information

| **Property** | **Value** |
|--------------|-----------|
| **Platform** | XRPL (XRP Ledger) Blockchain |
| **Database** | MongoDB Atlas |
| **Storage** | IPFS via Pinata |
| **Language** | Python 3.13 |
| **License** | Proprietary |

---

# Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Architecture](#2-system-architecture)
3. [Environment Configuration](#3-environment-configuration)
4. [Core Services](#4-core-services)
5. [Backend Scripts](#5-backend-scripts)
6. [NFT Structure & Metadata](#6-nft-structure--metadata)
7. [Database Schema](#7-database-schema)
8. [Testing Procedures](#8-testing-procedures)
9. [Deployment Guide](#9-deployment-guide)
10. [YouTube Integration](#10-youtube-integration)
11. [Troubleshooting](#11-troubleshooting)
12. [Security & Best Practices](#12-security--best-practices)
13. [API Reference](#13-api-reference)
14. [Appendices](#14-appendices)

---

# 1. Executive Summary

## 1.1 Overview

This backend platform automates the minting of YouTube videos as NFTs on the XRP Ledger (XRPL). It provides end-to-end functionality for:

- **NFT Minting:** Converting YouTube videos into blockchain-verified NFTs
- **Decentralized Storage:** Permanent IPFS storage via Pinata for images and metadata
- **Database Tracking:** Complete MongoDB-based tracking of videos and NFTs
- **YouTube Integration:** Automated video description updates with blockchain validation links
- **Blockchain Synchronization:** Recovery and sync of NFTs from XRPL to MongoDB
- **Duplicate Prevention:** Pre-mint and runtime duplicate detection
- **Network Safety:** Automatic testnet/mainnet detection with comprehensive safeguards

## 1.2 Key Features

✅ **Production Ready:** Tested on both testnet and mainnet with safety mechanisms
✅ **IPFS Persistence:** Thumbnails uploaded to IPFS (not relying on YouTube URLs)
✅ **MongoDB Integration:** Full tracking with videos, NFTs, and audit logs
✅ **Network Verification:** Automatic detection and confirmation prompts
✅ **Duplicate Detection:** CID checking before minting
✅ **Transaction Recovery:** Automatic recovery from network failures
✅ **BCA Validation:** Blockchain Content Authenticator integration
✅ **OpenSea Compatible:** Standard NFT metadata format

## 1.3 Technology Stack

| **Component** | **Technology** | **Purpose** |
|---------------|----------------|-------------|
| Blockchain | XRP Ledger (XRPL) | NFT minting and permanent on-chain storage |
| Database | MongoDB Atlas | Video and NFT tracking, audit logs |
| Storage | IPFS (Pinata v3 API) | Decentralized metadata and image storage |
| APIs | YouTube Data API v3 | Video data retrieval and description updates |
| Language | Python 3.13+ | Backend scripting and automation |
| Libraries | xrpl-py 2.5.0, pymongo 4.5.0, requests 2.31.0 | Core integrations |

## 1.4 System Flow

```
┌──────────────┐
│ YouTube API  │─────┐
└──────────────┘     │
                     │
┌──────────────┐     │      ┌─────────────────┐
│ Pinata IPFS  │─────┼─────▶│  Python Backend │
└──────────────┘     │      │    (Services)   │
                     │      └─────────────────┘
┌──────────────┐     │              │
│  XRPL Node   │─────┘              │
└──────────────┘                    │
                        ┌───────────┴───────────┐
                        │                       │
                 ┌──────▼──────┐        ┌──────▼──────┐
                 │   MongoDB   │        │    XRPL     │
                 │  (Tracking) │        │ (Blockchain)│
                 └─────────────┘        └─────────────┘
```

---

# 2. System Architecture

## 2.1 Project Structure

```
mvp-backend/
│
├── src/
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── mongodb_service.py         # MongoDB operations
│       ├── pinata_service.py          # IPFS uploads (Pinata v3 API)
│       ├── xrpl_service.py            # XRPL NFT minting
│       ├── youtube_service.py         # YouTube Data API v3
│       └── youtube_auth.py            # OAuth token management
│
├── docs/                              # Documentation folder
│   ├── COMPLETE_BACKEND_DOCUMENTATION.md  # This file
│   ├── README.md
│   ├── TESTING.md
│   ├── MAINNET_DEPLOYMENT.md
│   ├── NFT_SYNC_GUIDE.md
│   ├── YOUTUBE_DESCRIPTION_UPDATER.md
│   ├── YOUTUBE_QUOTA_GUIDE.md
│   └── [other documentation files]
│
├── mint_nfts.py                       # Main NFT management script
├── query_nfts.py                      # NFT query tool
├── update_youtube_descriptions.py     # Description updater
├── verify_network.py                  # Network verification
├── test_setup.py                      # Service testing
├── get_youtube_oauth_token.py         # OAuth token generator
│
├── .env                               # Environment variables (NEVER commit)
├── .env.example                       # Testnet configuration template
├── .env.mainnet.example               # Mainnet configuration template
├── requirements.txt                   # Python dependencies
├── .gitignore                         # Git exclusions
│
├── client_secrets.json                # YouTube OAuth (NEVER commit)
└── complete_videos.json               # Video data export
```

## 2.2 Data Flow

### Minting Process

```
1. Fetch Video Data from MongoDB
   ↓
2. Upload Thumbnail → IPFS (Pinata)
   ↓ Returns: image_ipfs_hash
3. Create OpenSea Metadata (with IPFS image URL)
   ↓
4. Upload Metadata → IPFS (Pinata)
   ↓ Returns: metadata_ipfs_hash
5. Check for Duplicate CID on XRPL
   ↓ If duplicate → Prompt user
6. Mint NFT on XRPL (with IPFS URI + Memo)
   ↓ Returns: nft_id, tx_hash
7. Save NFT Record → MongoDB
   ↓
8. Log Operation → minting_log Collection
```

### Description Update Process

```
1. Fetch Minted NFTs from MongoDB
   ↓
2. For Each Video:
   ├─ Verify NFT Exists
   ├─ Fetch Current Description from YouTube
   ├─ Check for Existing BCA Text
   ├─ Generate/Update BCA Validation Text
   ├─ Validate Character Limit (5000)
   └─ Update Description via YouTube API (OAuth)
```

---

# 3. Environment Configuration

## 3.1 Required Environment Variables

Create a `.env` file in the project root with the following variables:

### MongoDB Configuration

```bash
# MongoDB Connection
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_DATABASE=bcaxrpldev                    # Database name (NOT MONGODB_DB!)
```

**Note:** The environment variable is `MONGODB_DATABASE`, not `MONGODB_DB`.

### Pinata IPFS Configuration

```bash
# Pinata IPFS (v3 API)
PINATA_JWT_SECRET=your_jwt_token_here
PINATA_GROUP_ID=your_group_id_here
```

**Required Fields:**
- `PINATA_JWT_SECRET`: JWT token from Pinata dashboard
- `PINATA_GROUP_ID`: Group ID for organizing uploads

**Legacy fields (optional, not used):**
- `PINATA_API_KEY`
- `PINATA_API_SECRET`

### XRPL Configuration

```bash
# XRPL Configuration
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234/    # Testnet
XRPL_SECRET=sEdXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX          # Wallet secret
```

**For Mainnet:**
```bash
XRPL_NODE_URL=https://xrplcluster.com/
XRPL_SECRET=sYourMainnetSecretHere
```

### YouTube API Configuration

```bash
# YouTube Data API v3
YOUTUBE_API_KEY=AIzaSyXXXXXXXXXXXXXXXXXXXXXXXXXXXX
YOUTUBE_OAUTH_TOKEN=ya29.a0XXXXXXXXXXXXXXXXXXXXX       # For description updates
```

## 3.2 Environment File Templates

### Testnet Configuration (.env.example)

```bash
# ==================================================
# TESTNET CONFIGURATION
# ==================================================

# Pinata IPFS (Development)
PINATA_JWT_SECRET=your_jwt_token_here
PINATA_GROUP_ID=your_group_id_here

# YouTube API (Development)
YOUTUBE_API_KEY=your_api_key_here
YOUTUBE_OAUTH_TOKEN=your_oauth_token_here

# XRPL TESTNET
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234/
XRPL_SECRET=sTestnetSecretKey

# MongoDB (Development)
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/
MONGODB_DATABASE=bcaxrpldev

# Network Identifier
NETWORK=testnet
```

### Mainnet Configuration (.env.mainnet.example)

```bash
# ==================================================
# MAINNET CONFIGURATION - PRODUCTION
# ⚠️  REAL XRP WILL BE USED ⚠️
# ==================================================

# Pinata IPFS (Production)
PINATA_JWT_SECRET=your_production_jwt
PINATA_GROUP_ID=your_production_group_id

# YouTube API (Production)
YOUTUBE_API_KEY=your_production_api_key
YOUTUBE_OAUTH_TOKEN=your_oauth_token_here

# XRPL MAINNET
XRPL_NODE_URL=https://xrplcluster.com/
XRPL_SECRET=sMainnetSecretKey

# MongoDB (Production)
MONGODB_URI=mongodb+srv://production_user:password@production.mongodb.net/
MONGODB_DATABASE=bcaxrplprod

# Network Identifier
NETWORK=mainnet
```

## 3.3 Service Setup Guides

### 3.3.1 MongoDB Atlas Setup

**Step 1: Create Account**
1. Visit: https://cloud.mongodb.com
2. Sign up for free tier (M0)

**Step 2: Create Cluster**
1. Choose free tier (M0 Sandbox)
2. Select cloud provider and region
3. Wait for cluster creation (3-5 minutes)

**Step 3: Create Database User**
1. Security → Database Access
2. Add New Database User
3. Choose password authentication
4. Save username and password securely

**Step 4: Configure Network Access**
1. Security → Network Access
2. Add IP Address
3. For development: Allow Access from Anywhere (0.0.0.0/0)
4. For production: Restrict to specific IPs

**Step 5: Get Connection String**
1. Databases → Connect
2. Connect your application
3. Copy connection string
4. Replace `<password>` with your database password
5. Add to `MONGODB_URI` in `.env`

### 3.3.2 Pinata IPFS Setup

**Step 1: Create Account**
1. Visit: https://app.pinata.cloud
2. Sign up for free account (1GB storage)

**Step 2: Generate JWT Token**
1. API Keys → New Key
2. Enable permissions:
   - `pinFileToIPFS`
   - `pinJSONToIPFS`
3. Generate Key
4. Copy JWT token → Add to `PINATA_JWT_SECRET`

**Step 3: Get Group ID**
1. Navigate to Files
2. Create a new group or use existing
3. Click on group settings
4. Copy Group ID → Add to `PINATA_GROUP_ID`

### 3.3.3 YouTube API Setup

**Step 1: Create Google Cloud Project**
1. Visit: https://console.cloud.google.com
2. Create new project
3. Name: "YouTube NFT Platform"

**Step 2: Enable YouTube Data API v3**
1. APIs & Services → Library
2. Search: "YouTube Data API v3"
3. Click Enable

**Step 3: Create API Key**
1. APIs & Services → Credentials
2. Create Credentials → API Key
3. Copy key → Add to `YOUTUBE_API_KEY`

**Step 4: Create OAuth 2.0 Client ID** (for description updates)
1. Create Credentials → OAuth client ID
2. Application type: Desktop app
3. Name: "YouTube Description Updater"
4. Download JSON
5. Save as `client_secrets.json` in project root

**Step 5: Generate OAuth Token**
```bash
python get_youtube_oauth_token.py
```
- Browser will open
- Sign in with YouTube channel owner account
- Authorize application
- Token saved to `.env` automatically

### 3.3.4 XRPL Wallet Setup

**Testnet Wallet (Free):**

```bash
# Generate new wallet
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"
```

**Output:**
```
Address: rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Secret: sEdXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

**Fund Testnet Wallet:**
1. Visit: https://faucet.altnet.rippletest.net
2. Enter wallet address
3. Request 1000 XRP (free testnet XRP)

**Mainnet Wallet (Production):**

```bash
# Generate new wallet
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"
```

**⚠️ CRITICAL SECURITY:**
- **Backup secret immediately** in multiple secure locations
- **Never commit to git**
- **Never share** with anyone
- **Loss of secret = permanent loss of funds**

**Fund Mainnet Wallet:**
- Send 15-20 XRP from exchange
- Minimum 10 XRP for account activation
- Additional XRP for transaction fees
- Verify at: https://livenet.xrpl.org

## 3.4 Verification

After configuration, test all services:

```bash
python test_setup.py
```

**Expected Output:**

```
🔧 Testing Environment Variables
   ✅ Pinata IPFS: eyJhbG...
   ✅ YouTube API: AIzaSy...
   ✅ XRPL Node: https://...
   ✅ XRPL Wallet: sEdXXX...
   ✅ MongoDB: mongodb+srv://...

💾 Testing MongoDB Connection
   ✅ Connected to MongoDB
   📊 Database: bcaxrpldev
   📊 Collections: videos, nfts, minting_log

📦 Testing Pinata IPFS Service
   ✅ Pinata connected successfully
   📦 Test IPFS Hash: QmXXX...

⛓️  Testing XRPL Connection
   ✅ Connected to XRPL
   📍 Wallet Address: rXXXX...
   🌐 Node: https://s.altnet.rippletest.net:51234/
   💰 Balance: 1000.00 XRP

📺 Testing YouTube API
   ✅ YouTube API connected
   📹 Test channel fetch successful

🎉 All tests passed! System is ready for minting.
```

---

# 4. Core Services

## 4.1 MongoDB Service

**File:** `src/services/mongodb_service.py`

### Purpose

Complete database solution for NFT and video tracking with audit trails.

### Collections

1. **videos** - YouTube video metadata
2. **nfts** - Minted NFT records with IPFS hashes
3. **minting_log** - Complete audit trail of operations

### Initialization

```python
from src.services import create_mongodb_service

# Reads MONGODB_URI and MONGODB_DATABASE from environment
mongodb = create_mongodb_service()
```

**Output:**
```
MongoDB Service Initialized
  Database: bcaxrpldev
  Collections: videos, nfts, minting_log
```

### Key Methods

#### save_video(video_data: Dict[str, Any]) → Dict[str, Any]

Save or update video data.

**Parameters:**
- `video_data`: Dict containing:
  - `video_id` (required): YouTube video ID
  - `title`: Video title
  - `description`: Video description
  - `published_at`: Publication date
  - `thumbnail_url`: Thumbnail URL
  - `video_url`: YouTube URL
  - `channel_title`: Channel name
  - `channel_id`: YouTube channel ID
  - `category`: Auto-generated category

**Returns:**
```python
{
    'success': True,
    'video_id': 'abc123',
    'matched': 1,          # 1 if existing video updated
    'modified': 1,         # 1 if changes were made
    'upserted': False      # True if new video created
}
```

**Example:**
```python
result = mongodb.save_video({
    "video_id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "description": "The official video...",
    "published_at": "2009-10-25T06:57:33Z",
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "channel_title": "Rick Astley",
    "category": "General"
})
```

#### save_nft(nft_data: Dict[str, Any]) → Dict[str, Any]

Save NFT data after minting.

**Parameters:**
- `nft_data`: Dict containing:
  - `nft_id` (required): XRPL NFT Token ID
  - `video_id` (required): YouTube video ID
  - `tx_hash`: XRPL transaction hash
  - `uri`: IPFS URI (ipfs://...)
  - `metadata_ipfs_hash`: Metadata CID
  - `image_ipfs_hash`: Image CID
  - `taxon`: NFT taxon
  - `account`: Minting wallet address
  - `minted_at`: Timestamp
  - `metadata`: Full OpenSea metadata object
  - `memo_data`: On-chain memo string
  - `network`: "testnet" or "mainnet"

**Returns:**
```python
{
    'success': True,
    'nft_id': '000B0000...',
    'video_id': 'abc123',
    'inserted_id': 'ObjectId(...)'
}
```

**Error Response:**
```python
{
    'success': False,
    'error': 'NFT already exists for video_id: abc123'
}
```

#### get_unminted_videos(limit: int = 100, include_skipped: bool = False) → List[Dict]

Get videos that haven't been minted as NFTs.

**Parameters:**
- `limit`: Maximum number to return (default: 100)
- `include_skipped`: Include videos marked as skipped (default: False)

**Returns:** List of video dictionaries sorted by publication date (ascending)

**Example:**
```python
unminted = mongodb.get_unminted_videos(limit=10)
print(f"Found {len(unminted)} unminted videos")
```

#### get_nft_by_video_id(video_id: str) → Optional[Dict]

Get NFT record by video ID.

**Parameters:**
- `video_id`: YouTube video ID

**Returns:** NFT dictionary or None

**Example:**
```python
nft = mongodb.get_nft_by_video_id("dQw4w9WgXcQ")
if nft:
    print(f"NFT ID: {nft['nft_id']}")
else:
    print("No NFT found for this video")
```

#### get_all_nfts(limit: int = 100, skip: int = 0) → List[Dict]

Get all NFTs from database.

**Parameters:**
- `limit`: Maximum number to return (default: 100)
- `skip`: Number to skip (for pagination)

**Returns:** List of NFT dictionaries sorted by minted_at (descending)

#### mark_video_skipped(video_id: str, reason: str) → Dict

Mark a video to skip during minting.

**Parameters:**
- `video_id`: YouTube video ID
- `reason`: Reason for skipping (e.g., "Duplicate CID: QmXXX...")

**Returns:**
```python
{
    'success': True,
    'modified_count': 1
}
```

**Example:**
```python
mongodb.mark_video_skipped("abc123", "Duplicate CID detected")
```

#### unmark_video_skipped(video_id: str) → Dict

Remove skip flag from a video.

**Example:**
```python
mongodb.unmark_video_skipped("abc123")
```

#### get_minting_stats() → Dict

Get statistics about minting operations.

**Returns:**
```python
{
    'total_videos': 100,
    'total_nfts': 50,
    'unminted_count': 50,
    'category_breakdown': [
        {'_id': 'AI & Technology', 'count': 25},
        {'_id': 'General', 'count': 20},
        ...
    ]
}
```

#### log_minting_operation(video_id, success, nft_id, tx_hash, error) → Dict

Log a minting operation for audit trail.

**Parameters:**
- `video_id`: YouTube video ID
- `success`: Boolean indicating success
- `nft_id`: NFT ID if successful
- `tx_hash`: Transaction hash if successful
- `error`: Error message if failed

---

## 4.2 Pinata Service

**File:** `src/services/pinata_service.py`

### Purpose

IPFS storage via Pinata v3 API for images and JSON metadata.

### Initialization

```python
from src.services import create_pinata_service

# Reads PINATA_JWT_SECRET and PINATA_GROUP_ID from environment
pinata = create_pinata_service()
```

### API Version

This service uses **Pinata v3 API**:
- Upload URL: `https://uploads.pinata.cloud/v3/files`
- API URL: `https://api.pinata.cloud`

### Key Methods

#### upload_json(json_data, name, keyvalues, group_id) → Dict

Upload JSON metadata to IPFS.

**Parameters:**
- `json_data`: Dictionary to upload
- `name` (optional): Name for the pinned content
- `keyvalues` (optional): Metadata tags
- `group_id` (optional): Group ID (uses default if not provided)

**Returns:**
```python
{
    'IpfsHash': 'QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o',
    'PinSize': 1234,
    'Timestamp': '2025-11-14T10:00:00Z',
    'isDuplicate': False
}
```

**Example:**
```python
metadata = {
    "name": "Video Title",
    "description": "Description",
    "image": "ipfs://QmXXX...",
    "attributes": [...]
}

result = pinata.upload_json(
    json_data=metadata,
    name="metadata-video123",
    keyvalues={"type": "youtube_nft_metadata", "video_id": "video123"}
)

metadata_cid = result['IpfsHash']
print(f"Metadata uploaded: ipfs://{metadata_cid}")
```

#### upload_image_from_url(image_url, name, keyvalues, group_id) → Dict

Download image from URL and upload to IPFS.

**Parameters:**
- `image_url`: URL of image to download
- `name` (optional): Filename
- `keyvalues` (optional): Metadata tags
- `group_id` (optional): Group ID

**Returns:** Same format as `upload_json`

**Example:**
```python
result = pinata.upload_image_from_url(
    image_url="https://i.ytimg.com/vi/abc123/maxresdefault.jpg",
    name="thumbnail-abc123.jpg",
    keyvalues={"type": "youtube_thumbnail", "video_id": "abc123"}
)

image_cid = result['IpfsHash']
print(f"Image uploaded: ipfs://{image_cid}")
```

**Features:**
- Automatic retry with exponential backoff (3 attempts)
- Timeout handling (30 seconds for download, 60 for upload)
- Progress logging

---

## 4.3 XRPL Service

**File:** `src/services/xrpl_service.py`

### Purpose

NFT minting and blockchain operations on XRP Ledger.

### Initialization

```python
from src.services import create_xrpl_service

# Reads XRPL_NODE_URL and XRPL_SECRET from environment
xrpl = create_xrpl_service()
```

**Output:**
```
XRPL Service Initialized
  Wallet Address: rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  Node: https://s.altnet.rippletest.net:51234/
```

### Key Methods

#### mint_nft(uri, taxon, transfer_fee, flags, memo_data, memo_type) → Dict

Mint an NFT on XRPL.

**Parameters:**
- `uri`: IPFS URI pointing to metadata (e.g., "ipfs://QmXXX...")
- `taxon` (default: 0): NFToken taxon
- `transfer_fee` (default: 0): Transfer fee in basis points (0-50000)
- `flags` (default: 8): NFToken flags (8 = tfTransferable)
- `memo_data` (optional): Memo data string
- `memo_type` (optional): Memo type string

**Returns (Success):**
```python
{
    'success': True,
    'nft_id': '000B0000E3ECD0E6E0D52E7FD3EF3F89B1234567890ABCDEF...',
    'tx_hash': 'ABC123DEF456789...',
    'uri': 'ipfs://QmXXX...',
    'account': 'rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
    'validated': True
}
```

**Returns (Error):**
```python
{
    'success': False,
    'error': 'Error message',
    'uri': 'ipfs://QmXXX...'
}
```

**Example:**
```python
result = xrpl.mint_nft(
    uri="ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o",
    taxon=0,
    memo_data="This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger",
    memo_type="YouTubeNFTValidation"
)

if result['success']:
    print(f"NFT Minted: {result['nft_id']}")
    print(f"TX Hash: {result['tx_hash']}")
```

**Note:** The `memo_type` parameter is currently commented out in the actual minting code (line 69 of xrpl_service.py).

#### get_account_info() → Dict

Get XRPL account information.

**Returns:**
```python
{
    'success': True,
    'account_data': {
        'Balance': '10000000',      # in drops (1 XRP = 1,000,000 drops)
        'Account': 'rXXXX...',
        'Sequence': 123,
        ...
    }
}
```

**Example:**
```python
info = xrpl.get_account_info()
if info['success']:
    balance_drops = int(info['account_data']['Balance'])
    balance_xrp = balance_drops / 1_000_000
    print(f"Balance: {balance_xrp} XRP")
```

#### get_nfts(account) → Dict

Get NFTs owned by an account.

**Parameters:**
- `account` (optional): Account address (uses wallet address if not provided)

**Returns:**
```python
{
    'success': True,
    'nfts': [
        {
            'NFTokenID': '000B0000...',
            'URI': '697066733A2F2F516D...',  # Hex-encoded
            'Flags': 8,
            'Issuer': 'rXXXX...',
            'NFTokenTaxon': 0,
            'TransferFee': 0
        },
        ...
    ],
    'account': 'rXXXX...'
}
```

#### find_nft_by_uri(uri, account) → Optional[Dict]

Find NFT by URI in account's NFTs.

**Parameters:**
- `uri`: URI to search for (can be full "ipfs://QmXXX..." or just "QmXXX...")
- `account` (optional): Account to search

**Returns:** NFT object if found, None otherwise

**Example:**
```python
existing = xrpl.find_nft_by_uri("ipfs://QmYjtig7VJQ6...")
if existing:
    print(f"NFT already exists: {existing['NFTokenID']}")
else:
    print("No duplicate found, safe to mint")
```

#### verify_transaction_success(tx_hash) → Optional[str]

Verify if a transaction succeeded and extract NFT ID.

**Parameters:**
- `tx_hash`: Transaction hash to verify

**Returns:** NFT ID if successful, None otherwise

**Example:**
```python
nft_id = xrpl.verify_transaction_success("ABC123DEF...")
if nft_id:
    print(f"Transaction succeeded! NFT ID: {nft_id}")
```

---

## 4.4 YouTube Service

**File:** `src/services/youtube_service.py`

### Purpose

YouTube Data API v3 integration for video data retrieval and description updates.

### Initialization

```python
from src.services import create_youtube_service

# Reads YOUTUBE_API_KEY from environment
youtube = create_youtube_service()
```

### Key Methods

#### get_video_details(video_id, include_parts) → Dict

Get detailed video information.

**Parameters:**
- `video_id`: YouTube video ID
- `include_parts` (optional): List of parts to include (default: ["snippet", "contentDetails", "statistics"])

**Returns:** Video details dictionary from YouTube API

**Example:**
```python
details = youtube.get_video_details("dQw4w9WgXcQ")
print(f"Title: {details['snippet']['title']}")
print(f"Description: {details['snippet']['description']}")
```

#### get_video_description(video_id) → str

Get video description.

**Parameters:**
- `video_id`: YouTube video ID

**Returns:** Description text

#### update_video_description(video_id, new_description, oauth_token) → Dict

Update video description.

**Parameters:**
- `video_id`: YouTube video ID
- `new_description`: New description text (max 5000 chars)
- `oauth_token`: OAuth 2.0 access token

**Returns:** Updated video details

**Example:**
```python
oauth_token = os.getenv("YOUTUBE_OAUTH_TOKEN")

result = youtube.update_video_description(
    video_id="abc123",
    new_description="New description with BCA validation...",
    oauth_token=oauth_token
)
```

**Note:** Requires OAuth 2.0 with `https://www.googleapis.com/auth/youtube.force-ssl` scope.

#### fetch_all_videos_from_channel(channel_id, max_results) → List[Dict]

Fetch all videos from a channel.

**Parameters:**
- `channel_id`: YouTube channel ID
- `max_results` (default: 50): Results per page

**Returns:** List of video items

---

# 5. Backend Scripts

## 5.1 mint_nfts.py - Main NFT Management

### Purpose

Primary script for all NFT operations including minting, syncing, and status checking.

### Commands

#### 5.1.1 Sync Videos to MongoDB

```bash
python mint_nfts.py sync [json_file]
```

**Examples:**
```bash
# Use default file (complete_videos.json)
python mint_nfts.py sync

# Use specific file
python mint_nfts.py sync my_videos.json
```

**What it does:**
1. Reads JSON file with video data
2. Transforms YouTube API format to internal format
3. Saves videos to MongoDB
4. Auto-generates categories

**Output:**
```
📥 Syncing videos from complete_videos.json...
   Found 580 videos
   ✅ Synced 580/580 videos
```

#### 5.1.2 Mint NFTs

```bash
python mint_nfts.py mint <count>
```

**Examples:**
```bash
# Mint 1 NFT (test)
python mint_nfts.py mint 1

# Mint 10 NFTs
python mint_nfts.py mint 10

# Mint 100 NFTs
python mint_nfts.py mint 100
```

**Mainnet Safety:** On mainnet, requires typing "CONFIRM" before proceeding.

**Output:**
```
🎨 YouTube NFT Minting Platform
======================================================================
Initializing services...
MongoDB Service Initialized
  Database: bcaxrpldev
  Collections: videos, nfts, minting_log
XRPL Service Initialized
  Wallet Address: rXXXX...
  Node: https://s.altnet.rippletest.net:51234/

✅ Services Ready

🚀 Minting 1 NFT(s)...

[1/1]
🎬 Minting: Rick Astley - Never Gonna Give You Up...
   📸 Uploading thumbnail to IPFS...
      Downloading image from URL (attempt 1/3)...
      Downloaded 52341 bytes
      Uploading to Pinata IPFS (v3 API)...
      Upload successful: QmYjtig7VJQ6XsnUjqqJvj7QaMcCA...
   ✅ Thumbnail: QmYjtig7VJQ6XsnUjqqJvj7QaMcCA...
   📦 Uploading metadata to IPFS...
   ✅ Metadata: QmZZZ7VJQ6XsnUjqqJvj7QaMcCA...
   🔍 Checking for duplicate CID on XRPL...
   ⛓️  Minting on XRPL...

Minting NFT...
  URI: ipfs://QmZZZ7VJQ6XsnUjqqJvj7QaMcCA...
  Taxon: 0
  Transfer Fee: 0

Submitting transaction to XRPL...

NFT Minted Successfully!
  NFT ID: 000B0000E3ECD0E6E0D52E7FD3EF3F89B...
  TX Hash: ABC123DEF456789...

   ✅ NFT Minted!
      NFT ID: 000B0000E3ECD0E6E0D52E7FD3EF3F89B...
      TX Hash: ABC123DEF456789...
   💾 Saving to MongoDB...
   ✅ Saved to MongoDB

📊 Results: 1/1 minted successfully
```

#### 5.1.3 Check Status

```bash
python mint_nfts.py status
```

**Output:**
```
📊 YouTube NFT Minting Status
======================================================================
📺 Total Videos: 580
✅ Minted NFTs: 250
⏳ Unminted: 325
⏭️  Skipped: 5

📂 Category Breakdown:
   AI & Technology: 150 videos
   General: 200 videos
   Automotive: 100 videos
   Business: 80 videos
   Sports: 50 videos

⏳ Next Unminted Videos:
   1. Video Title 1
   2. Video Title 2
   3. Video Title 3
   4. Video Title 4
   5. Video Title 5
======================================================================
```

#### 5.1.4 Sync NFTs from Blockchain

```bash
python mint_nfts.py sync-nfts
```

**Purpose:** Reconcile NFTs on XRPL blockchain with MongoDB database.

**Output:**
```
======================================================================
🔄 NFT Blockchain → MongoDB Sync
======================================================================

📡 Step 1: Fetching NFTs from XRPL blockchain...
   ✅ Found 251 NFTs on blockchain

💾 Step 2: Fetching NFTs from MongoDB...
   ✅ Found 250 NFTs in database

🔍 Step 3: Comparing blockchain vs database...

======================================================================
📊 SYNC ANALYTICS
======================================================================
📡 NFTs on Blockchain:     251
💾 NFTs in Database:       250
✅ Matched (in sync):      250
⚠️  Missing in DB:         1
======================================================================

⚠️  1 NFT(s) on blockchain but NOT in database:
======================================================================

1. NFT ID: 000800003C85C18E326460579DA9BDCE1F96691820E14C8A...
   URI: ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o...
   📺 Associated Video: dQw4w9WgXcQ - Rick Astley - Never Gonna Give You Up

======================================================================

❓ What would you like to do?
   1. Update ALL missing NFTs to database
   2. Select specific NFTs to update
   3. Show detailed info for each missing NFT
   4. Export missing NFT list to file
   5. Skip update (view only)

Enter choice (1/2/3/4/5):
```

---

## 5.2 query_nfts.py - NFT Query Tool

### Purpose

Query and view NFT data from MongoDB.

### Commands

#### List NFTs

```bash
python query_nfts.py list <limit>
```

**Example:**
```bash
python query_nfts.py list 10
```

**Output:**
```
📋 Listing NFTs (limit: 10)

   Found 10 NFT(s):

   1. dQw4w9WgXcQ
      NFT: 000B0000E3ECD0E6E0D52E7FD3EF3F...
      General | Minted: 2025-11-14

   2. abc123xyz
      NFT: 000B0001A2B3C4D5E6F7G8H9I0J1K2...
      AI & Technology | Minted: 2025-11-13

   ...
```

#### Query by Video ID

```bash
python query_nfts.py video <video_id>
```

**Example:**
```bash
python query_nfts.py video dQw4w9WgXcQ
```

**Output:**
```
🔍 Querying NFT for video: dQw4w9WgXcQ

======================================================================
🎨 NFT: dQw4w9WgXcQ
======================================================================

📊 Core Information:
   NFT Token ID: 000B0000E3ECD0E6E0D52E7FD3EF3F89B...
   Video ID: dQw4w9WgXcQ
   TX Hash: ABC123DEF456789...
   Account: rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
   Network: testnet

📦 IPFS Storage:
   Metadata: QmZZZ7VJQ6XsnUjqqJvj7QaMcCA...
   Image: QmYjtig7VJQ6XsnUjqqJvj7QaMcCA...
   URI: ipfs://QmZZZ7VJQ6XsnUjqqJvj7QaMcCA...

🎬 Video Information:
   Title: Rick Astley - Never Gonna Give You Up
   External URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ

🏷️  Attributes:
   contextType: YouTube_NFT
   source: https://www.youtube.com/watch?v=dQw4w9WgXcQ
   channel: Rick Astley
   videoId: dQw4w9WgXcQ
   publishedDate: 2009-10-25
   accountXRPL: rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

📝 On-Chain Memo:
   This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger

⏰ Minted: 2025-11-14 10:30:45 UTC
```

#### Verify NFT Fields

```bash
python query_nfts.py verify
```

**Purpose:** Verify all required fields are present in NFT records.

---

## 5.3 update_youtube_descriptions.py - Description Updater

### Purpose

Automatically update YouTube video descriptions with BCA validation links.

### Commands

#### Check Status Only

```bash
python update_youtube_descriptions.py --check-only
```

**What it does:** Shows which videos need updates without making changes.

#### Dry Run (Simulate)

```bash
python update_youtube_descriptions.py --dry-run
python update_youtube_descriptions.py --dry-run --limit 5
```

**What it does:** Simulates updates without modifying YouTube.

#### Execute Updates

```bash
python update_youtube_descriptions.py --execute
python update_youtube_descriptions.py --execute --limit 10
python update_youtube_descriptions.py --execute --skip 100 --limit 50
python update_youtube_descriptions.py --execute --rate-limit 1.5
```

**Options:**
- `--execute`: Actually update descriptions
- `--limit N`: Process only N videos
- `--skip N`: Skip first N videos (resume from N+1)
- `--rate-limit X`: Delay X seconds between requests (default: 1.0)
- `--oauth-token TOKEN`: Use specific OAuth token

### BCA Validation Text Format

**Template:**
```
This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger — proof it's the genuine article from the official series run. BCA: https://bca.jimflint.com/verify/{nft_token_id}
```

**Placement:** At the very top of the description

**Example:**
```
This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger — proof it's the genuine article from the official series run. BCA: https://bca.jimflint.com/verify/000B0000E3ECD0E6E0D52E7FD3EF3F89B...

[Original video description content...]

#hashtag #tags
```

### Features

✅ **NFT Verification:** Checks NFT exists before updating
✅ **Description Sync:** Fetches latest description from YouTube
✅ **Duplicate Detection:** Detects existing BCA text
✅ **ID Validation:** Ensures NFToken ID matches database
✅ **Character Limit:** Validates 5000 character limit
✅ **Automatic Token Refresh:** Refreshes expired OAuth tokens
✅ **Retry Logic:** Exponential backoff for failed requests
✅ **Progress Tracking:** Real-time ETA and completion percentage

### Output Files

1. **youtube_description_updates.log** - Real-time logging
2. **youtube_update_results_YYYYMMDD_HHMMSS.log** - Detailed report

---

## 5.4 verify_network.py - Network Verification

### Purpose

Verify network configuration and prevent testnet/mainnet mix-ups.

### Usage

```bash
python verify_network.py
```

### What It Checks

1. **Network Detection** - Testnet vs Mainnet from XRPL_NODE_URL
2. **Wallet Configuration** - Secret and balance
3. **Database Configuration** - MongoDB connection and database name
4. **Consistency** - Prevents testnet DB with mainnet node

### Output (Testnet)

```
🔍 XRPL Network Configuration Verification
======================================================================
🟢 Network: TESTNET (Development)
   Safe for testing - no real XRP will be used

📋 Configuration:
   Node URL: https://s.altnet.rippletest.net:51234/
   Database: bcaxrpldev
   Wallet: ✅ Configured
   Balance: 1000.00 XRP
   MongoDB: ✅ Connected

✅ Configuration Valid
```

### Output (Mainnet)

```
🔍 XRPL Network Configuration Verification
======================================================================
🔴 Network: MAINNET (PRODUCTION)
   ⚠️  Real XRP will be used for transactions

📋 Configuration:
   Node URL: https://xrplcluster.com/
   Database: bcaxrplprod
   Wallet: ✅ Configured
   Balance: 15.50 XRP
   MongoDB: ✅ Connected

✅ Configuration Valid
⚠️  You are connected to MAINNET - transactions are permanent!
```

---

## 5.5 test_setup.py - Service Testing

### Purpose

Verify all services are configured correctly.

### Usage

```bash
python test_setup.py
```

### Tests Performed

1. Environment Variables
2. MongoDB Connection
3. Pinata IPFS Service
4. XRPL Connection
5. YouTube API
6. Data Flow (save/retrieve)

---

## 5.6 get_youtube_oauth_token.py - OAuth Generator

### Purpose

Generate YouTube OAuth 2.0 tokens for description updates.

### Usage

```bash
python get_youtube_oauth_token.py
```

### Process

1. Reads `client_secrets.json`
2. Opens browser for Google authentication
3. Requests `youtube.force-ssl` permission
4. Saves token to `YOUTUBE_OAUTH_TOKEN` in `.env`

**Note:** OAuth tokens expire after ~1 hour. The update script automatically refreshes them.

---

# 6. NFT Structure & Metadata

## 6.1 On-Chain Memo

**Current Implementation:**

The memo is a simple string (not JSON):

```
This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger
```

**Memo Type:** `"YouTubeNFTValidation"`

**Note:** The memo_type is currently commented out in the code (line 69 of xrpl_service.py).

**Previous Format (Commented Out):**

Lines 198-206 of mint_nfts.py show the old JSON format (no longer used):

```json
{
  "id": "video_id",
  "title": "Video Title",
  "url": "https://www.youtube.com/watch?v=...",
  "thumb": "https://i.ytimg.com/vi/.../hqdefault.jpg",
  "channel": "Channel Name",
  "date": "2025-10-27",
  "category": "AI & Technology"
}
```

## 6.2 Full Metadata (IPFS)

**OpenSea-compatible metadata stored on IPFS:**

```json
{
  "name": "Rick Astley - Never Gonna Give You Up",
  "description": "YouTube video from @Rick Astley. Published on October 25, 2009. This NFT represents verified content on the XRPL blockchain. Original video: https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "image": "ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o",
  "external_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "attributes": [
    {
      "trait_type": "contextType",
      "value": "YouTube_NFT"
    },
    {
      "trait_type": "source",
      "value": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    },
    {
      "trait_type": "channel",
      "value": "Rick Astley"
    },
    {
      "trait_type": "videoId",
      "value": "dQw4w9WgXcQ"
    },
    {
      "trait_type": "publishedDate",
      "value": "2009-10-25"
    },
    {
      "trait_type": "accountXRPL",
      "value": "rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
    }
  ]
}
```

**Note:** The `category` attribute is commented out (line 140 of mint_nfts.py).

## 6.3 IPFS URI Format

```
ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o
```

**Access URLs:**
- Pinata Gateway: `https://gateway.pinata.cloud/ipfs/QmYjtig7...`
- Public Gateway: `https://ipfs.io/ipfs/QmYjtig7...`
- Cloudflare Gateway: `https://cloudflare-ipfs.com/ipfs/QmYjtig7...`

---

# 7. Database Schema

## 7.1 Videos Collection

```javascript
{
  _id: ObjectId("..."),
  video_id: "dQw4w9WgXcQ",              // Unique, indexed
  title: "Rick Astley - Never Gonna Give You Up",
  description: "The official video...",
  published_at: "2009-10-25T06:57:33Z",
  thumbnail_url: "https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
  video_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  channel_title: "Rick Astley",
  channel_id: "UCuAXFkgsw1L7xaCfnd5JJOw",
  category: "General",                  // Auto-generated
  skip_minting: false,                  // Optional: skip flag
  skip_reason: "",                      // Optional: skip reason
  skipped_at: null,                     // Optional: skip timestamp
  created_at: ISODate("2025-11-14T10:00:00Z"),
  updated_at: ISODate("2025-11-14T10:00:00Z")
}
```

**Indexes:**
- `video_id` (unique)
- `published_at` (descending)
- `category`

## 7.2 NFTs Collection

```javascript
{
  _id: ObjectId("..."),
  nft_id: "000B0000E3ECD0E6E0D52E7FD3EF3F89B1234567890ABCDEF...",  // Unique
  video_id: "dQw4w9WgXcQ",                                          // Unique
  tx_hash: "ABC123DEF456789...",
  uri: "ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o",
  metadata_ipfs_hash: "QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o",
  image_ipfs_hash: "QmZZZ7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o",
  taxon: 3735928559,                    // Generated from video_id hash
  account: "rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
  minted_at: ISODate("2025-11-14T10:30:45Z"),
  network: "testnet",                   // "testnet" or "mainnet"
  metadata: {                           // Full OpenSea metadata
    "name": "Rick Astley - Never Gonna Give You Up",
    "description": "YouTube video from @Rick Astley...",
    "image": "ipfs://QmZZZ...",
    "external_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "attributes": [...]
  },
  memo_data: "This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger",
  created_at: ISODate("2025-11-14T10:30:45Z")
}
```

**Indexes:**
- `nft_id` (unique)
- `video_id` (unique)
- `tx_hash`
- `minted_at` (descending)

## 7.3 Minting Log Collection

```javascript
{
  _id: ObjectId("..."),
  video_id: "dQw4w9WgXcQ",
  success: true,
  timestamp: ISODate("2025-11-14T10:30:45Z"),
  nft_id: "000B0000E3ECD0E6E0D52E7FD3EF3F89B...",
  tx_hash: "ABC123DEF456789...",
  error: null
}
```

**Indexes:**
- `timestamp` (descending)
- `video_id`

---

# 8. Testing Procedures

## 8.1 Pre-Testing Checklist

- [ ] All environment variables configured in `.env`
- [ ] MongoDB connection tested
- [ ] Pinata JWT token and Group ID verified
- [ ] XRPL wallet funded (testnet: from faucet)
- [ ] YouTube API key active
- [ ] `requirements.txt` dependencies installed

## 8.2 Test Suite

### Step 1: Test All Services

```bash
python test_setup.py
```

**Expected:** All tests pass with ✅

### Step 2: Verify Network

```bash
python verify_network.py
```

**Expected:** Network correctly detected, configuration valid

### Step 3: Sync Test Videos

```bash
python mint_nfts.py sync complete_videos.json
```

**Expected:** Videos imported to MongoDB

### Step 4: Check Status

```bash
python mint_nfts.py status
```

**Expected:** Shows video counts and categories

### Step 5: Test Mint (Single NFT)

```bash
python mint_nfts.py mint 1
```

**Expected:**
- Thumbnail uploaded to IPFS
- Metadata uploaded to IPFS
- NFT minted on XRPL
- Record saved to MongoDB

### Step 6: Verify NFT Data

```bash
python query_nfts.py verify
```

**Expected:** All required fields present

### Step 7: Query NFT

```bash
python query_nfts.py list 5
```

**Expected:** Lists NFTs with details

---

# 9. Deployment Guide

## 9.1 Testnet Deployment

### Setup

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Edit with testnet credentials

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create testnet wallet
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"

# 4. Fund from faucet
# Visit: https://faucet.altnet.rippletest.net

# 5. Verify
python verify_network.py
python test_setup.py
```

### Workflow

```bash
# Sync videos
python mint_nfts.py sync complete_videos.json

# Check status
python mint_nfts.py status

# Test mint
python mint_nfts.py mint 1

# Verify
python query_nfts.py verify

# Batch mint
python mint_nfts.py mint 10
```

## 9.2 Mainnet Deployment

### Pre-Deployment Checklist

- [ ] Tested thoroughly on testnet
- [ ] Mainnet wallet created and backed up securely
- [ ] Wallet funded with 15-20 XRP
- [ ] Production MongoDB configured
- [ ] Production Pinata account ready
- [ ] Team trained on procedures
- [ ] All documentation reviewed

### Deployment Steps

**Step 1: Create Mainnet Wallet**

```bash
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"
```

**⚠️ CRITICAL:** Backup secret immediately in multiple secure locations!

**Step 2: Fund Wallet**

Send 15-20 XRP from exchange to wallet address.

**Step 3: Configure Environment**

```bash
# Backup current config
cp .env .env.testnet.backup

# Use mainnet template
cp .env.mainnet.example .env

# Edit configuration
nano .env
```

**Required changes:**
```bash
XRPL_NODE_URL=https://xrplcluster.com/
XRPL_SECRET=sYourMainnetSecret
MONGODB_URI=mongodb+srv://production...
MONGODB_DATABASE=bcaxrplprod
NETWORK=mainnet
```

**Step 4: Verify Configuration**

```bash
python verify_network.py
```

**Expected:**
```
🔴 Network: MAINNET (PRODUCTION)
   ⚠️  Real XRP will be used for transactions
```

**Step 5: Test Single Mint**

```bash
python mint_nfts.py mint 1
```

**Confirmation required:**
```
======================================================================
⚠️  MAINNET OPERATION WARNING
======================================================================
You are about to perform: Mint 1 NFT(s) on MAINNET
This will use REAL XRP on the XRPL mainnet.
Transactions are PERMANENT and CANNOT be reversed.
======================================================================

Type 'CONFIRM' to proceed with mainnet operation: CONFIRM
```

**Step 6: Verify Transaction**

Visit: https://livenet.xrpl.org
Search wallet address → Verify NFT appears

**Step 7: Production Minting**

```bash
python mint_nfts.py mint 100
python mint_nfts.py status
```

### Cost Estimation

| **Component** | **Amount** | **Notes** |
|---------------|------------|-----------|
| Account Reserve | 10 XRP | Minimum to activate |
| Transaction Fees | 5-10 XRP | For 500-5000 NFTs |
| **Recommended Total** | **15-20 XRP** | Safe buffer |

**Per-NFT Cost:**
- NFTokenMint: ~0.00001 XRP
- Average: ~0.00002 XRP per NFT

**Examples:**
- 100 NFTs: ~0.002 XRP
- 500 NFTs: ~0.01 XRP
- 1,000 NFTs: ~0.02 XRP
- 5,000 NFTs: ~0.1 XRP

---

# 10. YouTube Integration

## 10.1 Description Updater Overview

Automatically updates video descriptions with BCA validation links after NFT minting.

### BCA Template

```
This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger — proof it's the genuine article from the official series run. BCA: https://bca.jimflint.com/verify/{nft_token_id}
```

### Features

✅ NFT verification before updating
✅ Latest description sync from YouTube
✅ Existing BCA text detection
✅ NFToken ID validation
✅ 5000 character limit validation
✅ Automatic OAuth token refresh
✅ Retry logic with exponential backoff
✅ Rate limiting
✅ Progress tracking with ETA

### Quick Start

```bash
# 1. Generate OAuth token
python get_youtube_oauth_token.py

# 2. Check status
python update_youtube_descriptions.py --check-only

# 3. Test (dry run)
python update_youtube_descriptions.py --dry-run --limit 1

# 4. Execute updates
python update_youtube_descriptions.py --execute
```

### API Quota Management

**YouTube Data API v3 Limits:**
- Default quota: 10,000 units/day
- Update cost: ~50 units per video
- Maximum: ~200 updates/day

**Solution:** Use `--skip` parameter to resume after quota reset.

**Example:**
```bash
# Day 1: Updated 198 videos
python update_youtube_descriptions.py --execute

# Day 2: Resume from video 199
python update_youtube_descriptions.py --execute --skip 198
```

---

# 11. Troubleshooting

## 11.1 Common Issues

### Environment Variables

**Issue:** "MONGODB_DATABASE environment variable is required"

**Solution:**
```bash
# Check .env file
cat .env | grep MONGODB

# Ensure it says MONGODB_DATABASE, not MONGODB_DB
MONGODB_DATABASE=bcaxrpldev
```

### MongoDB Connection

**Issue:** "Failed to connect to MongoDB"

**Solutions:**
1. Verify URI format: `mongodb+srv://username:password@cluster.mongodb.net/`
2. Check username/password
3. Whitelist IP address in MongoDB Atlas
4. Test: `python test_setup.py`

### Pinata IPFS

**Issue:** "PINATA_GROUP_ID environment variable is required"

**Solution:**
```bash
# Add both required variables
PINATA_JWT_SECRET=your_jwt_token
PINATA_GROUP_ID=your_group_id
```

**Issue:** "Failed to upload image to Pinata"

**Solutions:**
1. Verify JWT token is correct
2. Check Pinata account status
3. Verify available storage quota
4. Check Group ID is valid

**Note:** Script falls back to YouTube URL if IPFS upload fails.

### XRPL Connection

**Issue:** "Insufficient XRP balance"

**Testnet:**
```bash
# Visit faucet
# https://faucet.altnet.rippletest.net
# Enter wallet address
```

**Mainnet:**
- Fund wallet with 15-20 XRP from exchange

### YouTube API

**Issue:** "OAuth token required"

**Solution:**
```bash
python get_youtube_oauth_token.py
```

**Issue:** "403 Forbidden"

**Causes:**
1. Quota exhausted → Wait for midnight PT reset
2. OAuth scope insufficient → Regenerate token
3. API not enabled → Enable in Google Cloud Console

---

# 12. Security & Best Practices

## 12.1 Wallet Security

1. **Never share wallet secret** - Complete control of wallet
2. **Backup securely** - Multiple offline locations
3. **Use dedicated wallets** - Separate from personal holdings
4. **Monitor activity** - Regular checks on XRPL explorer

## 12.2 Environment Security

```bash
# Verify .env in .gitignore
cat .gitignore | grep .env

# Check git history for secrets
git log --all -p | grep -i "secret\|password\|key"

# Set file permissions
chmod 600 .env
```

## 12.3 Production Checklist

- [ ] Wallet secret backed up offline
- [ ] `.env` NOT in git repository
- [ ] Strong passwords for all services
- [ ] API keys restricted to application
- [ ] MongoDB network access restricted
- [ ] Database backups enabled
- [ ] Regular security audits scheduled

---

# 13. API Reference

## 13.1 Environment Variables

| **Variable** | **Required** | **Example** | **Description** |
|--------------|--------------|-------------|-----------------|
| `MONGODB_URI` | Yes | `mongodb+srv://user:pass@cluster.mongodb.net/` | MongoDB connection string |
| `MONGODB_DATABASE` | Yes | `bcaxrpldev` | Database name |
| `PINATA_JWT_SECRET` | Yes | `eyJhbGc...` | Pinata JWT token |
| `PINATA_GROUP_ID` | Yes | `01234567-89ab-cdef...` | Pinata group ID |
| `XRPL_NODE_URL` | Yes | `https://s.altnet.rippletest.net:51234/` | XRPL node URL |
| `XRPL_SECRET` | Yes | `sEdXXX...` | XRPL wallet secret |
| `YOUTUBE_API_KEY` | Yes | `AIzaSy...` | YouTube Data API v3 key |
| `YOUTUBE_OAUTH_TOKEN` | For updates | `ya29.a0...` | OAuth 2.0 access token |
| `NETWORK` | Recommended | `testnet` | Network identifier |

## 13.2 XRPL Node URLs

**Testnet:**
- Primary: `https://s.altnet.rippletest.net:51234/`
- WebSocket: `wss://s.altnet.rippletest.net:51233`

**Mainnet:**
- Primary: `https://xrplcluster.com/`
- Alternative 1: `https://s2.ripple.com:51234/`
- Alternative 2: `wss://xrplcluster.com/`
- Alternative 3: `https://s1.ripple.com:51234/`

## 13.3 Command Quick Reference

```bash
# Setup
cp .env.example .env
pip install -r requirements.txt
python test_setup.py
python verify_network.py

# Minting
python mint_nfts.py sync complete_videos.json
python mint_nfts.py mint 10
python mint_nfts.py status
python mint_nfts.py sync-nfts

# Queries
python query_nfts.py list 10
python query_nfts.py video <video_id>
python query_nfts.py verify

# Description Updates
python get_youtube_oauth_token.py
python update_youtube_descriptions.py --check-only
python update_youtube_descriptions.py --execute --limit 10
```

---

# 14. Appendices

## 14.1 MongoDB Collections Summary

| **Collection** | **Purpose** | **Key Fields** |
|----------------|-------------|----------------|
| `videos` | YouTube video metadata | `video_id`, `title`, `description`, `category` |
| `nfts` | Minted NFT records | `nft_id`, `video_id`, `tx_hash`, `uri` |
| `minting_log` | Audit trail | `video_id`, `success`, `timestamp`, `error` |

## 14.2 IPFS Gateways

| **Gateway** | **URL Format** |
|-------------|----------------|
| Pinata | `https://gateway.pinata.cloud/ipfs/{CID}` |
| Public | `https://ipfs.io/ipfs/{CID}` |
| Cloudflare | `https://cloudflare-ipfs.com/ipfs/{CID}` |

## 14.3 Explorer URLs

| **Network** | **URL** |
|-------------|---------|
| XRPL Testnet | https://testnet.xrpl.org |
| XRPL Mainnet | https://livenet.xrpl.org |
| Alternative | https://xrpscan.com |

## 14.4 Useful Links

- **XRPL Documentation:** https://xrpl.org
- **XRPL Status:** https://status.xrpl.org
- **XRPL Discord:** https://discord.gg/xrpl
- **MongoDB Atlas:** https://cloud.mongodb.com
- **Pinata Dashboard:** https://app.pinata.cloud
- **Google Cloud Console:** https://console.cloud.google.com
- **YouTube API Quotas:** https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
- **XRPL Testnet Faucet:** https://faucet.altnet.rippletest.net

## 14.5 Category Classification

Videos are auto-categorized based on title and description keywords:

| **Category** | **Keywords** |
|--------------|--------------|
| **AI & Technology** | ai, chatgpt, grok, llm, artificial intelligence |
| **Automotive** | car, dealer, automotive, vehicle |
| **Sports** | nfl, football, sports, game |
| **Business** | business, entrepreneur, marketing |
| **General** | Default for all others |

## 14.6 Document History

| **Version** | **Date** | **Changes** |
|-------------|----------|-------------|
| 1.0 | 2025-10-27 | Initial documentation |
| 2.0 | 2025-11-08 | Added mainnet deployment |
| 3.0 | 2025-11-14 | Accurate codebase documentation, Word formatting |

---

**END OF COMPLETE BACKEND DOCUMENTATION**

This document provides complete, accurate information based on the actual codebase implementation. All code examples, environment variables, and data structures match the source code exactly.

For questions or updates, review the source code in `src/services/` and main scripts.
