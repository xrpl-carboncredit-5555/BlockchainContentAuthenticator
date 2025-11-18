import { Client, AccountNFTsRequest } from 'xrpl'
import { ipfsCache } from './ipfsCache'
import { ipfsImageCache } from './ipfsImageCache'

export interface NFTMetadata {
  // Enhanced YouTube NFT format
  name?: string
  image?: string
  video_url?: string
  video_id?: string
  channel?: string
  category?: string
  published?: number
  verified?: number
  verification_timestamp?: number
  source?: string
  url?: string
  u?: string

  // Compact format properties
  n?: string  // name/title
  v?: string  // video_id
  p?: number  // published
  vf?: number // verified
  c?: string  // channel
  id?: string // video id
  videoId?: string // video id

  // Redirect links
  redirects?: {
    youtube?: string
    thumbnail?: string
    channel?: string
  }

  // Extended metadata
  description?: string
  external_url?: string
  youtube_metadata?: {
    video_id?: string
    video_url?: string
    thumbnail_url?: string
    channel_title?: string
    published_at?: string
    description?: string
  }

  // Attributes for display
  attributes?: Array<{
    trait_type: string
    value: string | number
    display_type?: string
    max_value?: number
  }>

  // Legacy fields for compatibility
  title?: string
  thumbnail_url?: string
  published_at?: string
  publishedDate?: number | string
  channel_title?: string
  creator?: string
  platform?: string
  content_type?: string
  ai_content_claim?: string
  ai?: string
  verification_note?: string
}

export interface VideoNFT {
  nft_id: string
  title: string
  video_url: string
  minted_at: string
  wallet_address: string
}

export interface NFTResult {
  nft_id: string
  metadata: NFTMetadata | null
  issuer: string
  flags: number
}

export interface XRPLNFTResponse {
  NFTokenID: string
  URI?: string
  Issuer: string
  Flags: number
}

export class XRPLService {
  private client: Client
  private isTestnet: boolean

  constructor(testnet?: boolean) {
    // Use environment variable if not explicitly provided
    // Defaults to mainnet if env variable is not set
    const networkFromEnv = process.env.NEXT_PUBLIC_XRPL_NETWORK?.toLowerCase()
    this.isTestnet = testnet !== undefined ? testnet : networkFromEnv === 'testnet'

    const url = this.isTestnet
      ? 'wss://s.altnet.rippletest.net:51233'
      : 'wss://xrplcluster.com'

    this.client = new Client(url)
  }

  async connect() {
    if (!this.client.isConnected()) {
      await this.client.connect()
    }
  }

  async disconnect() {
    if (this.client.isConnected()) {
      await this.client.disconnect()
    }
  }

  async getNFTByTokenId(nftId: string, walletAddress: string): Promise<NFTResult | null> {
    try {
      await this.connect()

      // Validate that the NFT ID format is correct
      if (!nftId || nftId.length < 32) {
        throw new Error('Invalid NFT ID format')
      }

      console.log(`Searching for NFT ${nftId} in account ${walletAddress}`)

      let allNFTs: XRPLNFTResponse[] = []
      let marker: unknown = undefined
      let pageCount = 0

      // Paginate through all NFTs to find the exact match
      do {
        pageCount++
        const request: AccountNFTsRequest = {
          command: 'account_nfts',
          account: walletAddress,
          limit: 400, // Maximum allowed by XRPL
          ...(marker ? { marker } : {})
        } as AccountNFTsRequest

        console.log(`Fetching NFTs page ${pageCount} to find ${nftId}...`)
        const response = await this.client.request(request)

        if (!response.result) {
          throw new Error('Invalid response from XRPL')
        }

        const result = response.result as {
          error?: string
          account_nfts?: Array<{ NFTokenID: string; URI?: string; Issuer: string; Flags: number }>
          marker?: unknown
        }

        if (result.error) {
          if (result.error === 'actNotFound') {
            throw new Error(`Account ${walletAddress} not found on the XRPL ledger`)
          }
          throw new Error(`XRPL Error: ${result.error}`)
        }

        const pageNFTs = result.account_nfts || []
        allNFTs = allNFTs.concat(pageNFTs)

        console.log(`Page ${pageCount}: Searched ${pageNFTs.length} NFTs (Total searched: ${allNFTs.length})`)

        // Update marker for next page
        marker = result.marker
      } while (marker)

      console.log(`Total NFTs in account: ${allNFTs.length}`)

      // Find NFT by EXACT ID match only (no partial matching!)
      const nft = allNFTs.find((nft: XRPLNFTResponse) => nft.NFTokenID === nftId)

      if (!nft) {
        console.log(`NFT ${nftId} not found in account ${walletAddress} after searching ${allNFTs.length} NFTs`)
        return null
      }

      console.log(`Found exact match for NFT ${nftId}`)

      let metadata = null

      // Enhanced metadata retrieval with multiple fallbacks
      try {
        // First try to get metadata from transaction MEMOs
        const memoMetadata = await this.extractMemoMetadata(nft.NFTokenID)
        if (memoMetadata) {
          metadata = memoMetadata
        }

        // If no MEMO data, try to parse URI with improved error handling
        if (!metadata && nft.URI) {
          const uriDecoded = Buffer.from(nft.URI, 'hex').toString('utf8')

          // Check if it's an IPFS URI
          if (uriDecoded.startsWith('ipfs://')) {
            const ipfsHash = uriDecoded.replace('ipfs://', '')
            metadata = await this.fetchFromIPFS(ipfsHash)
          } else if (uriDecoded.startsWith('http')) {
            // Handle HTTP(S) URLs
            const response = await fetch(uriDecoded)
            if (response.ok) {
              metadata = await response.json()
            }
          } else {
            // Try to parse as direct JSON
            try {
              metadata = JSON.parse(uriDecoded)
            } catch {
              // If not JSON, create metadata object from URI
              metadata = { uri: uriDecoded }
            }
          }
        }
      } catch (e) {
        console.error('Error retrieving NFT metadata:', e)
        // Don't fail the entire request if metadata can't be loaded
      }

      const processedMetadata = metadata ? this.processMetadata(metadata) : null

      return {
        nft_id: nft.NFTokenID,
        metadata: processedMetadata,
        issuer: nft.Issuer,
        flags: nft.Flags
      }
    } catch (error) {
      console.error('Error fetching NFT:', error)
      throw error
    } finally {
      await this.disconnect()
    }
  }

  async getAllNFTs(walletAddress: string): Promise<NFTResult[]> {
    try {
      await this.connect()
      console.log(`Connecting to XRPL to fetch NFTs for account: ${walletAddress}`)

      let allNFTs: XRPLNFTResponse[] = []
      let marker: unknown = undefined
      let pageCount = 0

      // Paginate through all NFTs
      do {
        pageCount++
        const request: AccountNFTsRequest = {
          command: 'account_nfts',
          account: walletAddress,
          limit: 400, // Maximum allowed by XRPL
          ...(marker ? { marker } : {})
        } as AccountNFTsRequest

        console.log(`Fetching NFTs page ${pageCount}${marker ? ' with marker' : ''}...`)
        const response = await this.client.request(request)

        if (!response.result) {
          console.error('No result in XRPL response')
          throw new Error('Invalid response from XRPL')
        }

        // Check for errors (type-safe approach)
        const result = response.result as {
          error?: string
          account_nfts?: Array<{ NFTokenID: string; URI?: string; Issuer: string; Flags: number }>
          marker?: unknown
        }

        if (result.error) {
          console.error('XRPL returned error:', result.error)
          if (result.error === 'actNotFound') {
            throw new Error(`Account ${walletAddress} not found on the XRPL ledger`)
          }
          throw new Error(`XRPL Error: ${result.error}`)
        }

        const pageNFTs = result.account_nfts || []
        allNFTs = allNFTs.concat(pageNFTs)

        console.log(`Page ${pageCount}: Found ${pageNFTs.length} NFTs (Total so far: ${allNFTs.length})`)

        // Update marker for next page
        marker = result.marker
      } while (marker)

      console.log(`XRPL Response: Found ${allNFTs.length} total NFTs across ${pageCount} pages`)
      console.log('Processing metadata for all NFTs...')

      // Process NFTs in parallel batches for better performance
      const BATCH_SIZE = 20
      const results: NFTResult[] = []

      for (let i = 0; i < allNFTs.length; i += BATCH_SIZE) {
        const batch = allNFTs.slice(i, Math.min(i + BATCH_SIZE, allNFTs.length))
        const batchNumber = Math.floor(i / BATCH_SIZE) + 1
        const totalBatches = Math.ceil(allNFTs.length / BATCH_SIZE)

        console.log(`Processing batch ${batchNumber}/${totalBatches} (NFTs ${i + 1}-${Math.min(i + BATCH_SIZE, allNFTs.length)} of ${allNFTs.length})`)

        const batchResults = await Promise.all(
          batch.map(async (nft) => {
            let metadata = null

            if (nft.URI) {
              try {
                const uriDecoded = Buffer.from(nft.URI, 'hex').toString('utf8')

                // Check if it's an IPFS URI
                if (uriDecoded.startsWith('ipfs://')) {
                  const ipfsHash = uriDecoded.replace('ipfs://', '')
                  try {
                    metadata = await this.fetchFromIPFS(ipfsHash)
                    if (!metadata) {
                      metadata = {
                        ipfs_hash: ipfsHash,
                        name: 'YouTube NFT',
                        description: 'IPFS content unavailable'
                      }
                    }
                  } catch {
                    metadata = {
                      ipfs_hash: ipfsHash,
                      name: 'YouTube NFT',
                      description: 'Loading from IPFS failed'
                    }
                  }
                } else if (uriDecoded.startsWith('http')) {
                  // Handle HTTP(S) URLs
                  try {
                    const response = await fetch(uriDecoded)
                    if (response.ok) {
                      metadata = await response.json()
                    }
                  } catch {
                    metadata = { uri: uriDecoded, error: 'Failed to fetch metadata' }
                  }
                } else {
                  // Try to parse as JSON
                  try {
                    metadata = JSON.parse(uriDecoded)
                  } catch {
                    metadata = { uri: uriDecoded }
                  }
                }

                if (metadata) {
                  metadata = this.processMetadata(metadata)
                }
              } catch (e) {
                console.error(`Error parsing NFT URI for ${nft.NFTokenID}:`, e)
              }
            }

            return {
              nft_id: nft.NFTokenID,
              metadata,
              issuer: nft.Issuer,
              flags: nft.Flags
            }
          })
        )

        results.push(...batchResults)
      }

      console.log(`Successfully processed ${results.length} NFTs`)
      return results
    } catch (error) {
      console.error('Error fetching NFTs:', error)
      throw error
    } finally {
      await this.disconnect()
    }
  }

  private processMetadata(metadata: NFTMetadata): NFTMetadata {
    // Process and normalize metadata format
    const processed: NFTMetadata = { ...metadata }

    // Extract data from attributes if present
    if (metadata.attributes && Array.isArray(metadata.attributes)) {
      metadata.attributes.forEach(attr => {
        switch (attr.trait_type) {
          case 'videoId':
            processed.video_id = attr.value as string
            break
          case 'source':
            processed.video_url = attr.value as string
            break
          case 'channel':
            processed.channel = attr.value as string
            processed.channel_title = attr.value as string
            break
          case 'category':
            processed.category = attr.value as string
            break
          case 'publishedDate':
            processed.published_at = attr.value as string
            break
        }
      })
    }

    // Ensure YouTube video fields are populated
    if (metadata.video_url || metadata.redirects?.youtube || metadata.source) {
      processed.video_url = metadata.video_url || metadata.redirects?.youtube || metadata.source
    }

    if (metadata.image || metadata.redirects?.thumbnail) {
      processed.thumbnail_url = metadata.image || metadata.redirects?.thumbnail
    }

    if (metadata.channel) {
      processed.channel_title = metadata.channel
    }

    // Handle various ID formats
    if (metadata.video_id || metadata.videoId || metadata.id) {
      processed.video_id = metadata.video_id || metadata.videoId || metadata.id
    }

    // Convert timestamps to readable dates if needed
    if (metadata.published && !metadata.published_at) {
      processed.published_at = new Date(metadata.published * 1000).toISOString()
    }

    if (metadata.verified) {
      processed.verification_timestamp = metadata.verified
    }

    return processed
  }

  getBithompExplorerUrl(nftId: string): string {
    const domain = this.isTestnet ? 'test.bithomp.com' : 'bithomp.com'
    return `https://${domain}/nft/${nftId}`
  }

  getXRPLExplorerUrl(nftId: string): string {
    const domain = this.isTestnet ? 'testnet.xrpl.org' : 'livenet.xrpl.org'
    return `https://${domain}/nft/${nftId}`
  }

  getNetworkName(): string {
    return this.isTestnet ? 'testnet' : 'mainnet'
  }

  private async fetchFromIPFS(ipfsHash: string): Promise<NFTMetadata | null> {
    // Check cache first
    const cachedData = ipfsCache.get(ipfsHash)
    if (cachedData) {
      return cachedData
    }

    const gateways = [
      'https://crimson-main-grouse-700.mypinata.cloud/ipfs/',
      'https://gateway.pinata.cloud/ipfs/',
      'https://ipfs.io/ipfs/',
      'https://cloudflare-ipfs.com/ipfs/',
      'https://gateway.ipfs.io/ipfs/'
    ]

    for (const gateway of gateways) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 10000) // 10 second timeout

        const response = await fetch(`${gateway}${ipfsHash}`, {
          signal: controller.signal,
          headers: {
            'Accept': 'application/json',
          }
        })
        clearTimeout(timeoutId)

        if (response.ok) {
          const data = await response.json()
          console.log(`Successfully fetched metadata from ${gateway}`)

          // Cache the fetched data
          ipfsCache.set(ipfsHash, data)

          return data
        }
      } catch (e) {
        console.log(`Failed to fetch from gateway ${gateway}:`, e instanceof Error ? e.message : e)
        continue
      }
    }

    console.error(`Failed to fetch IPFS data from all gateways for hash: ${ipfsHash}`)
    return null
  }

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  async extractMemoMetadata(_nftTokenId: string): Promise<NFTMetadata | null> {
    try {
      // Try to find the mint transaction for this NFT
      const accountTxRequest = {
        command: 'account_tx',
        account: 'rrn5TTseRjmcV3Da3Z4ituzKsoXWVqYpbg',
        limit: 100,
        ledger_index_min: -1,
        ledger_index_max: -1
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const txsResponse = await this.client.request(accountTxRequest as any)
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const result = txsResponse.result as any

      if (result && result.transactions) {
        for (const tx of result.transactions) {
          if (tx.tx && tx.tx.TransactionType === 'NFTokenMint' && tx.tx.Memos) {
            const memos = tx.tx.Memos
            for (const memo of memos) {
              if (memo.Memo && memo.Memo.MemoType) {
                const memoType = Buffer.from(memo.Memo.MemoType, 'hex').toString('utf8')
                if (memoType === 'nft_data' && memo.Memo.MemoData) {
                  const memoData = Buffer.from(memo.Memo.MemoData, 'hex').toString('utf8')
                  return JSON.parse(memoData)
                }
              }
            }
          }
        }
      }
    } catch (e) {
      console.log('Could not extract MEMO metadata:', e)
    }
    return null
  }

  async getYouTubeNFTsOnly(walletAddress: string): Promise<NFTResult[]> {
    // Get all NFTs and filter for YouTube videos
    const allNFTs = await this.getAllNFTs(walletAddress)

    return allNFTs.filter(nft => {
      // If no metadata, skip this NFT
      if (!nft.metadata) return false

      // Check various indicators that this is a YouTube NFT
      const isYouTubeNFT =
        nft.metadata?.video_id ||
        nft.metadata?.videoId ||
        nft.metadata?.id ||
        nft.metadata?.redirects?.youtube ||
        nft.metadata?.video_url?.includes('youtube.com') ||
        nft.metadata?.video_url?.includes('youtu.be') ||
        nft.metadata?.url?.includes('youtube.com') ||
        nft.metadata?.url?.includes('youtu.be') ||
        nft.metadata?.source?.includes('youtube.com') ||
        nft.metadata?.attributes?.some((attr: { trait_type: string; value: string | number }) =>
          attr.trait_type === 'contextType' && attr.value === 'YouTube_NFT'
        ) ||
        nft.metadata?.attributes?.some((attr: { trait_type: string; value: string | number }) =>
          attr.trait_type === 'platform' && attr.value === 'YouTube'
        )

      return isYouTubeNFT
    })
  }

  // Cache management methods
  clearIPFSCache(): void {
    ipfsCache.clear()
    console.log('IPFS metadata cache cleared')
  }

  clearExpiredIPFSCache(): void {
    ipfsCache.clearExpired()
    console.log('Expired IPFS metadata cache entries cleared')
  }

  getIPFSCacheStats() {
    return ipfsCache.getCacheStats()
  }

  // Image cache management methods
  clearIPFSImageCache(): void {
    ipfsImageCache.clear()
    console.log('IPFS image cache cleared')
  }

  clearExpiredIPFSImageCache(): void {
    ipfsImageCache.clearExpired()
    console.log('Expired IPFS image cache entries cleared')
  }

  getIPFSImageCacheStats() {
    return ipfsImageCache.getCacheStats()
  }

  clearAllCaches(): void {
    ipfsCache.clear()
    ipfsImageCache.clear()
    console.log('All IPFS caches cleared (metadata + images)')
  }

  clearAllExpiredCaches(): void {
    ipfsCache.clearExpired()
    ipfsImageCache.clearExpired()
    console.log('All expired IPFS cache entries cleared (metadata + images)')
  }
}