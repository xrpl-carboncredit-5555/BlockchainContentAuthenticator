# YouTube NFT Minting Platform - Complete Documentation

**Version:** 2.0
**Last Updated:** 2025-11-14
**Platform:** XRPL (XRP Ledger)
**Database:** MongoDB
**Storage:** IPFS (Pinata)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Project Structure](#project-structure)
4. [Environment Setup](#environment-setup)
5. [Core Services](#core-services)
6. [Backend Scripts](#backend-scripts)
7. [NFT Metadata Structure](#nft-metadata-structure)
8. [Database Schema](#database-schema)
9. [Testing Guide](#testing-guide)
10. [Deployment](#deployment)
11. [YouTube Description Updater](#youtube-description-updater)
12. [NFT Blockchain Sync](#nft-blockchain-sync)
13. [Duplicate Detection](#duplicate-detection)
14. [API Quota Management](#api-quota-management)
15. [Troubleshooting](#troubleshooting)
16. [Security Best Practices](#security-best-practices)
17. [Appendix](#appendix)

---

## Executive Summary

### What This System Does

This backend platform automates the process of minting YouTube videos as NFTs on the XRP Ledger (XRPL) blockchain. It provides:

- **NFT Minting**: Converts YouTube videos into blockchain-verified NFTs
- **IPFS Storage**: Permanent decentralized storage for thumbnails and metadata
- **MongoDB Tracking**: Complete database tracking of videos and NFTs
- **YouTube Integration**: Updates video descriptions with blockchain validation links
- **Blockchain Sync**: Recovers and syncs NFTs from XRPL to database
- **Duplicate Detection**: Prevents duplicate NFT creation
- **Network Safety**: Automatic testnet/mainnet detection with safeguards

### Key Features

- ✅ **Mainnet Ready**: Production-ready with safety checks and validation
- ✅ **IPFS Persistence**: Images uploaded to IPFS (not just YouTube URLs)
- ✅ **MongoDB Integration**: Complete tracking of videos and NFTs
- ✅ **Network Verification**: Automatic testnet/mainnet detection
- ✅ **Duplicate Detection**: Pre-mint and runtime CID duplicate checking
- ✅ **Transaction Verification**: Automatic recovery from network failures
- ✅ **Auto-Categorization**: Smart video classification
- ✅ **OpenSea Compatible**: Standard NFT metadata format
- ✅ **YouTube Description Updates**: Automated BCA validation text insertion
- ✅ **Blockchain Recovery**: Sync NFTs from XRPL to MongoDB

### Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Blockchain** | XRPL (XRP Ledger) | NFT minting and permanent storage |
| **Database** | MongoDB Atlas | Video and NFT tracking |
| **Storage** | IPFS (Pinata) | Decentralized metadata and image storage |
| **APIs** | YouTube Data API v3 | Video data and description updates |
| **Language** | Python 3.13 | Backend scripting |
| **Libraries** | xrpl-py, pymongo, requests | Core integrations |

---

## System Overview

### Architecture Diagram

```
┌─────────────────┐
│  YouTube API    │──┐
└─────────────────┘  │
                     │
┌─────────────────┐  │    ┌──────────────────┐
│   Pinata IPFS   │──┼───▶│  Backend System  │
└─────────────────┘  │    │   (Python 3.13)  │
                     │    └──────────────────┘
┌─────────────────┐  │            │
│   XRPL Node     │──┘            │
└─────────────────┘               │
                                  │
                     ┌────────────┴────────────┐
                     │                         │
              ┌──────▼──────┐          ┌──────▼──────┐
              │  MongoDB    │          │   XRPL      │
              │   Database  │          │ Blockchain  │
              └─────────────┘          └─────────────┘
```

### Data Flow

1. **Video Sync**: Fetch videos from YouTube API → Store in MongoDB
2. **NFT Minting**:
   - Upload thumbnail to IPFS (Pinata)
   - Create OpenSea-compatible metadata
   - Upload metadata to IPFS
   - Mint NFT on XRPL with IPFS URI
   - Save NFT record to MongoDB
3. **Description Update**: Update YouTube video description with BCA validation link
4. **Blockchain Sync**: Recover missing NFTs from XRPL to MongoDB

---

## Project Structure

### Directory Layout

```
mvp-backend/
├── src/
│   └── services/
│       ├── __init__.py
│       ├── mongodb_service.py      # MongoDB operations
│       ├── pinata_service.py       # IPFS uploads (images + metadata)
│       ├── xrpl_service.py         # XRPL NFT minting
│       ├── youtube_service.py      # YouTube API
│       └── youtube_auth.py         # YouTube OAuth handling
│
├── docs/                           # All documentation (NEW)
│   ├── MASTER_DOCUMENTATION.md     # This file
│   ├── README.md                   # Quick start guide
│   ├── TESTING.md                  # Testing procedures
│   ├── MAINNET_DEPLOYMENT.md       # Mainnet deployment guide
│   ├── MAINNET_CHECKLIST.md        # Pre-launch checklist
│   ├── MAINNET_SUMMARY.md          # Quick mainnet overview
│   ├── MAINNET_QUICKSTART.txt      # Quick commands
│   ├── YOUTUBE_DESCRIPTION_UPDATER.md  # Description updater docs
│   ├── YOUTUBE_QUOTA_GUIDE.md      # API quota management
│   ├── QUICKSTART_YOUTUBE_UPDATER.md   # Quick setup guide
│   ├── NFT_SYNC_GUIDE.md           # Blockchain sync guide
│   ├── DUPLICATE_HANDLING.md       # Duplicate detection docs
│   ├── DUPLICATE_RECOVERY_SUMMARY.md
│   └── YOUTUBE_UPDATER_CHANGELOG.md
│
├── mint_nfts.py                    # Main NFT minting script
├── query_nfts.py                   # Query and view NFT data
├── update_youtube_descriptions.py  # Update video descriptions
├── verify_network.py               # Network verification tool
├── test_setup.py                   # Test all services
├── get_youtube_oauth_token.py      # OAuth token generator
│
├── .env                            # Environment variables (NEVER commit)
├── .env.example                    # Testnet environment template
├── .env.mainnet.example            # Mainnet environment template
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git exclusions
│
├── complete_videos.json            # Video data export
└── client_secrets.json             # YouTube OAuth credentials (NEVER commit)
```

### Script Files

| Script | Purpose | Usage |
|--------|---------|-------|
| `mint_nfts.py` | Main NFT management | `python mint_nfts.py mint 10` |
| `query_nfts.py` | Query NFT data | `python query_nfts.py list 10` |
| `update_youtube_descriptions.py` | Update descriptions | `python update_youtube_descriptions.py --execute` |
| `verify_network.py` | Verify configuration | `python verify_network.py` |
| `test_setup.py` | Test all services | `python test_setup.py` |
| `get_youtube_oauth_token.py` | Get OAuth token | `python get_youtube_oauth_token.py` |

---

## Environment Setup

### Prerequisites

**System Requirements:**
- Python 3.13 or higher
- Internet connection
- 500MB+ available disk space

**Required Accounts:**
- MongoDB Atlas account (free tier available)
- Pinata IPFS account (free tier available)
- Google Cloud Platform account (for YouTube API)
- XRPL wallet (testnet for development, mainnet for production)

### Installation Steps

#### 1. Clone/Download Project

```bash
cd /path/to/project
# Project files should be in: mvp-backend/
```

#### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**
- `requests>=2.31.0` - HTTP requests
- `python-dotenv>=1.0.0` - Environment variables
- `xrpl-py>=2.5.0` - XRPL integration
- `pymongo>=4.5.0` - MongoDB driver
- `Pillow>=10.0.0` - Image processing
- `google-auth-oauthlib>=1.0.0` - YouTube OAuth

#### 3. Configure Environment Variables

**For Testnet (Development):**

```bash
cp .env.example .env
nano .env
```

**For Mainnet (Production):**

```bash
cp .env.mainnet.example .env
nano .env
```

### Environment Variable Reference

#### Testnet Configuration (.env.example)

```bash
# Pinata IPFS (Development)
PINATA_JWT_SECRET=your_jwt_token_here

# YouTube API (Development)
YOUTUBE_API_KEY=your_api_key_here
YOUTUBE_OAUTH_TOKEN=your_oauth_token_here

# XRPL TESTNET Configuration
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234/
XRPL_SECRET=sTestnetSecretKey

# MongoDB (Development)
MONGODB_URI=mongodb+srv://user:password@cluster.mongodb.net/
MONGODB_DB=bcaxrpldev

# Network Identifier
NETWORK=testnet
```

#### Mainnet Configuration (.env.mainnet.example)

```bash
# Pinata IPFS (Production)
PINATA_JWT_SECRET=your_production_jwt_token

# YouTube API (Production)
YOUTUBE_API_KEY=your_production_api_key
YOUTUBE_OAUTH_TOKEN=your_oauth_token_here

# XRPL MAINNET Configuration
XRPL_NODE_URL=https://xrplcluster.com/
XRPL_SECRET=sMainnetSecretKey

# MongoDB (Production)
MONGODB_URI=mongodb+srv://production_user:password@production_cluster.mongodb.net/
MONGODB_DB=bcaxrplprod

# Network Identifier
NETWORK=mainnet
```

### Service Setup Guides

#### MongoDB Setup

1. **Create MongoDB Atlas Account**
   - Visit: https://cloud.mongodb.com
   - Sign up for free tier

2. **Create Cluster**
   - Choose free tier (M0)
   - Select region closest to you
   - Wait for cluster creation (3-5 minutes)

3. **Create Database User**
   - Security → Database Access
   - Add new database user
   - Save username and password

4. **Whitelist IP Address**
   - Security → Network Access
   - Add IP Address → Allow Access from Anywhere (0.0.0.0/0)
   - For production: restrict to specific IPs

5. **Get Connection String**
   - Databases → Connect → Connect your application
   - Copy connection string
   - Replace `<password>` with your database password
   - Add to `MONGODB_URI` in `.env`

#### Pinata IPFS Setup

1. **Create Pinata Account**
   - Visit: https://app.pinata.cloud
   - Sign up for free account

2. **Generate API Key**
   - API Keys → New Key
   - Enable: `pinFileToIPFS`, `pinJSONToIPFS`
   - Generate Key
   - Copy JWT token

3. **Add to Environment**
   - Copy JWT to `PINATA_JWT_SECRET` in `.env`

#### YouTube API Setup

1. **Create Google Cloud Project**
   - Visit: https://console.cloud.google.com
   - Create new project

2. **Enable YouTube Data API v3**
   - APIs & Services → Library
   - Search "YouTube Data API v3"
   - Click Enable

3. **Create API Key**
   - APIs & Services → Credentials
   - Create Credentials → API Key
   - Copy key to `YOUTUBE_API_KEY`

4. **Create OAuth 2.0 Credentials** (for description updates)
   - Create Credentials → OAuth client ID
   - Application type: Desktop app
   - Download JSON → Save as `client_secrets.json`

5. **Generate OAuth Token**
   ```bash
   python get_youtube_oauth_token.py
   ```

#### XRPL Wallet Setup

**Testnet (Free):**

```bash
# Generate new testnet wallet
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"

# Fund from faucet
# Visit: https://faucet.altnet.rippletest.net
# Enter wallet address and request XRP
```

**Mainnet (Production):**

```bash
# Generate new mainnet wallet
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"

# IMPORTANT: Backup the secret in a secure location!
# Fund wallet with 15-20 XRP from exchange
# Verify at: https://livenet.xrpl.org
```

### Verification

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

📦 Testing Pinata IPFS Service
   ✅ Pinata connected successfully

⛓️  Testing XRPL Connection
   ✅ Connected to XRPL
   💰 Balance: 10.00 XRP

📺 Testing YouTube API
   ✅ YouTube API connected

🎉 All tests passed! System is ready for minting.
```

---

## Core Services

### MongoDB Service

**File:** `src/services/mongodb_service.py`

**Purpose:** Complete database solution for NFT and video tracking.

#### Collections

1. **videos** - YouTube video metadata
2. **nfts** - Minted NFT records with IPFS hashes
3. **minting_log** - Complete audit trail

#### Key Methods

```python
from src.services import create_mongodb_service

db = create_mongodb_service()

# Save video to database
db.save_video({
    "video_id": "abc123",
    "title": "Video Title",
    "description": "Video description",
    "thumbnail_url": "https://...",
    "video_url": "https://youtube.com/watch?v=abc123",
    "channel_title": "Channel Name",
    "published_at": "2025-10-27"
})

# Get unminted videos
unminted = db.get_unminted_videos(limit=10)

# Save NFT after minting
db.save_nft({
    "nft_id": "000B0000...",
    "video_id": "abc123",
    "tx_hash": "ABC123...",
    "uri": "ipfs://QmXXX...",
    "metadata_ipfs_hash": "QmXXX...",
    "image_ipfs_hash": "QmYYY...",
    "taxon": 123456,
    "account": "rXXXX...",
    "metadata": {...},
    "memo_data": {...}
})

# Get minting statistics
stats = db.get_minting_stats()
# Returns: {"total_videos": 100, "minted": 50, "unminted": 50}

# Get NFT by video ID
nft = db.get_nft_by_video_id("abc123")

# Mark video as skipped
db.mark_video_skipped("abc123", "Duplicate CID: QmXXX...")

# Unmark video
db.unmark_video_skipped("abc123")
```

#### Database Indexes

Automatically created indexes for performance:
- `videos.video_id` (unique)
- `nfts.nft_id` (unique)
- `nfts.video_id` (indexed)

### Pinata Service

**File:** `src/services/pinata_service.py`

**Purpose:** IPFS storage with image upload support.

#### Features

- Upload JSON metadata to IPFS
- Upload images from URLs to IPFS
- Organize uploads with groups and tags
- Update metadata for existing pins

#### Key Methods

```python
from src.services import create_pinata_service

pinata = create_pinata_service()

# Upload image from URL
result = pinata.upload_image_from_url(
    image_url="https://i.ytimg.com/vi/abc123/hqdefault.jpg",
    name="thumbnail-abc123.jpg",
    keyvalues={"type": "youtube_thumbnail", "video_id": "abc123"}
)
# Returns: {"IpfsHash": "QmYYY...", "PinSize": 12345, ...}

# Upload JSON metadata
result = pinata.upload_json(
    json_data={
        "name": "NFT Name",
        "description": "NFT Description",
        "image": "ipfs://QmYYY...",
        "attributes": [...]
    },
    name="metadata-abc123.json"
)
# Returns: {"IpfsHash": "QmXXX...", "PinSize": 678, ...}

# Test connection
test_result = pinata.test_connection()
# Returns: {"success": True, "ipfs_hash": "QmTest..."}
```

#### IPFS URI Format

```
ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o
```

Can be viewed at:
- Pinata Gateway: `https://gateway.pinata.cloud/ipfs/QmYjtig7...`
- Public Gateway: `https://ipfs.io/ipfs/QmYjtig7...`

### XRPL Service

**File:** `src/services/xrpl_service.py`

**Purpose:** NFT minting on XRP Ledger.

#### Features

- Mint NFTs with IPFS URI
- Add memos for on-chain metadata
- Verify transaction success
- Find NFTs by URI (for duplicate detection)
- Get account info and balance

#### Key Methods

```python
from src.services import create_xrpl_service

xrpl = create_xrpl_service()

# Mint NFT
result = xrpl.mint_nft(
    uri="ipfs://QmXXX...",
    taxon=0,
    flags=8,  # tfTransferable
    memo_data='{"id": "abc123", "title": "Video Title"}',
    memo_type="nft_data"
)
# Returns: {
#     "success": True,
#     "nft_id": "000B0000...",
#     "tx_hash": "ABC123...",
#     "message": "NFT minted successfully"
# }

# Get account info
info = xrpl.get_account_info()
# Returns: {
#     "success": True,
#     "account_data": {
#         "Balance": "10000000",  # in drops (1 XRP = 1,000,000 drops)
#         "Account": "rXXXX...",
#         ...
#     }
# }

# Verify transaction success (for error recovery)
nft_id = xrpl.verify_transaction_success("ABC123...")
# Returns: "000B0000..." or None

# Find NFT by URI (for duplicate detection)
nft = xrpl.find_nft_by_uri("ipfs://QmXXX...")
# Returns: {
#     "NFTokenID": "000B0000...",
#     "URI": "ipfs://QmXXX...",
#     "Issuer": "rXXXX...",
#     ...
# } or None
```

#### Transaction Flags

| Flag | Value | Description |
|------|-------|-------------|
| `tfTransferable` | 8 | NFT can be transferred to others |
| `tfBurnable` | 1 | NFT can be burned by owner |
| `tfOnlyXRP` | 2 | Only accept XRP offers |

### YouTube Service

**File:** `src/services/youtube_service.py`

**Purpose:** YouTube Data API integration.

#### Features

- Fetch all videos from channel
- Get video details
- Fetch video list by IDs
- Auto-categorize videos

#### Key Methods

```python
from src.services import create_youtube_service

youtube = create_youtube_service()

# Fetch all videos from channel
videos = youtube.fetch_all_videos_from_channel(
    channel_id="UCXXXX",
    max_results=50
)
# Returns: [{video_id, title, description, published_at, thumbnail_url}, ...]

# Get video details
details = youtube.get_video_details(video_id="abc123")
# Returns: {video_id, title, description, published_at, thumbnail_url, ...}

# Categorize video
category = youtube.categorize_video("AI and ChatGPT Tutorial", "Learn about AI...")
# Returns: "AI & Technology"
```

#### Video Categories

- **AI & Technology** - AI, ChatGPT, Grok, LLM, technology keywords
- **Automotive** - Car, dealer, vehicle keywords
- **Sports** - NFL, football, sports keywords
- **Business** - Business, entrepreneur, marketing keywords
- **General** - Default category

### YouTube Auth Service

**File:** `src/services/youtube_auth.py`

**Purpose:** OAuth token management for YouTube API.

#### Features

- Generate OAuth tokens
- Refresh expired tokens
- Store tokens in environment

#### Key Methods

```python
from src.services.youtube_auth import get_oauth_token, refresh_oauth_token

# Get OAuth token (opens browser)
token = get_oauth_token()

# Refresh expired token
new_token = refresh_oauth_token(client_secrets_file="client_secrets.json")
```

---

## Backend Scripts

### mint_nfts.py - Main NFT Management Script

**Purpose:** Primary script for NFT minting and management.

#### Commands

**1. Sync Videos to MongoDB**

```bash
python mint_nfts.py sync [json_file]

# Examples:
python mint_nfts.py sync                    # Uses complete_videos.json
python mint_nfts.py sync my_videos.json     # Uses custom file
```

**2. Mint NFTs**

```bash
python mint_nfts.py mint <count>

# Examples:
python mint_nfts.py mint 1      # Mint 1 NFT (test)
python mint_nfts.py mint 10     # Mint 10 NFTs
python mint_nfts.py mint 100    # Mint 100 NFTs
```

**Mainnet Safety:** On mainnet, requires typing "CONFIRM" before minting.

**3. Check Status**

```bash
python mint_nfts.py status
```

**Output:**
```
📊 YouTube NFT Minting Status
======================================================================
📺 Total Videos: 100
✅ Minted NFTs: 50
⏳ Unminted: 45
⏭️  Skipped: 5

📂 Category Breakdown:
   AI & Technology: 25 videos
   Automotive: 15 videos
   Sports: 10 videos
```

**4. Sync NFTs from Blockchain**

```bash
python mint_nfts.py sync-nfts
```

Reconciles NFTs on XRPL blockchain with MongoDB database.

#### Minting Process Flow

```
1. Get unminted video from MongoDB
2. Upload thumbnail to IPFS (Pinata)
   ↓ Returns: image_ipfs_hash
3. Create OpenSea metadata with IPFS image
4. Upload metadata to IPFS
   ↓ Returns: metadata_ipfs_hash
5. Check for duplicate CID on blockchain
   ↓ If duplicate: prompt user
6. Mint NFT on XRPL with IPFS URI
   ↓ Returns: nft_id, tx_hash
7. Save NFT to MongoDB
8. Log to minting_log
```

#### Error Handling

- **Network failure during minting**: Verifies transaction on-chain, recovers NFT ID
- **Duplicate CID detected**: Prompts user to skip, continue, or abort
- **Insufficient XRP**: Shows clear error message
- **MongoDB connection lost**: Retries connection
- **IPFS upload failed**: Falls back to YouTube URL (with warning)

### query_nfts.py - NFT Query Tool

**Purpose:** Query and view NFT data from MongoDB.

#### Commands

**1. List NFTs**

```bash
python query_nfts.py list <limit>

# Examples:
python query_nfts.py list 10    # List 10 most recent NFTs
python query_nfts.py list 100   # List 100 NFTs
```

**2. Query by Video ID**

```bash
python query_nfts.py video <video_id>

# Example:
python query_nfts.py video dQw4w9WgXcQ
```

**Output:**
```
🔍 Querying NFT for video: dQw4w9WgXcQ
======================================================================
NFT Token ID: 000B0000E3ECD0E6E0D52E7FD3EF3F89B...
TX Hash: ABC123DEF456...
IPFS URI: ipfs://QmYjtig7VJQ6...
Image: ipfs://QmXXXXXX...
Account: rXXXXXXXXXX...
```

**3. Query by NFT ID**

```bash
python query_nfts.py nft <nft_token_id>

# Example:
python query_nfts.py nft 000B0000E3ECD0E6E0D52E7FD3EF3F89B...
```

**4. Verify NFT Fields**

```bash
python query_nfts.py verify
```

Checks that all required fields are present in NFT records.

### update_youtube_descriptions.py - Description Updater

**Purpose:** Update YouTube video descriptions with BCA validation links.

#### Commands

**1. Check Status (No Changes)**

```bash
python update_youtube_descriptions.py --check-only
```

Shows which videos need updates without making changes.

**2. Dry Run (Simulate)**

```bash
python update_youtube_descriptions.py --dry-run
python update_youtube_descriptions.py --dry-run --limit 5
```

Simulates updates without modifying YouTube descriptions.

**3. Execute Updates**

```bash
python update_youtube_descriptions.py --execute
python update_youtube_descriptions.py --execute --limit 10
python update_youtube_descriptions.py --execute --skip 100 --limit 50
```

Actually updates video descriptions.

**4. Rate Limiting**

```bash
python update_youtube_descriptions.py --execute --rate-limit 1.5
```

Controls delay between API requests (default: 1.0 second).

#### BCA Validation Text Format

```
This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger — proof it's the genuine article from the official series run. BCA: https://bca.jimflint.com/verify/{NFTokenId}

[Original video description content...]

#hashtags #here
```

#### Features

- ✅ Verifies NFT exists before updating
- ✅ Syncs latest description from YouTube API
- ✅ Detects existing BCA text
- ✅ Validates NFToken ID matches
- ✅ Updates or adds BCA text at top of description
- ✅ Validates 5000 character limit
- ✅ Automatic OAuth token refresh
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting to avoid quota issues
- ✅ Progress tracking with ETA
- ✅ Detailed timing statistics

### verify_network.py - Network Verification

**Purpose:** Verify network configuration and prevent mistakes.

#### Usage

```bash
python verify_network.py
```

#### What It Checks

1. **Network Detection**
   - Detects testnet vs mainnet from `XRPL_NODE_URL`
   - Shows clear warning for mainnet

2. **Wallet Configuration**
   - Verifies wallet secret is set
   - Checks wallet balance
   - Shows wallet address

3. **Database Configuration**
   - Verifies MongoDB connection
   - Checks database name consistency
   - Warns if testnet database with mainnet node

4. **Consistency Checks**
   - Prevents testnet/mainnet mix-ups
   - Validates all required environment variables

#### Example Output

**Testnet:**
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

**Mainnet:**
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

### test_setup.py - Service Testing

**Purpose:** Verify all services are configured correctly.

#### Usage

```bash
python test_setup.py
```

#### Tests Performed

1. **Environment Variables** - Checks all required variables
2. **MongoDB Connection** - Tests database connectivity
3. **Pinata IPFS** - Tests IPFS upload
4. **XRPL Connection** - Tests blockchain connectivity
5. **YouTube API** - Tests API access
6. **Data Flow** - Tests save/retrieve operations

### get_youtube_oauth_token.py - OAuth Generator

**Purpose:** Generate YouTube OAuth tokens for description updates.

#### Usage

```bash
python get_youtube_oauth_token.py
```

#### Process

1. Opens browser for Google authentication
2. Requests YouTube video management permissions
3. Saves access token to `.env` file

**Note:** OAuth tokens expire after ~1 hour for security.

---

## NFT Metadata Structure

### On-Chain MEMO (Compact Format)

Stored in XRPL transaction memo - optimized for blockchain storage:

```json
{
  "id": "dQw4w9WgXcQ",
  "title": "Rick Astley - Never Gonna Give You Up",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "thumb": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
  "channel": "JimFlintLSG",
  "date": "2025-10-27",
  "category": "AI & Technology"
}
```

### Full Metadata (IPFS Storage)

OpenSea-compatible metadata stored on IPFS:

```json
{
  "name": "Rick Astley - Never Gonna Give You Up",
  "description": "YouTube video from All-Time High channel - permanently recorded on XRP Ledger",
  "image": "ipfs://QmYYYYYYYYYYYYYYYYYYYYYYYYY",
  "external_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "attributes": [
    {"trait_type": "contextType", "value": "YouTube_NFT"},
    {"trait_type": "videoId", "value": "dQw4w9WgXcQ"},
    {"trait_type": "channel", "value": "JimFlintLSG"},
    {"trait_type": "category", "value": "AI & Technology"},
    {"trait_type": "publishedDate", "value": "2025-10-27"},
    {"trait_type": "accountXRPL", "value": "rXXXXXXXXXXXXXXXXXXX"}
  ]
}
```

### NFT URI Structure

```
ipfs://QmXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
```

Points to the full metadata JSON on IPFS.

---

## Database Schema

### Videos Collection

```javascript
{
  _id: ObjectId("..."),
  video_id: "dQw4w9WgXcQ",           // Unique, indexed
  title: "Rick Astley - Never Gonna Give You Up",
  description: "The official video...",
  published_at: "2025-10-27",
  thumbnail_url: "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
  video_url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  channel_title: "JimFlintLSG",
  category: "AI & Technology",        // Auto-classified
  skip_minting: false,                // Optional: skip flag
  skip_reason: "",                    // Optional: why skipped
  skipped_at: null,                   // Optional: when skipped
  created_at: ISODate("2025-10-27T10:00:00Z"),
  updated_at: ISODate("2025-10-27T10:00:00Z")
}
```

### NFTs Collection

```javascript
{
  _id: ObjectId("..."),
  nft_id: "000B0000E3ECD0E6E0D52E7FD3EF3F89B...",  // XRPL NFT ID (unique)
  video_id: "dQw4w9WgXcQ",                         // Links to video
  tx_hash: "ABC123DEF456789...",                   // XRPL transaction
  uri: "ipfs://QmXXXXXXXXXXXXXXXXXXXXXXXXX",      // Metadata URI
  metadata_ipfs_hash: "QmXXXXXXXXXXXXXXXXXXXXX",  // Metadata CID
  image_ipfs_hash: "QmYYYYYYYYYYYYYYYYYYYYYYYY",  // Image CID
  taxon: 123456,                                   // NFT taxon
  account: "rXXXXXXXXXXXXXXXXXXXXXXXXXX",         // Minting wallet
  minted_at: ISODate("2025-10-27T11:00:00Z"),
  network: "testnet",                              // testnet or mainnet
  metadata: {                                      // Full OpenSea metadata
    "name": "...",
    "description": "...",
    "image": "ipfs://...",
    "attributes": [...]
  },
  memo_data: {                                     // Compact on-chain memo
    "id": "dQw4w9WgXcQ",
    "title": "...",
    "channel": "..."
  }
}
```

### Minting Log Collection

```javascript
{
  _id: ObjectId("..."),
  video_id: "dQw4w9WgXcQ",
  nft_id: "000B0000...",
  action: "minted",                    // minted, failed, skipped
  status: "success",                   // success, error
  error_message: null,                 // If failed
  timestamp: ISODate("2025-10-27T11:00:00Z")
}
```

### Database Indexes

```javascript
// Videos collection
db.videos.createIndex({"video_id": 1}, {unique: true})

// NFTs collection
db.nfts.createIndex({"nft_id": 1}, {unique: true})
db.nfts.createIndex({"video_id": 1})
db.nfts.createIndex({"metadata_ipfs_hash": 1})

// Minting log
db.minting_log.createIndex({"video_id": 1})
db.minting_log.createIndex({"timestamp": -1})
```

---

## Testing Guide

### Pre-Testing Checklist

- [ ] All environment variables configured
- [ ] MongoDB connection tested
- [ ] Pinata IPFS access verified
- [ ] XRPL wallet funded (testnet: use faucet)
- [ ] YouTube API key active

### Test Suite

#### 1. Test All Services

```bash
python test_setup.py
```

**Expected Result:** All tests pass with ✅

#### 2. Sync Test Videos

```bash
python mint_nfts.py sync complete_videos.json
```

**Expected Result:** Videos imported to MongoDB

#### 3. Check Status

```bash
python mint_nfts.py status
```

**Expected Result:** Shows video counts and categories

#### 4. Test Mint (Single NFT)

```bash
python mint_nfts.py mint 1
```

**Expected Result:**
```
[1/1] Minting: Video Title
   📸 Uploading thumbnail to IPFS...
   ✅ Thumbnail: QmXXX...
   📦 Uploading metadata to IPFS...
   ✅ Metadata: QmYYY...
   ⛓️  Minting on XRPL...
   ✅ NFT Minted!
      NFT ID: 000B0000...
      TX Hash: ABC123...
   💾 Saving to MongoDB...
   ✅ Saved to MongoDB
```

#### 5. Verify NFT Fields

```bash
python query_nfts.py verify
```

**Expected Result:** All 12 required fields present

#### 6. Query NFT

```bash
python query_nfts.py list 5
```

**Expected Result:** Lists NFTs with details

#### 7. Test Blockchain Sync

```bash
python mint_nfts.py sync-nfts
```

**Expected Result:** Shows sync analytics, matches found

#### 8. Test Description Update (Dry Run)

```bash
python update_youtube_descriptions.py --dry-run --limit 1
```

**Expected Result:** Shows what would be updated

### Manual Verification

#### Verify on XRPL Explorer

**Testnet:**
1. Visit: https://testnet.xrpl.org
2. Search wallet address
3. Check "NFTs" tab
4. Verify NFT appears

**Mainnet:**
1. Visit: https://livenet.xrpl.org
2. Search wallet address
3. Check "NFTs" tab
4. Verify NFT appears

#### Verify on Pinata

1. Login: https://app.pinata.cloud
2. Go to "Files"
3. Verify uploads:
   - `thumbnail-{video_id}.jpg`
   - `metadata-{video_id}`

#### Verify in MongoDB

Using MongoDB Compass or shell:

```javascript
// Check videos
db.videos.find({video_id: "dQw4w9WgXcQ"})

// Check NFTs
db.nfts.find({video_id: "dQw4w9WgXcQ"})

// Check logs
db.minting_log.find({video_id: "dQw4w9WgXcQ"})
```

---

## Deployment

### Testnet Deployment (Development)

#### Setup

```bash
# 1. Configure testnet environment
cp .env.example .env
nano .env  # Edit with testnet credentials

# 2. Create testnet wallet
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"

# 3. Fund wallet from faucet
# Visit: https://faucet.altnet.rippletest.net
# Enter wallet address

# 4. Verify network
python verify_network.py

# 5. Test all services
python test_setup.py
```

#### Development Workflow

```bash
# 1. Sync videos
python mint_nfts.py sync complete_videos.json

# 2. Check status
python mint_nfts.py status

# 3. Mint test NFT
python mint_nfts.py mint 1

# 4. Verify NFT
python query_nfts.py verify

# 5. Mint batch
python mint_nfts.py mint 10
```

### Mainnet Deployment (Production)

#### Pre-Deployment Checklist

- [ ] **Tested thoroughly on testnet**
- [ ] **Mainnet wallet created and backed up**
- [ ] **Wallet funded with 15-20 XRP**
- [ ] **Production MongoDB configured**
- [ ] **Production Pinata account ready**
- [ ] **All documentation reviewed**
- [ ] **Team trained on procedures**

#### Step-by-Step Deployment

**Step 1: Create Mainnet Wallet**

```bash
# Generate wallet
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"

# CRITICAL: Backup secret in secure location!
# Never commit to git or share
```

**Step 2: Fund Wallet**

- Send **15-20 XRP** to wallet address
- From exchange (Coinbase, Kraken, Binance)
- Verify at: https://livenet.xrpl.org

**Step 3: Configure Environment**

```bash
# Backup current config
cp .env .env.testnet.backup

# Copy mainnet template
cp .env.mainnet.example .env

# Edit with mainnet credentials
nano .env
```

**Required Changes:**
```bash
XRPL_NODE_URL=https://xrplcluster.com/
XRPL_SECRET=sYourMainnetSecret
MONGODB_URI=mongodb+srv://production...
MONGODB_DB=bcaxrplprod
NETWORK=mainnet
```

**Step 4: Verify Configuration**

```bash
python verify_network.py
```

**Expected Output:**
```
🔴 Network: MAINNET (PRODUCTION)
   ⚠️  Real XRP will be used for transactions

✅ Configuration Valid
```

**Step 5: Test Single Mint**

```bash
python mint_nfts.py mint 1
```

**You will see:**
```
🔴 MAINNET MODE DETECTED
======================================================================
⚠️  MAINNET OPERATION WARNING
======================================================================
Type 'CONFIRM' to proceed:
```

Type `CONFIRM` and press Enter.

**Step 6: Verify Transaction**

1. Visit: https://livenet.xrpl.org
2. Search your wallet address
3. Verify NFT appears in "NFTs" tab

**Step 7: Production Minting**

```bash
# Mint batch
python mint_nfts.py mint 100

# Monitor progress
python mint_nfts.py status

# Continue minting
python mint_nfts.py mint 100
```

#### Cost Estimation

| Component | Amount | Notes |
|-----------|--------|-------|
| Account Reserve | 10 XRP | Minimum to activate account |
| Transaction Fees | 5-10 XRP | For 500-5000 NFTs |
| **Total Recommended** | **15-20 XRP** | Safe buffer |

**Per-NFT Cost:**
- NFTokenMint: ~0.00001 XRP
- Average: ~0.00002 XRP per NFT

**Budget Examples:**
- 100 NFTs: ~0.002 XRP (~$0.001 at $0.50/XRP)
- 500 NFTs: ~0.01 XRP (~$0.005)
- 1,000 NFTs: ~0.02 XRP (~$0.01)
- 5,000 NFTs: ~0.1 XRP (~$0.05)

#### Monitoring & Maintenance

**Daily Checks:**

```bash
# Check wallet balance
python3 -c "from src.services import create_xrpl_service; xrpl = create_xrpl_service(); info = xrpl.get_account_info(); print(f'Balance: {int(info[\"account_data\"][\"Balance\"])/1000000} XRP')"

# Check minting status
python mint_nfts.py status

# Query recent NFTs
python query_nfts.py list 10
```

**Weekly Checks:**
- MongoDB database backups
- Pinata storage usage
- YouTube API quota usage

#### Rollback Plan

If issues occur on mainnet:

```bash
# 1. Stop all operations immediately

# 2. Switch back to testnet
cp .env.testnet.backup .env

# 3. Verify network
python verify_network.py

# 4. Investigate issue
python query_nfts.py list 100

# 5. Check XRPL explorer
# Visit: https://livenet.xrpl.org
```

**Note:** Mainnet transactions are **permanent** and **cannot be reversed**.

#### Network Switching

**To Testnet:**
```bash
# In .env
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234/
XRPL_SECRET=sTestnetSecret
MONGODB_DB=bcaxrpldev
```

**To Mainnet:**
```bash
# In .env
XRPL_NODE_URL=https://xrplcluster.com/
XRPL_SECRET=sMainnetSecret
MONGODB_DB=bcaxrplprod
```

---

## YouTube Description Updater

### Overview

Automatically updates YouTube video descriptions to include BCA (Blockchain Content Authenticator) validation information after NFTs are minted.

### Features

- ✅ Queries MongoDB for all minted NFTs
- ✅ **Verifies NFT exists before attempting updates** (CRITICAL)
- ✅ Syncs latest description from YouTube API
- ✅ Checks current descriptions for existing BCA text
- ✅ Validates NFToken ID matches
- ✅ Updates or adds BCA text at top of description
- ✅ Validates 5000 character limit
- ✅ Dry-run mode for safe testing
- ✅ Automatic OAuth token refresh
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting for quota management
- ✅ Progress tracking with ETA

### Quick Start

#### 1. Generate OAuth Token

```bash
python get_youtube_oauth_token.py
```

Browser opens → Sign in → Authorize → Token saved to `.env`

#### 2. Check Status

```bash
python update_youtube_descriptions.py --check-only
```

#### 3. Test with Dry Run

```bash
python update_youtube_descriptions.py --dry-run --limit 1
```

#### 4. Execute Updates

```bash
python update_youtube_descriptions.py --execute
```

### Command Reference

| Command | Purpose |
|---------|---------|
| `--check-only` | View status without changes |
| `--dry-run` | Simulate updates |
| `--execute` | Actually update descriptions |
| `--limit N` | Process only N videos |
| `--skip N` | Skip first N videos |
| `--rate-limit X` | Delay X seconds between requests |
| `--oauth-token TOKEN` | Use specific OAuth token |

### Usage Examples

**Check which videos need updates:**
```bash
python update_youtube_descriptions.py --check-only
```

**Test with single video:**
```bash
python update_youtube_descriptions.py --dry-run --limit 1
```

**Update first 50 videos:**
```bash
python update_youtube_descriptions.py --execute --limit 50
```

**Resume from video 200:**
```bash
python update_youtube_descriptions.py --execute --skip 200
```

**Conservative rate limiting:**
```bash
python update_youtube_descriptions.py --execute --rate-limit 1.5
```

### BCA Text Format

```
This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger — proof it's the genuine article from the official series run. BCA: https://bca.jimflint.com/verify/{NFTokenId}

[Original description content...]

#hashtags #here
```

### Features in Detail

#### NFT Verification

```python
# BEFORE attempting update, verify NFT exists
nft_exists, nft_id, error_msg = verify_nft_exists(video_id)

if not nft_exists:
    logger.warning(f"⚠️  SKIPPED: {error_msg}")
    continue
```

**Checks:**
1. NFT record exists in MongoDB
2. NFT has valid nft_id field
3. nft_id is correct format

#### Automatic Token Refresh

```
Token expired, refreshing...
✅ Token refreshed successfully
```

No manual intervention needed for long-running batches.

#### Progress Tracking

```
[1/500] Progress: 0.2% | ETA: 45.2 min
Processing video: dQw4w9WgXcQ
  Status: BCA text not found
  Updated: Added at top

[2/500] Progress: 0.4% | ETA: 44.8 min
...
```

#### Performance Statistics

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

### Output Files

1. **youtube_description_updates.log**
   - Real-time logging of all operations
   - Error tracking
   - Detailed progress

2. **youtube_update_results_YYYYMMDD_HHMMSS.log**
   - Comprehensive report
   - Status of each video
   - Actions taken

### API Quota Considerations

YouTube Data API v3 quota limits:
- **Default quota:** 10,000 units per day
- **Update operation:** ~50 units per video
- **Maximum:** ~200 video updates per day

**Solution:** Use `--skip` to resume after quota reset.

Example:
```bash
# Day 1: Updated 198 videos
python update_youtube_descriptions.py --execute

# Day 2: Resume from video 199
python update_youtube_descriptions.py --execute --skip 198
```

---

## NFT Blockchain Sync

### Overview

The `sync-nfts` command reconciles NFTs that exist on the XRPL blockchain with your MongoDB database.

### Use Cases

- NFTs minted but database wasn't updated (network failures)
- Database accidentally cleared or corrupted
- Migrating from another system
- Auditing blockchain vs database consistency

### Quick Start

```bash
python mint_nfts.py sync-nfts
```

### Process Flow

```
1. Fetch all NFTs from XRPL blockchain
2. Fetch all NFTs from MongoDB database
3. Compare and generate analytics
4. Display missing/orphaned NFTs
5. Prompt user for action
6. Update database based on selection
```

### Example Output

```
======================================================================
🔄 NFT Blockchain → MongoDB Sync
======================================================================

📡 Step 1: Fetching NFTs from XRPL blockchain...
   ✅ Found 580 NFTs on blockchain

💾 Step 2: Fetching NFTs from MongoDB...
   ✅ Found 579 NFTs in database

🔍 Step 3: Comparing blockchain vs database...

======================================================================
📊 SYNC ANALYTICS
======================================================================
📡 NFTs on Blockchain:     580
💾 NFTs in Database:       579
✅ Matched (in sync):      579
⚠️  Missing in DB:         1
======================================================================

⚠️  1 NFT(s) on blockchain but NOT in database:
======================================================================

1. NFT ID: 000800003C85C18E326460579DA9BDCE...
   URI: ipfs://QmYjtig7VJQ6XsnUjqqJvj7QaMcCA...
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

### User Options

**Option 1: Update ALL Missing NFTs**
- Automatically adds all missing NFTs to database
- Links to associated videos if found

**Option 2: Select Specific NFTs**
- Choose which NFTs to sync
- Interactive selection

**Option 3: Show Detailed Info**
- View full details for each missing NFT
- Helpful for investigation

**Option 4: Export to File**
- Saves missing NFT list to JSON
- Useful for audit trail

**Option 5: Skip Update (View Only)**
- No changes made
- Just shows analytics

### Video Association

The sync process tries to find associated YouTube videos:

1. Extracts CID from NFT URI (`ipfs://QmXXX...`)
2. Searches `videos` collection for matching `metadata_ipfs_hash`
3. If found: Links NFT to video
4. If not found: Creates placeholder video ID (`unknown_000800003C85C18E...`)

### Synced NFT Fields

```javascript
{
  nft_id: "000800003C85C18E...",
  video_id: "dQw4w9WgXcQ",              // or "unknown_..." if not found
  tx_hash: "RECOVERED_FROM_BLOCKCHAIN",  // Special marker
  uri: "ipfs://QmYjtig7VJQ6...",
  metadata_ipfs_hash: "QmYjtig7VJQ6...",
  image_ipfs_hash: "",                   // Unknown
  taxon: 0,
  account: "rBCA9v3tQMLSnRdEFqN5...",
  minted_at: ISODate("2025-11-09..."),   // Current time
  metadata: {},                          // Empty (needs IPFS fetch)
  memo_data: "",
  network: "mainnet",
  synced_from_blockchain: true,          // Flag
  sync_date: ISODate("2025-11-09...")
}
```

### Understanding Analytics

**Matched NFTs:**
```
✅ Matched (in sync): 579
```
These NFTs exist on both blockchain and database. No action needed.

**Missing in Database:**
```
⚠️  Missing in DB: 1
```
NFT exists on blockchain but not in MongoDB. Should be synced.

**Extra in Database (Orphaned):**
```
🔍 Extra in DB (orphaned): 5
```
NFT in database but not on blockchain. Possible causes:
- NFT was burned
- NFT was transferred
- Wrong wallet checked

### Best Practices

**Before Syncing:**
1. Backup database
2. Verify network configuration
3. Check wallet address
4. Use option 5 (view only) first

**During Syncing:**
1. Review missing NFTs
2. Use selective update if unsure
3. Check video associations

**After Syncing:**
1. Verify counts with `python mint_nfts.py status`
2. Check synced NFTs
3. Update placeholders if possible

---

## Duplicate Detection

### Overview

Prevents duplicate NFT creation when the same metadata is uploaded to IPFS (resulting in same CID).

### How It Works

#### Level 1: Pre-Minting Batch Check

Before starting batch minting:

```
🔍 Pre-minting duplicate check...
🔍 Fetching existing NFTs from XRPL to check for duplicates...
   Found 47 existing NFTs on XRPL
   Indexed 47 unique CIDs
```

Builds a map of all existing CIDs for fast lookup.

#### Level 2: Runtime Check Before Each Mint

Before minting each video:

```
🔍 Checking for duplicate CID on XRPL...
```

If duplicate found:

```
⚠️  DUPLICATE DETECTED!
   CID: QmYjtig7VJQ6XsnUjqqJvj7QaMcCAwtrgNdahSiFofrE7o
   Existing NFT ID: 000800003C85C18E326460579DA9BDCE...
   This CID is already minted on XRPL
   Found in database for video: xyz789

❓ What would you like to do?
   1. Skip this video (will not retry)
   2. Continue anyway (will attempt to mint duplicate)
   3. Abort minting process

Enter choice (1/2/3):
```

### User Options

**Option 1: Skip**
- Marks video with `skip_minting: true` in MongoDB
- Records skip reason
- Video won't appear in unminted list

**Option 2: Continue Anyway**
- Proceeds with minting
- Creates duplicate NFT (XRPL allows this)
- Useful if intentional

**Option 3: Abort**
- Stops entire minting process
- No data changed

### Transaction Verification

When minting appears to fail but transaction was submitted:

```
❌ Minting appears to have failed: Connection timeout

🔍 Transaction was submitted, verifying on-chain status...
🔍 Verifying transaction A1B2C3D4...
✅ Transaction actually SUCCEEDED on-chain!
   NFT ID: 000800003C85C18E326460579DA9BDCE...
   TX Hash: A1B2C3D4E5F6...

💾 Saving to MongoDB...
✅ Saved to MongoDB
```

**Process:**
1. Checks if transaction hash exists
2. Queries XRPL for transaction details
3. Verifies result is `tesSUCCESS`
4. Extracts NFT ID from transaction
5. Updates MongoDB correctly

### Recovery from Previous Attempts

If NFT was minted before but not saved:

```
❌ Minting appears to have failed: tecDUPLICATE

🔍 Checking if NFT already exists with this URI...
✅ Found existing NFT with matching URI!
   NFT ID: 000800003C85C18E326460579DA9BDCE...
   This was likely minted in a previous attempt

💾 Saving to MongoDB...
✅ Saved to MongoDB
```

### Managing Skipped Videos

**View skipped videos:**
```python
from src.services import create_mongodb_service

mongodb = create_mongodb_service()
skipped = list(mongodb.videos.find({"skip_minting": True}))

for video in skipped:
    print(f"{video['video_id']}: {video.get('skip_reason', 'No reason')}")
```

**Unskip a video:**
```python
mongodb.unmark_video_skipped("abc123")
```

**Unskip all videos:**
```python
result = mongodb.videos.update_many(
    {"skip_minting": True},
    {"$unset": {"skip_minting": "", "skip_reason": "", "skipped_at": ""}}
)
print(f"Unskipped {result.modified_count} videos")
```

---

## API Quota Management

### YouTube API Quota Limits

- **Default quota:** 10,000 units per day
- **Quota reset:** Midnight Pacific Time (PT) daily
- **Video update cost:** ~50 units per video
- **Maximum:** ~200 video updates per day

### Quota Cost Breakdown

| Operation | Cost | Videos per 10k quota |
|-----------|------|---------------------|
| Read video details | 1 unit | 10,000 |
| Update video description | 50 units | 200 |
| List videos | 1 unit | 10,000 |

### When Quota is Exhausted

**Symptoms:**
```
[198/580] Processing video: abc123...
  ✅ Successfully updated

[199/580] Processing video: def456...
  ❌ 403 Forbidden Error - Likely API quota exhausted
  ⚠️  Quota failure #1

...

🛑 STOPPING: 5 consecutive quota failures detected
   YouTube API quota appears to be exhausted
   Successfully updated 198 videos before quota exhaustion
```

### Solutions

#### Solution 1: Wait for Quota Reset (Free)

**Best for:** Most users

**Steps:**
1. Note how many videos were updated (e.g., 198)
2. Wait until midnight Pacific Time
3. Resume using `--skip`:

```bash
# Skip first 198 videos, continue from 199
python update_youtube_descriptions.py --execute --skip 198 --rate-limit 1.5
```

**Why use `--skip`?**
- ✅ Saves quota
- ✅ Starts exactly where you left off
- ✅ Faster processing

**Multi-Day Workflow:**
- **Day 1**: Updated videos 1-198
- **Day 2**: `--skip 198` → Update 199-388
- **Day 3**: `--skip 388` → Update 389-580

#### Solution 2: Request Quota Increase

**Best for:** Channels with 500+ videos

**Steps:**

1. Go to: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
2. Click on "Queries per day" quota
3. Click "EDIT QUOTAS"
4. Enter new quota (e.g., 50,000 for ~1,000 videos/day)
5. Fill out justification form
6. Submit request

**Justification Example:**
```
Project Name: YouTube NFT Content Verification

Use Case: We are minting NFTs for YouTube video content verification
and need to update video descriptions with blockchain validation links.

Current Limitation: We have 580 videos to update but can only update
200 per day with the default quota.

Requested Quota: 50,000 units/day (allows ~1,000 video updates)

Business Impact: This is a one-time bulk update for adding blockchain
validation to our video library.
```

**Approval Time:** Usually 1-2 business days

#### Solution 3: Batch Processing

**Best for:** No urgency

**Strategy:**
```bash
# Day 1: Update first 190 videos
python update_youtube_descriptions.py --execute --limit 190 --rate-limit 1.5

# Day 2: Skip first 190, update next 190 (191-380)
python update_youtube_descriptions.py --execute --skip 190 --limit 190 --rate-limit 1.5

# Day 3: Skip first 380, update remaining (381-580)
python update_youtube_descriptions.py --execute --skip 380 --rate-limit 1.5
```

### Checking Quota Usage

**Via Google Cloud Console:**
1. Go to: https://console.cloud.google.com/apis/dashboard
2. Select YouTube Data API v3
3. Click "Quotas" tab
4. View current usage and limits

### Best Practices

1. **Use `--check-only` first** (minimal quota usage)
2. **Use `--dry-run` to verify** before executing
3. **Process in batches** with `--limit`
4. **Use rate limiting** with `--rate-limit`
5. **Monitor quota** in Google Cloud Console

---

## Troubleshooting

### Common Issues

#### Environment Variables

**Issue:** "MONGODB_URI environment variable is required"

**Solution:**
```bash
# Check .env file exists
ls -la .env

# Add required variable
nano .env
# Add: MONGODB_URI=mongodb+srv://...
```

#### MongoDB Connection

**Issue:** "Failed to connect to MongoDB"

**Solutions:**
1. Check MongoDB URI format
2. Verify database user credentials
3. Whitelist IP address in MongoDB Atlas
4. Test connection: `python test_setup.py`

#### Pinata IPFS

**Issue:** "Failed to upload image to Pinata"

**Solutions:**
1. Verify `PINATA_JWT_SECRET` is correct
2. Check Pinata account status
3. Verify account has available storage
4. Test: `python test_setup.py`

**Note:** Script falls back to YouTube URL if IPFS upload fails (with warning)

#### XRPL Connection

**Issue:** "Failed to connect to XRPL"

**Solutions:**
1. Check `XRPL_NODE_URL` format
2. Try alternative node:
   ```bash
   # Testnet
   XRPL_NODE_URL=https://s.altnet.rippletest.net:51234/

   # Mainnet
   XRPL_NODE_URL=https://s2.ripple.com:51234/
   ```
3. Verify internet connection
4. Check XRPL status: https://status.xrpl.org

#### Insufficient XRP

**Issue:** "Insufficient XRP balance"

**Testnet:**
```bash
# Visit faucet
# https://faucet.altnet.rippletest.net
# Enter wallet address
```

**Mainnet:**
```bash
# Fund wallet from exchange
# Minimum 10 XRP for account activation
# 15-20 XRP recommended for operations
```

#### NFT Already Exists

**Issue:** "NFT already exists for video_id"

**Explanation:** Video already minted

**Check:**
```bash
python query_nfts.py video <video_id>
python mint_nfts.py status
```

#### YouTube API Issues

**Issue:** "OAuth token required"

**Solution:**
```bash
python get_youtube_oauth_token.py
```

**Issue:** "Token has expired"

**Solution:**
```bash
# The script auto-refreshes tokens
# If manual refresh needed:
python get_youtube_oauth_token.py
```

**Issue:** "403 Forbidden"

**Possible causes:**
1. Quota exhausted (wait for reset)
2. OAuth scope insufficient (regenerate token)
3. API not enabled (enable in Google Cloud Console)

**Issue:** "Description exceeds 5000 characters"

**Solution:** Video description is too long. The script automatically skips these videos.

#### Network Detection

**Issue:** Wrong network detected

**Solution:**
```bash
# Verify configuration
python verify_network.py

# Check XRPL_NODE_URL in .env
nano .env
```

#### Duplicate Detection

**Issue:** "Duplicate CID detected" but it's a false positive

**Solutions:**
1. Choose "Continue anyway" (option 2)
2. Verify video metadata is truly unique
3. Check if NFT already minted for different video

### Diagnostic Commands

```bash
# Test all services
python test_setup.py

# Verify network configuration
python verify_network.py

# Check NFT counts
python mint_nfts.py status

# List recent NFTs
python query_nfts.py list 10

# Check logs
tail -f youtube_description_updates.log
```

### Debug Logging

For detailed debugging, add to scripts:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## Security Best Practices

### Wallet Security

1. **Never share wallet secret**
   - Secret gives complete control of wallet
   - Anyone with secret can steal all XRP and NFTs

2. **Backup wallet secret securely**
   - Store offline in multiple secure locations
   - Use password manager or hardware wallet
   - Never store in cloud storage or email

3. **Use dedicated wallets**
   - Separate wallet for minting (not personal holdings)
   - Limits exposure if compromised

4. **Monitor wallet activity**
   - Check regularly at XRPL explorer
   - Set up alerts for unexpected transactions
   - Review transaction history

### Environment Security

1. **Never commit secrets to git**
   ```bash
   # Verify .env is in .gitignore
   cat .gitignore | grep .env

   # Check git history for secrets
   git log --all -p | grep -i "secret\|password\|key"
   ```

2. **Use environment variables only**
   - Never hardcode secrets in scripts
   - Store in `.env` file
   - Load with `python-dotenv`

3. **Secure `.env` file permissions**
   ```bash
   chmod 600 .env  # Owner read/write only
   ```

### API Key Security

1. **Restrict API key usage**
   - YouTube API: Restrict to specific app
   - Pinata: Use minimal required permissions
   - MongoDB: Use role-based access control

2. **Rotate keys regularly**
   - Change API keys periodically
   - Revoke unused keys
   - Monitor API usage

### Database Security

1. **Use strong passwords**
   - 16+ characters
   - Mix of letters, numbers, symbols
   - Unique for each service

2. **Enable backups**
   - MongoDB Atlas: Auto-backup enabled
   - Export important data regularly
   - Test restore procedures

3. **Restrict network access**
   - Whitelist specific IP addresses
   - Use VPN for remote access
   - Enable SSL/TLS connections

### Production Security Checklist

- [ ] Wallet secret backed up offline
- [ ] `.env` file NOT in git repository
- [ ] Strong passwords for all services
- [ ] API keys restricted to app only
- [ ] MongoDB network access restricted
- [ ] Database backups enabled
- [ ] Regular security audits scheduled
- [ ] Team trained on security procedures

### Incident Response

**If wallet secret is compromised:**

1. **Immediate Actions:**
   - Transfer all XRP to new wallet
   - Transfer all NFTs to new wallet
   - Revoke access to old wallet

2. **Investigation:**
   - Review transaction history
   - Identify unauthorized transactions
   - Determine how compromise occurred

3. **Prevention:**
   - Generate new wallet
   - Update all configurations
   - Implement additional security measures

**If API key is compromised:**

1. **Immediate Actions:**
   - Revoke compromised key
   - Generate new key
   - Update `.env` file

2. **Investigation:**
   - Review API usage logs
   - Check for unauthorized access
   - Identify source of compromise

3. **Prevention:**
   - Rotate all API keys
   - Restrict key permissions
   - Monitor usage closely

---

## Appendix

### Appendix A: Environment Variable Reference

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `PINATA_JWT_SECRET` | Yes | `eyJhbGc...` | Pinata IPFS API JWT token |
| `YOUTUBE_API_KEY` | Yes | `AIzaSy...` | YouTube Data API v3 key |
| `YOUTUBE_OAUTH_TOKEN` | For descriptions | `ya29.a0...` | YouTube OAuth access token |
| `XRPL_NODE_URL` | Yes | `https://s.altnet...` | XRPL node URL |
| `XRPL_SECRET` | Yes | `sEdXXX...` | XRPL wallet secret key |
| `MONGODB_URI` | Yes | `mongodb+srv://...` | MongoDB connection string |
| `MONGODB_DB` | Yes | `bcaxrpldev` | MongoDB database name |
| `NETWORK` | Recommended | `testnet` | Network identifier |

### Appendix B: XRPL Node URLs

**Testnet:**
- Primary: `https://s.altnet.rippletest.net:51234/`
- Alternative: `wss://s.altnet.rippletest.net:51233`

**Mainnet:**
- Primary: `https://xrplcluster.com/`
- Alternative 1: `https://s2.ripple.com:51234/`
- Alternative 2: `wss://xrplcluster.com/`
- Alternative 3: `https://s1.ripple.com:51234/`

### Appendix C: MongoDB Collections

| Collection | Purpose | Key Fields |
|------------|---------|------------|
| `videos` | YouTube video metadata | video_id, title, description |
| `nfts` | Minted NFT records | nft_id, video_id, tx_hash |
| `minting_log` | Audit trail | video_id, action, timestamp |

### Appendix D: IPFS Gateways

| Gateway | URL Format |
|---------|-----------|
| Pinata | `https://gateway.pinata.cloud/ipfs/{CID}` |
| Public | `https://ipfs.io/ipfs/{CID}` |
| Cloudflare | `https://cloudflare-ipfs.com/ipfs/{CID}` |

### Appendix E: Explorer URLs

| Network | Explorer URL |
|---------|--------------|
| XRPL Testnet | https://testnet.xrpl.org |
| XRPL Mainnet | https://livenet.xrpl.org |
| Alternative | https://xrpscan.com |

### Appendix F: Useful Links

- **XRPL Documentation**: https://xrpl.org
- **XRPL Status**: https://status.xrpl.org
- **XRPL Discord**: https://discord.gg/xrpl
- **MongoDB Atlas**: https://cloud.mongodb.com
- **Pinata Dashboard**: https://app.pinata.cloud
- **Google Cloud Console**: https://console.cloud.google.com
- **YouTube API Quotas**: https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
- **XRPL Testnet Faucet**: https://faucet.altnet.rippletest.net

### Appendix G: File Extensions

| Extension | Purpose |
|-----------|---------|
| `.py` | Python scripts |
| `.md` | Markdown documentation |
| `.json` | JSON data files |
| `.env` | Environment variables (NEVER commit) |
| `.log` | Log files |

### Appendix H: Git Best Practices

**Always in .gitignore:**
```
.env
.env.*
*.log
client_secrets.json
complete_videos.json
__pycache__/
venv/
```

**Before committing:**
```bash
# Check for secrets
git diff | grep -i "secret\|password\|key"

# Verify .env not staged
git status | grep .env
```

### Appendix I: Command Quick Reference

```bash
# Setup
cp .env.example .env
pip install -r requirements.txt
python test_setup.py

# Minting
python mint_nfts.py sync complete_videos.json
python mint_nfts.py mint 10
python mint_nfts.py status

# Queries
python query_nfts.py list 10
python query_nfts.py video <video_id>
python query_nfts.py verify

# Description Updates
python update_youtube_descriptions.py --check-only
python update_youtube_descriptions.py --execute --limit 10

# Blockchain Sync
python mint_nfts.py sync-nfts

# Verification
python verify_network.py
```

### Appendix J: Support Contacts

For issues or questions:
1. Review this documentation
2. Check troubleshooting section
3. Review error logs
4. Consult XRPL documentation
5. Visit XRPL Discord community

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-27 | Initial documentation |
| 1.5 | 2025-11-08 | Added mainnet deployment guide |
| 2.0 | 2025-11-14 | Comprehensive master documentation |

---

**End of Master Documentation**

This document covers all aspects of the YouTube NFT Minting Platform backend. For specific topics, refer to individual documentation files in the `docs/` folder.
