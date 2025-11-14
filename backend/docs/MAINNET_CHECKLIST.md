# XRPL Mainnet Deployment Checklist

Quick reference checklist for mainnet deployment.

## 📋 Pre-Launch Checklist

### 1. Wallet Setup
- [ ] Created new mainnet wallet
  ```bash
  python3 -c "from xrpl.wallet import Wallet; w = Wallet.create(); print(f'Address: {w.address}\nSecret: {w.seed}')"
  ```
- [ ] Saved wallet address: `___________________________`
- [ ] Saved wallet secret in password manager
- [ ] Created offline backup of wallet secret
- [ ] Funded wallet with 15-20 XRP
- [ ] Verified wallet activation at https://livenet.xrpl.org

### 2. Environment Configuration
- [ ] Copied `.env.mainnet.example` to `.env`
- [ ] Updated `XRPL_NODE_URL=https://xrplcluster.com/`
- [ ] Updated `XRPL_SECRET` with mainnet wallet secret
- [ ] Updated `MONGODB_URI` to production cluster
- [ ] Updated `MONGODB_DB=bcaxrplprod`
- [ ] Updated `PINATA_JWT_SECRET` with production token
- [ ] Updated `YOUTUBE_API_KEY` with production key
- [ ] Verified `.env` is in `.gitignore`

### 3. Security Verification
- [ ] Confirmed `.env` NOT committed to git
  ```bash
  git status --ignored | grep .env
  ```
- [ ] No secrets in git history
  ```bash
  git log --all -p | grep -i "secret\|password" || echo "Clean ✅"
  ```
- [ ] Wallet secret stored offline securely
- [ ] Production MongoDB has backups enabled
- [ ] Production MongoDB has IP whitelist configured

### 4. Network Verification
- [ ] Ran network verification script
  ```bash
  python verify_network.py
  ```
- [ ] Confirmed network = MAINNET
- [ ] Verified wallet balance > 15 XRP
- [ ] Verified MongoDB connection to production cluster
- [ ] Confirmed no testnet/mainnet mixing

### 5. Service Testing
- [ ] Ran complete service test
  ```bash
  python3 test_setup.py
  ```
- [ ] Pinata IPFS working
- [ ] YouTube API working
- [ ] XRPL connection working
- [ ] MongoDB working

### 6. Test Mint
- [ ] Minted single test NFT
  ```bash
  python3 mint_nfts.py mint 1
  ```
- [ ] Confirmed transaction on explorer: https://livenet.xrpl.org
- [ ] Verified NFT appears in wallet NFTs
- [ ] Confirmed metadata on IPFS
- [ ] Verified data saved to MongoDB
  ```bash
  python3 query_nfts.py list 1
  ```

---

## 🚀 Launch Day

### Phase 1: Initial Minting (10 NFTs)
- [ ] Reviewed latest wallet balance
- [ ] Started initial batch
  ```bash
  python3 mint_nfts.py mint 10
  ```
- [ ] Monitored for errors
- [ ] Verified transactions on explorer
- [ ] Checked MongoDB records

### Phase 2: Scale Up (50+ NFTs)
- [ ] Reviewed initial batch success
- [ ] Checked wallet balance
- [ ] Started scaled minting
  ```bash
  python3 mint_nfts.py mint 50
  ```
- [ ] Monitored progress
  ```bash
  python3 mint_nfts.py status
  ```

### Phase 3: Full Production
- [ ] Established monitoring schedule
- [ ] Set up balance alerts (< 5 XRP warning)
- [ ] Documented any issues encountered
- [ ] Created backup schedule for MongoDB

---

## 📊 Ongoing Maintenance

### Daily
- [ ] Check wallet balance
  ```bash
  python verify_network.py
  ```
- [ ] Review minting status
  ```bash
  python3 mint_nfts.py status
  ```
- [ ] Check for failed transactions
  ```bash
  # Check MongoDB minting_log collection
  ```

### Weekly
- [ ] Verify MongoDB backups
- [ ] Review IPFS storage usage
- [ ] Check YouTube API quota usage
- [ ] Audit NFT records vs blockchain

### Monthly
- [ ] Review transaction costs
- [ ] Analyze minting patterns
- [ ] Update documentation
- [ ] Test disaster recovery procedures

---

## 🆘 Emergency Contacts

### Services
- **XRPL Status**: https://status.xrpl.org
- **Pinata Support**: support@pinata.cloud
- **MongoDB Support**: https://support.mongodb.com

### Explorers
- **Mainnet Explorer**: https://livenet.xrpl.org
- **Account**: `___________________________`

### Backups
- **Wallet Secret Location**: `___________________________`
- **MongoDB Backup Location**: `___________________________`
- **Last Backup Date**: `___________________________`

---

## 🔴 Rollback Plan

If critical issues occur:

1. **Stop Minting**
   - Cancel any running minting operations
   - Do NOT delete any data

2. **Assess Damage**
   - Check wallet balance
   - Review failed transactions
   - Identify root cause

3. **Revert to Testnet**
   ```bash
   # Switch back to testnet
   cp .env.testnet.backup .env
   python verify_network.py
   ```

4. **Document Issue**
   - Record all error messages
   - Save transaction hashes
   - Note timestamps

5. **Fix and Re-test**
   - Fix issue on testnet
   - Test thoroughly
   - Document fix

6. **Return to Mainnet**
   - Only after thorough testnet validation
   - Start with single NFT test
   - Scale up gradually

---

## ✅ Post-Launch Verification

After first week:
- [ ] All minted NFTs visible on explorer
- [ ] Wallet balance > 10 XRP
- [ ] No failed transactions
- [ ] MongoDB backups working
- [ ] IPFS content accessible
- [ ] YouTube descriptions updated (if applicable)

---

## 📝 Notes

### Deployment Date
**Date**: ___________________________
**Deployed By**: ___________________________

### Wallet Information
**Address**: ___________________________
**Initial Balance**: ___________________________
**Network**: Mainnet

### NFT Minting Goals
**Initial Target**: ___________________________
**Expected Completion**: ___________________________

### Issues Encountered
1. ___________________________
2. ___________________________
3. ___________________________

---

**Last Updated**: 2025-11-08
**Version**: 1.0
**Status**: Ready for Production
