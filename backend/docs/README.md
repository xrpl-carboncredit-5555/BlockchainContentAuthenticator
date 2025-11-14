# YouTube NFT Minting Platform

Complete solution for minting YouTube videos as NFTs on XRPL with MongoDB tracking and IPFS storage.

## 🌟 Features

- ✅ **IPFS Image Persistence**: Thumbnails uploaded to IPFS (not just YouTube URLs)
- ✅ **MongoDB Integration**: Complete tracking of videos and NFTs
- ✅ **Mainnet Ready**: Production-ready with safety checks and validation
- ✅ **Network Verification**: Automatic testnet/mainnet detection with confirmation
- ✅ **Duplicate Detection**: Pre-mint and runtime CID duplicate checking
- ✅ **Transaction Verification**: Automatic recovery from network failures
- ✅ **Skip Tracking**: Mark videos to skip with MongoDB persistence
- ✅ **Compact MEMOs**: Same structure as reference implementation
- ✅ **Auto-Categorization**: Smart video classification
- ✅ **OpenSea Compatible**: Standard NFT metadata format

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# Pinata IPFS
PINATA_JWT_SECRET=your_jwt_token

# YouTube API
YOUTUBE_API_KEY=your_api_key

# XRPL (Testnet)
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234/
XRPL_SECRET=your_wallet_secret

# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
```

### 3. Sync Videos to MongoDB

```bash
python mint_nfts.py sync complete_videos.json
```

### 4. Mint NFTs

```bash
# Mint first unminted video
python mint_nfts.py mint 1

# Mint 10 videos
python mint_nfts.py mint 10

# Check status
python mint_nfts.py status
```

---

## 📁 Project Structure

```
mvp-backend/
├── src/
│   └── services/
│       ├── __init__.py
│       ├── mongodb_service.py      # MongoDB operations
│       ├── pinata_service.py       # IPFS uploads (images + metadata)
│       ├── xrpl_service.py         # XRPL NFT minting
│       └── youtube_service.py      # YouTube API
│
├── mint_nfts.py                    # Main management script
├── query_nfts.py                   # Query and view NFT data
├── test_setup.py                   # Test all services
├── .env.example                    # Environment template
├── requirements.txt                # Dependencies
└── README.md                       # This file
```

---

## 🔧 Services

### MongoDB Service

Complete database solution for NFT and video tracking.

**Collections:**
- `videos`: YouTube video metadata
- `nfts`: Minted NFT records with IPFS hashes
- `minting_log`: Complete audit trail

**Key Methods:**
```python
from src.services import create_mongodb_service

db = create_mongodb_service()

# Get unminted videos
unminted = db.get_unminted_videos(limit=10)

# Get minting statistics
stats = db.get_minting_stats()

# Get specific NFT
nft = db.get_nft_by_video_id("video_id")
```

### Pinata Service

Enhanced IPFS storage with image upload support.

**Features:**
- Upload JSON metadata to IPFS
- Upload images from URLs to IPFS
- Organize uploads with groups and tags
- Update metadata for existing pins

**Key Methods:**
```python
from src.services import create_pinata_service

pinata = create_pinata_service()

# Upload image from URL
result = pinata.upload_image_from_url(
    image_url="https://...",
    name="thumbnail.jpg",
    keyvalues={"type": "youtube_thumbnail"}
)

# Upload metadata
result = pinata.upload_json(
    json_data={"name": "NFT Name"},
    name="metadata.json"
)
```

### XRPL Service

NFT minting on XRP Ledger.

**Key Methods:**
```python
from src.services import create_xrpl_service

xrpl = create_xrpl_service()

# Mint NFT
result = xrpl.mint_nft(
    uri="ipfs://QmXXX...",
    taxon=0,
    flags=8,  # tfTransferable
    memo_data='{"id": "video_id"}',
    memo_type="nft_data"
)
```

### YouTube Service

YouTube Data API integration.

**Key Methods:**
```python
from src.services import create_youtube_service

youtube = create_youtube_service()

# Fetch channel videos
videos = youtube.fetch_all_videos_from_channel(
    channel_id="UCXXXX",
    max_results=50
)

# Get video details
details = youtube.get_video_details(video_id="abc123")
```

---

## 📊 NFT Metadata Structure

### On-Chain MEMO (Compact Format)

Stored in XRPL transaction memo - **same format as reference code**:

```json
{
  "id": "video_id",
  "title": "Video Title",
  "url": "https://www.youtube.com/watch?v=...",
  "thumb": "https://i.ytimg.com/vi/.../hqdefault.jpg",
  "channel": "JimFlintLSG",
  "date": "2025-10-27",
  "category": "AI & Technology"
}
```

### Full Metadata (IPFS Storage)

OpenSea-compatible metadata stored on IPFS:

```json
{
  "name": "Video Title",
  "description": "YouTube video from All-Time High...",
  "image": "ipfs://[image-hash]",
  "external_url": "https://www.youtube.com/watch?v=...",
  "attributes": [
    {"trait_type": "contextType", "value": "YouTube_NFT"},
    {"trait_type": "videoId", "value": "abc123"},
    {"trait_type": "channel", "value": "JimFlintLSG"},
    {"trait_type": "category", "value": "AI & Technology"},
    {"trait_type": "publishedDate", "value": "2025-10-27"},
    {"trait_type": "accountXRPL", "value": "rXXXX..."}
  ]
}
```

---

## 🗄️ MongoDB Schema

### Videos Collection
```javascript
{
  video_id: "abc123",           // Unique, indexed
  title: "Video Title",
  description: "...",
  published_at: "2025-10-27",
  thumbnail_url: "https://...",
  video_url: "https://...",
  channel_title: "JimFlintLSG",
  category: "AI & Technology",  // Auto-classified
  created_at: ISODate("..."),
  updated_at: ISODate("...")
}
```

### NFTs Collection
```javascript
{
  nft_id: "000B0000...",        // XRPL NFT ID
  video_id: "abc123",           // Links to video
  tx_hash: "ABC123...",         // XRPL transaction
  uri: "ipfs://Qm...",          // Metadata URI
  metadata_ipfs_hash: "Qm...",  // Metadata on IPFS
  image_ipfs_hash: "Qm...",     // Image on IPFS
  taxon: 123456,
  account: "rXXXX...",
  minted_at: ISODate("..."),
  metadata: { ... },            // Full metadata
  memo_data: { ... }            // Compact memo
}
```

---

## 🎯 Auto-Categorization

Videos are automatically categorized based on title and description:

- **AI & Technology**: AI, ChatGPT, Grok, LLM keywords
- **Automotive**: Car, dealer, vehicle keywords
- **Sports**: NFL, football, sports keywords
- **Business**: Business, entrepreneur, marketing keywords
- **General**: Default category

---

## 🔐 Network Configuration

### Testnet (Development)
```bash
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234/
MONGODB_DB=bcaxrpldev
```
- Free XRP from faucet: https://faucet.altnet.rippletest.net
- Safe for testing
- No real value

### Mainnet (Production)
```bash
XRPL_NODE_URL=https://xrplcluster.com/
MONGODB_DB=bcaxrplprod
```
- Real XRP required (15-20 XRP recommended)
- Permanent blockchain records
- Production NFTs with real value

**🚀 Ready for Mainnet?** See [MAINNET_DEPLOYMENT.md](MAINNET_DEPLOYMENT.md) for complete deployment guide.

### Network Verification

Before minting, verify your network configuration:

```bash
python verify_network.py
```

This will:
- ✅ Detect testnet vs mainnet
- ✅ Verify wallet configuration
- ✅ Check wallet balance
- ✅ Warn about potential issues
- ✅ Prevent accidental mainnet usage

---

## 📋 Management Commands

### Verify Network (Run First!)
```bash
# Verify network configuration and prevent mainnet accidents
python verify_network.py
```

This will verify:
- ✅ Network detection (testnet vs mainnet)
- ✅ Wallet configuration and balance
- ✅ Database configuration
- ✅ Prevent testnet/mainnet mix-ups

### Test Setup
```bash
# Verify all services are configured
python3 test_setup.py
```

This will test:
- ✅ Environment variables
- ✅ MongoDB connection
- ✅ Pinata IPFS service
- ✅ XRPL connection
- ✅ YouTube API
- ✅ Data flow (save/retrieve)

### Sync Videos
```bash
# Sync from default file
python3 mint_nfts.py sync

# Sync from specific file
python3 mint_nfts.py sync videos.json
```

### Mint NFTs
```bash
# Mint 1 NFT
python3 mint_nfts.py mint 1

# Mint 10 NFTs
python3 mint_nfts.py mint 10

# Mint 50 NFTs
python3 mint_nfts.py mint 50
```

### Sync NFTs from Blockchain
```bash
# Sync blockchain NFTs to MongoDB
python3 mint_nfts.py sync-nfts
```

This command:
- Fetches all NFTs from XRPL blockchain
- Compares with MongoDB database
- Shows analytics (matched, missing, orphaned)
- Prompts to update missing NFTs
- Recovers NFTs from failed minting attempts

### Check Status
```bash
python3 mint_nfts.py status
```

**Output:**
```
📊 YouTube NFT Minting Status
======================================================================
📺 Total Videos: 100
✅ Minted NFTs: 50
⏳ Unminted: 50

📂 Category Breakdown:
   AI & Technology: 25 videos
   Automotive: 15 videos
   Sports: 10 videos
```

### Query NFT Data
```bash
# List all NFTs
python3 query_nfts.py list 10

# Query by video ID
python3 query_nfts.py video <video_id>

# Query by NFT token ID
python3 query_nfts.py nft <nft_token_id>

# Verify all fields are saved
python3 query_nfts.py verify
```

---

## 🔄 Minting Process

The minting script performs the following steps:

1. ✅ **Upload thumbnail to IPFS** → Permanent image storage
2. ✅ **Create OpenSea-compatible metadata** → Industry standards
3. ✅ **Upload metadata to IPFS** → Decentralized storage
4. ✅ **Generate unique taxon** → From video ID hash
5. ✅ **Create compact MEMO** → For on-chain querying (same format as reference)
6. ✅ **Mint NFT on XRPL** → Blockchain transaction
7. ✅ **Save to MongoDB** → Complete tracking

---

## 💾 Dependencies

```
requests>=2.31.0        # HTTP requests
python-dotenv>=1.0.0    # Environment variables
xrpl-py>=2.5.0          # XRPL integration
pymongo>=4.5.0          # MongoDB driver
Pillow>=10.0.0          # Image processing
```

---

## 🛠️ Troubleshooting

### "MONGODB_URI environment variable is required"
**Fix:** Add `MONGODB_URI` to `.env` file

### "Failed to upload image to Pinata"
**Fix:** Verify `PINATA_JWT_SECRET` is correct. Script falls back to YouTube URL if upload fails.

### "NFT already exists for video_id"
**Fix:** This video is already minted. Check MongoDB or use `status` command.

### "Insufficient XRP balance"
**Fix:**
- **Testnet:** Use faucet at https://faucet.altnet.rippletest.net
- **Mainnet:** Fund wallet with XRP

---

## 🔗 Resources

- **Pinata Dashboard**: https://app.pinata.cloud
- **MongoDB Atlas**: https://cloud.mongodb.com
- **XRPL Testnet Explorer**: https://testnet.xrpl.org
- **XRPL Mainnet Explorer**: https://livenet.xrpl.org
- **XRPL Testnet Faucet**: https://faucet.altnet.rippletest.net

---

## 📈 Example Workflow

### Testnet Development Workflow

```bash
# 1. Setup environment
cp .env.example .env
# Edit .env with testnet credentials

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Verify network configuration
python verify_network.py

# 4. Test all services
python3 test_setup.py

# 5. Sync videos to MongoDB
python3 mint_nfts.py sync complete_videos.json

# 6. Check status
python3 mint_nfts.py status

# 7. Mint first NFT (test)
python3 mint_nfts.py mint 1

# 8. Verify NFT fields
python3 query_nfts.py verify

# 9. Query minted NFT
python3 query_nfts.py list 10

# 10. Mint more NFTs
python3 mint_nfts.py mint 10
```

### Mainnet Production Workflow

```bash
# 1. Review mainnet deployment guide
cat MAINNET_DEPLOYMENT.md

# 2. Setup mainnet environment
cp .env.mainnet.example .env
# Edit .env with mainnet credentials

# 3. Create and fund mainnet wallet (15-20 XRP)
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"

# 4. Verify network configuration
python verify_network.py

# 5. Test single NFT mint
python3 mint_nfts.py mint 1
# You will be prompted to type 'CONFIRM' for mainnet operations

# 6. Verify on XRPL explorer
# Visit: https://livenet.xrpl.org

# 7. Begin batch minting
python3 mint_nfts.py mint 100

# 8. Monitor progress
python3 mint_nfts.py status
```

**See:**
- [TESTING.md](TESTING.md) - Complete testing guide
- [MAINNET_DEPLOYMENT.md](MAINNET_DEPLOYMENT.md) - Production deployment guide
- [DUPLICATE_HANDLING.md](DUPLICATE_HANDLING.md) - Duplicate detection & recovery guide
- [NFT_SYNC_GUIDE.md](NFT_SYNC_GUIDE.md) - Blockchain sync guide

---

## ✨ Key Features

✅ **Clean Architecture**: Services in `src/services/`, single management script
✅ **MongoDB Tracking**: Complete database with videos, NFTs, and audit logs
✅ **IPFS Persistence**: Images and metadata permanently stored
✅ **Mainnet Ready**: Production configuration (currently testnet)
✅ **Compact MEMOs**: Same format as reference implementation
✅ **Auto-Classification**: Smart category detection
✅ **OpenSea Compatible**: Standard metadata format
✅ **Error Handling**: Comprehensive logging and recovery

---

## 📝 License

This project is for YouTube video verification and NFT minting on XRPL.
