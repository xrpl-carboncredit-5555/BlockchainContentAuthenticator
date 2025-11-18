// Cache utility for IPFS metadata and NFT data
interface CacheEntry<T> {
  data: T
  timestamp: number
  expiresAt: number
}

class CacheManager {
  private cache: Map<string, CacheEntry<unknown>> = new Map()
  private readonly DEFAULT_TTL = 6 * 60 * 60 * 1000 // 6 hours in milliseconds

  /**
   * Set a value in the cache with optional TTL (Time To Live)
   * @param key Cache key
   * @param data Data to cache
   * @param ttl Time to live in milliseconds (default: 6 hours)
   */
  set<T>(key: string, data: T, ttl: number = this.DEFAULT_TTL): void {
    const timestamp = Date.now()
    const expiresAt = timestamp + ttl
    this.cache.set(key, { data, timestamp, expiresAt })

    // Store in localStorage for persistence
    if (typeof window !== 'undefined') {
      try {
        const cacheData = {
          data,
          timestamp,
          expiresAt
        }
        localStorage.setItem(`cache_${key}`, JSON.stringify(cacheData))
      } catch (error) {
        console.warn('Failed to store in localStorage:', error)
      }
    }
  }

  /**
   * Get a value from the cache
   * @param key Cache key
   * @returns Cached data or null if not found or expired
   */
  get<T>(key: string): T | null {
    // Try memory cache first
    let entry = this.cache.get(key) as CacheEntry<T> | undefined

    // If not in memory, try localStorage
    if (!entry && typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem(`cache_${key}`)
        if (stored) {
          entry = JSON.parse(stored) as CacheEntry<T>
          // Restore to memory cache
          if (entry) {
            this.cache.set(key, entry)
          }
        }
      } catch (error) {
        console.warn('Failed to read from localStorage:', error)
      }
    }

    if (!entry) {
      return null
    }

    // Check if expired
    if (Date.now() > entry.expiresAt) {
      this.delete(key)
      return null
    }

    return entry.data as T
  }

  /**
   * Check if a key exists and is not expired
   * @param key Cache key
   * @returns true if key exists and is valid
   */
  has(key: string): boolean {
    return this.get(key) !== null
  }

  /**
   * Delete a key from the cache
   * @param key Cache key
   */
  delete(key: string): void {
    this.cache.delete(key)
    if (typeof window !== 'undefined') {
      try {
        localStorage.removeItem(`cache_${key}`)
      } catch (error) {
        console.warn('Failed to remove from localStorage:', error)
      }
    }
  }

  /**
   * Clear all cache entries
   */
  clear(): void {
    this.cache.clear()
    if (typeof window !== 'undefined') {
      try {
        const keys = Object.keys(localStorage)
        keys.forEach(key => {
          if (key.startsWith('cache_')) {
            localStorage.removeItem(key)
          }
        })
      } catch (error) {
        console.warn('Failed to clear localStorage:', error)
      }
    }
  }

  /**
   * Get cache statistics
   */
  getStats(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    }
  }

  /**
   * Remove expired entries
   */
  cleanup(): void {
    const now = Date.now()
    const keysToDelete: string[] = []

    this.cache.forEach((entry, key) => {
      if (now > entry.expiresAt) {
        keysToDelete.push(key)
      }
    })

    keysToDelete.forEach(key => this.delete(key))
  }
}

// Create a singleton instance
export const cache = new CacheManager()

// Auto cleanup every hour
if (typeof window !== 'undefined') {
  setInterval(() => {
    cache.cleanup()
  }, 60 * 60 * 1000) // 1 hour

  // Expose cache utilities to window for debugging
  // Usage in browser console: window.clearNFTCache()
  interface WindowWithCache extends Window {
    clearNFTCache?: () => void
    clearWalletCache?: (address: string) => void
    getCacheStats?: () => { size: number; keys: string[] }
  }

  const windowWithCache = window as WindowWithCache
  windowWithCache.clearNFTCache = () => {
    cache.clear()
    console.log('✅ All NFT caches cleared! Refresh the page to fetch fresh data.')
  }
  windowWithCache.clearWalletCache = (address: string) => {
    CacheHelpers.invalidateWallet(address)
    console.log(`✅ Cache cleared for wallet: ${address}`)
  }
  windowWithCache.getCacheStats = () => {
    const stats = cache.getStats()
    console.log('📊 Cache Statistics:', stats)
    return stats
  }

  console.log('💡 Cache utilities available:')
  console.log('  - window.clearNFTCache() - Clear all caches')
  console.log('  - window.clearWalletCache(address) - Clear specific wallet cache')
  console.log('  - window.getCacheStats() - View cache statistics')
}

// Cache key generators
export const CacheKeys = {
  ipfsMetadata: (url: string) => `ipfs_metadata_${url}`,
  nftData: (nftId: string) => `nft_data_${nftId}`,
  nftList: (walletAddress: string) => `nft_list_${walletAddress}`,
  videoGallery: (walletAddress: string) => `video_gallery_${walletAddress}`,
}

// Typed cache helpers
export const CacheHelpers = {
  /**
   * Get or fetch IPFS metadata with caching
   */
  async getIPFSMetadata<T>(
    url: string,
    fetcher: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cacheKey = CacheKeys.ipfsMetadata(url)
    const cached = cache.get<T>(cacheKey)

    if (cached !== null) {
      console.log('Cache hit for IPFS metadata:', url)
      return cached
    }

    console.log('Cache miss for IPFS metadata, fetching:', url)
    const data = await fetcher()
    cache.set(cacheKey, data, ttl)
    return data
  },

  /**
   * Get or fetch NFT data with caching
   */
  async getNFTData<T>(
    nftId: string,
    fetcher: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cacheKey = CacheKeys.nftData(nftId)
    const cached = cache.get<T>(cacheKey)

    if (cached !== null) {
      console.log('Cache hit for NFT:', nftId)
      return cached
    }

    console.log('Cache miss for NFT, fetching:', nftId)
    const data = await fetcher()
    cache.set(cacheKey, data, ttl)
    return data
  },

  /**
   * Get or fetch NFT list with caching
   */
  async getNFTList<T>(
    walletAddress: string,
    fetcher: () => Promise<T>,
    ttl?: number
  ): Promise<T> {
    const cacheKey = CacheKeys.nftList(walletAddress)
    const cached = cache.get<T>(cacheKey)

    if (cached !== null) {
      console.log('Cache hit for NFT list:', walletAddress)
      return cached
    }

    console.log('Cache miss for NFT list, fetching:', walletAddress)
    const data = await fetcher()
    cache.set(cacheKey, data, ttl)
    return data
  },

  /**
   * Invalidate (clear) cache for a specific NFT
   */
  invalidateNFT(nftId: string): void {
    const cacheKey = CacheKeys.nftData(nftId)
    cache.delete(cacheKey)
    console.log('Invalidated cache for NFT:', nftId)
  },

  /**
   * Invalidate (clear) cache for a wallet's NFT list
   */
  invalidateWallet(walletAddress: string): void {
    cache.delete(CacheKeys.nftList(walletAddress))
    cache.delete(CacheKeys.videoGallery(walletAddress))
    console.log('Invalidated cache for wallet:', walletAddress)
  },

  /**
   * Clear all NFT-related caches
   */
  clearAllNFTCaches(): void {
    cache.clear()
    console.log('Cleared all NFT caches')
  },
}
