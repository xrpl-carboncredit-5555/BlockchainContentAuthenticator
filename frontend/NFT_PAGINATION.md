# NFT Pagination Implementation

## Overview

This application now supports fetching and displaying large NFT collections (500+ NFTs) through automatic pagination and parallel batch processing.

## Changes Made

### 1. **Pagination Implementation** (src/lib/xrpl.ts)

The `getAllNFTs()` method now automatically paginates through all NFTs on an account:

```typescript
// Fetches all NFTs using pagination
async getAllNFTs(walletAddress: string): Promise<NFTResult[]>
```

**Key Features:**
- Automatically handles pagination using XRPL's `marker` field
- Sets `limit: 400` (maximum allowed by XRPL) per request
- Continues fetching until all NFTs are retrieved
- Logs progress for each page

**Example Output:**
```
Fetching NFTs page 1...
Page 1: Found 400 NFTs (Total so far: 400)
Fetching NFTs page 2 with marker...
Page 2: Found 200 NFTs (Total so far: 600)
XRPL Response: Found 600 total NFTs across 2 pages
```

### 2. **Parallel Batch Processing**

NFT metadata is now processed in parallel batches for better performance:

**Configuration:**
- Batch size: 20 NFTs per batch
- Processes batches sequentially but NFTs within each batch in parallel
- Significantly faster than sequential processing

**Benefits:**
- Reduces total loading time for large collections
- Better utilization of network resources
- Progress logging for each batch

**Example Output:**
```
Processing batch 1/30 (NFTs 1-20 of 600)
Processing batch 2/30 (NFTs 21-40 of 600)
...
Successfully processed 600 NFTs
```

### 3. **UI Enhancements**

**Loading State:**
- Enhanced loading message for large collections
- Informs users that 500+ NFT collections may take time

**Stats Display:**
- Shows total number of videos/NFTs loaded
- Displays network being used (mainnet/testnet)
- Shows wallet address

## Performance Characteristics

### Small Collections (< 100 NFTs)
- **Fetch Time**: ~2-5 seconds
- **Pages**: 1 page
- **Metadata Processing**: 1-5 batches

### Medium Collections (100-400 NFTs)
- **Fetch Time**: ~5-15 seconds
- **Pages**: 1 page
- **Metadata Processing**: 5-20 batches

### Large Collections (400+ NFTs)
- **Fetch Time**: ~15-60 seconds
- **Pages**: 2+ pages
- **Metadata Processing**: 20+ batches

## Technical Details

### XRPL Pagination Parameters

```typescript
{
  command: 'account_nfts',
  account: walletAddress,
  limit: 400,        // Maximum per request
  marker: marker     // Continuation marker (optional)
}
```

### Response Structure

```typescript
{
  account_nfts: [...],  // Array of NFTs
  marker: "..."        // Present if more pages exist
}
```

### Batch Processing Flow

1. Fetch all NFTs via pagination (raw data)
2. Split NFTs into batches of 20
3. For each batch:
   - Process all 20 NFTs in parallel
   - Fetch IPFS metadata concurrently
   - Parse and normalize metadata
4. Aggregate all results
5. Return complete NFT collection

## Caching

The application uses a 6-hour cache for NFT data:

- **Cache Key**: `video_gallery_${walletAddress}`
- **Duration**: 6 hours (21,600 seconds)
- **Benefit**: Subsequent loads are instant for cached collections

## Console Logging

Monitor the browser console to see:
- Pagination progress
- Batch processing status
- Individual NFT processing
- Total counts and timing

## Limitations

1. **XRPL Rate Limits**: Respects XRPL node rate limits
2. **IPFS Timeouts**: 10-second timeout per IPFS fetch
3. **Browser Memory**: Very large collections (1000+) may impact browser performance

## Troubleshooting

### Slow Loading
- Check network connection
- Verify IPFS gateway availability
- Clear cache and retry: `ipfsCache.clear()`

### Incomplete Results
- Check console for error messages
- Verify wallet address is correct
- Ensure account exists on the configured network

### Out of Memory
- For extremely large collections (1000+), consider implementing:
  - Virtual scrolling
  - Lazy loading
  - Progressive rendering

## Future Enhancements

Potential improvements for very large collections:
- Streaming results (display as they load)
- Virtual scrolling for gallery
- Background sync
- Service worker caching
- Progressive Web App (PWA) features
