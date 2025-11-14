# XRPL Mainnet Deployment Guide

Complete guide for deploying your YouTube NFT Minting Platform to XRPL Mainnet.

---

## 🚨 Pre-Deployment Checklist

### Critical Requirements

Before deploying to mainnet, ensure you have:

- [ ] **Funded XRPL Mainnet Wallet** with sufficient XRP for:
  - Account reserve: **10 XRP minimum**
  - Transaction fees: **~0.00001 XRP per transaction**
  - NFT minting: **Estimated 100-500 NFTs = ~1-2 XRP total fees**

- [ ] **Backup of Wallet Secret** stored securely (offline storage recommended)

- [ ] **Tested on Testnet** - Verify all functionality works correctly

- [ ] **Production MongoDB Instance** (not test database)

- [ ] **Production Pinata Account** with sufficient storage

---

## 🔐 Step 1: Create Mainnet Wallet

### Option A: Generate New Wallet (Recommended for Production)

```python
python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\\nSecret: {w.seed}')"
```

**CRITICAL:** Save both the address and secret immediately:
- Store secret in password manager or hardware wallet
- **Never commit secret to git**
- Keep backup copy in secure location

### Option B: Import Existing Wallet

If you already have a mainnet wallet, you can use its secret directly.

### Step 2: Fund Your Wallet

**Minimum Funding:**
- **10 XRP** for account activation
- **5-10 XRP** for transaction fees (depending on volume)
- **Total: 15-20 XRP recommended**

**How to Fund:**
1. Transfer XRP from exchange (Coinbase, Kraken, Binance, etc.)
2. Use another XRPL wallet you control
3. Verify receipt at: https://livenet.xrpl.org

**Verify Balance:**
```bash
# After setting mainnet env vars
python3 -c "from src.services import create_xrpl_service; xrpl = create_xrpl_service(); info = xrpl.get_account_info(); print(f'Balance: {info[\"account_data\"][\"Balance\"]} drops ({int(info[\"account_data\"][\"Balance\"])/1000000} XRP)')"
```

---

## ⚙️ Step 3: Configure Environment

### Create Mainnet Environment File

Copy your current `.env` to `.env.mainnet` for backup:

```bash
cp .env .env.testnet.backup
```

### Update `.env` with Mainnet Configuration

```bash
# Pinata IPFS (Production)
PINATA_JWT_SECRET=your_production_jwt_token

# YouTube API (Production)
YOUTUBE_API_KEY=your_production_api_key
YOUTUBE_OAUTH_TOKEN=your_oauth_token_here

# XRPL MAINNET Configuration
XRPL_NODE_URL=https://xrplcluster.com/
XRPL_SECRET=sXXXXXXXXXXXXXXXXXXXXXXXXXXX

# MongoDB (Production)
MONGODB_URI=mongodb+srv://production_user:password@production_cluster.mongodb.net/
MONGODB_DB=bcaxrplprod

# Network Identifier (for logging)
NETWORK=mainnet
```

### Recommended Mainnet Node URLs

**Primary (Recommended):**
```bash
XRPL_NODE_URL=https://xrplcluster.com/
```

**Alternatives:**
```bash
# Option 2: Ripple's public mainnet
XRPL_NODE_URL=https://s2.ripple.com:51234/

# Option 3: WebSocket (for real-time)
XRPL_NODE_URL=wss://xrplcluster.com/

# Option 4: Your own node (if running)
XRPL_NODE_URL=https://your-xrpl-node.com/
```

---

## 🧪 Step 4: Test Mainnet Connection

### Verify All Services

```bash
python3 test_setup.py
```

**Expected Output:**
```
XRPL Service Initialized
  Wallet Address: rXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
  Node: https://xrplcluster.com/
```

### Verify Wallet Balance

```bash
python3 -c "
from src.services import create_xrpl_service
xrpl = create_xrpl_service()
info = xrpl.get_account_info()
if info['success']:
    balance = int(info['account_data']['Balance']) / 1_000_000
    print(f'✅ Wallet Balance: {balance} XRP')
    if balance < 10:
        print('⚠️  WARNING: Balance below minimum (10 XRP)')
else:
    print(f'❌ Error: {info[\"error\"]}')
"
```

---

## 🚀 Step 5: Production Deployment

### Phase 1: Test Mint (1 NFT)

**Test with a single NFT first:**

```bash
# Mint 1 NFT on mainnet
python3 mint_nfts.py mint 1
```

**Verify on XRPL Explorer:**
1. Go to: https://livenet.xrpl.org
2. Search for your wallet address
3. Check "NFTs" tab
4. Verify transaction hash

### Phase 2: Batch Minting

Once verified, proceed with batch minting:

```bash
# Mint 10 NFTs
python3 mint_nfts.py mint 10

# Check status
python3 mint_nfts.py status

# Mint more as needed
python3 mint_nfts.py mint 50
```

### Phase 3: Monitor Progress

```bash
# Check minting stats
python3 mint_nfts.py status

# Query specific NFT
python3 query_nfts.py video <video_id>

# List all minted NFTs
python3 query_nfts.py list 100
```

---

## 📊 Cost Estimation

### Transaction Fees

| Operation | Estimated Cost |
|-----------|----------------|
| NFTokenMint | ~0.00001 XRP |
| AccountSet (domain) | ~0.00001 XRP |
| Average per NFT | ~0.00002 XRP |

### Budget Examples

| NFTs to Mint | Estimated XRP Cost |
|--------------|-------------------|
| 100 NFTs | ~0.002 XRP |
| 500 NFTs | ~0.01 XRP |
| 1,000 NFTs | ~0.02 XRP |
| 5,000 NFTs | ~0.1 XRP |

**Note:** Actual costs may vary based on network load. Reserve **10-20 XRP** for safety.

---

## 🔒 Security Best Practices

### Wallet Security

1. **Never share your wallet secret**
2. **Use environment variables only** - Never hardcode secrets
3. **Backup your secret** in multiple secure locations
4. **Monitor your wallet** for unauthorized transactions
5. **Use a dedicated wallet** for minting (not your personal holdings)

### Environment Security

```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore

# Verify no secrets in git
git log --all -p | grep -i "secret\|password\|key"
```

### Production Checklist

- [ ] Wallet secret stored securely offline
- [ ] `.env` file NOT committed to git
- [ ] Production MongoDB has backups enabled
- [ ] Pinata account has sufficient storage quota
- [ ] YouTube API quota monitored
- [ ] Error logging and monitoring configured

---

## 🔄 Switching Between Networks

### Quick Network Switch

**To Testnet:**
```bash
# In .env
XRPL_NODE_URL=https://s.altnet.rippletest.net:51234/
XRPL_SECRET=sTestnetSecretXXXXXXXXXXXXXXXX
MONGODB_DB=bcaxrpldev
```

**To Mainnet:**
```bash
# In .env
XRPL_NODE_URL=https://xrplcluster.com/
XRPL_SECRET=sMainnetSecretXXXXXXXXXXXXXXXX
MONGODB_DB=bcaxrplprod
```

### Use Separate Environment Files

```bash
# Switch to testnet
cp .env.testnet .env

# Switch to mainnet
cp .env.mainnet .env
```

---

## 🐛 Troubleshooting

### "Account not found" Error

**Cause:** Wallet not activated on mainnet
**Fix:** Fund wallet with at least 10 XRP

### "Insufficient XRP" Error

**Cause:** Not enough XRP for transaction fees
**Fix:** Add more XRP to wallet (5-10 XRP recommended)

### "tecUNFUNDED_PAYMENT" Error

**Cause:** Account reserve too low
**Fix:** Ensure wallet has 10+ XRP base reserve

### Connection Timeout

**Cause:** Mainnet node unreachable
**Fix:** Try alternative node URL:
```bash
XRPL_NODE_URL=https://s2.ripple.com:51234/
```

### Transaction Failed

1. Check wallet balance: `python3 query_nfts.py verify`
2. Verify network connectivity
3. Check XRPL status: https://status.xrpl.org
4. Review error in minting_log collection

---

## 📈 Monitoring & Maintenance

### Monitor Wallet Balance

```bash
# Check balance regularly
python3 -c "from src.services import create_xrpl_service; xrpl = create_xrpl_service(); info = xrpl.get_account_info(); print(f'Balance: {int(info[\"account_data\"][\"Balance\"])/1000000} XRP')"
```

### Monitor Minting Progress

```bash
# Daily status check
python3 mint_nfts.py status

# Query recent NFTs
python3 query_nfts.py list 10
```

### MongoDB Backups

Ensure production MongoDB has:
- Automated daily backups
- Point-in-time recovery enabled
- Backup retention policy (30+ days)

---

## 🎯 Mainnet vs Testnet Differences

| Feature | Testnet | Mainnet |
|---------|---------|---------|
| **Node URL** | https://s.altnet.rippletest.net:51234/ | https://xrplcluster.com/ |
| **XRP Cost** | Free (faucet) | Real XRP required |
| **Explorer** | https://testnet.xrpl.org | https://livenet.xrpl.org |
| **Permanence** | Periodically reset | Permanent records |
| **Data Validity** | Test data only | Production data |
| **Risk** | Zero risk | Financial risk |
| **NFT Value** | No value | Potential value |

---

## 📝 Pre-Launch Checklist

Complete this checklist before mainnet launch:

### Technical Setup
- [ ] Mainnet wallet created and funded (15-20 XRP)
- [ ] Wallet secret backed up securely
- [ ] .env configured for mainnet
- [ ] All services tested with `test_setup.py`
- [ ] Test mint completed successfully (1 NFT)
- [ ] Transaction verified on livenet.xrpl.org

### Database & Storage
- [ ] Production MongoDB configured
- [ ] Database backups enabled
- [ ] Pinata production account active
- [ ] YouTube API quota sufficient

### Security
- [ ] `.env` in `.gitignore`
- [ ] No secrets committed to git
- [ ] Wallet secret stored offline
- [ ] Access controls configured

### Documentation
- [ ] Team trained on mainnet procedures
- [ ] Incident response plan documented
- [ ] Monitoring alerts configured

---

## 🚀 Ready to Launch?

Once all checklist items are complete:

```bash
# 1. Final verification
python3 test_setup.py

# 2. Test mint 1 NFT
python3 mint_nfts.py mint 1

# 3. Verify on explorer
# Visit: https://livenet.xrpl.org

# 4. Start production minting
python3 mint_nfts.py mint 100

# 5. Monitor progress
python3 mint_nfts.py status
```

---

## 📞 Support Resources

- **XRPL Documentation**: https://xrpl.org
- **XRPL Status**: https://status.xrpl.org
- **XRPL Discord**: https://discord.gg/xrpl
- **Mainnet Explorer**: https://livenet.xrpl.org

---

## ⚠️ Important Warnings

1. **Mainnet transactions are permanent** - Cannot be reversed
2. **XRP costs real money** - Budget accordingly
3. **Test thoroughly on testnet first** - Verify all functionality
4. **Backup your wallet secret** - Loss means permanent loss of funds
5. **Never share your secret** - Keep it completely private
6. **Monitor your wallet** - Watch for unauthorized activity

---

**Last Updated:** 2025-11-08
**Network:** XRPL Mainnet
**Version:** 1.0
