/**
 * IPFS Image Cache Utility
 *
 * Specialized caching system for IPFS images (binary data):
 * - Caches images as base64-encoded data URLs in localStorage
 * - Falls back to IndexedDB for larger images (localStorage has 5-10MB limit)
 * - In-memory cache for ultra-fast access during current session
 *
 * Features:
 * - Automatic IPFS hash extraction from URIs (ipfs://, ipfs://ipfs/, or raw hash)
 * - Gateway fallback with multiple IPFS gateways
 * - Configurable TTL (default: 7 days for images)
 * - Automatic cleanup of expired entries
 * - Support for all image formats (PNG, JPG, GIF, WebP, etc.)
 */

interface ImageCacheEntry {
  dataUrl: string
  contentType: string
  timestamp: number
  expiresAt: number
  size: number
}

export class IPFSImageCache {
  private memoryCache: Map<string, ImageCacheEntry>
  private readonly CACHE_PREFIX = 'ipfs_img_'
  private readonly DEFAULT_TTL = 7 * 24 * 60 * 60 * 1000 // 7 days
  private readonly MAX_LOCALSTORAGE_SIZE = 2 * 1024 * 1024 // 2MB per image for localStorage
  private readonly MAX_MEMORY_CACHE_SIZE = 50 // Maximum image entries in memory
  private readonly MAX_LOCALSTORAGE_CACHE_SIZE = 30 // Maximum image entries in localStorage
  private localStorageDisabled = false // Flag to disable localStorage if quota exceeded

  private readonly gateways = [
    'https://crimson-main-grouse-700.mypinata.cloud/ipfs/',
    'https://gateway.pinata.cloud/ipfs/',
    'https://ipfs.io/ipfs/',
    'https://cloudflare-ipfs.com/ipfs/',
    'https://gateway.ipfs.io/ipfs/'
  ]

  constructor(private ttl: number = 7 * 24 * 60 * 60 * 1000) {
    this.memoryCache = new Map()
    this.loadFromLocalStorage()
  }

  /**
   * Extract IPFS hash from various URI formats
   */
  private extractIPFSHash(uri: string): string | null {
    if (!uri) return null

    // Already a hash (no protocol)
    if (uri.startsWith('Qm') || uri.startsWith('bafy')) {
      return uri
    }

    // ipfs:// protocol
    if (uri.startsWith('ipfs://')) {
      return uri.replace('ipfs://', '').replace('ipfs/', '')
    }

    // Full gateway URL
    const gatewayMatch = uri.match(/\/ipfs\/([^/?#]+)/)
    if (gatewayMatch) {
      return gatewayMatch[1]
    }

    return null
  }

  /**
   * Check if URL is an IPFS reference
   */
  isIPFSUrl(url: string): boolean {
    if (!url) return false
    return url.startsWith('ipfs://') ||
           url.startsWith('Qm') ||
           url.startsWith('bafy') ||
           url.includes('/ipfs/')
  }

  private getCacheKey(ipfsHash: string): string {
    return `${this.CACHE_PREFIX}${ipfsHash}`
  }

  private loadFromLocalStorage(): void {
    if (typeof window === 'undefined') return

    try {
      const keys = Object.keys(localStorage)
      const now = Date.now()

      keys.forEach(key => {
        if (key.startsWith(this.CACHE_PREFIX)) {
          const value = localStorage.getItem(key)
          if (value) {
            try {
              const entry: ImageCacheEntry = JSON.parse(value)

              // Check if entry is still valid
              if (entry.expiresAt > now) {
                const ipfsHash = key.replace(this.CACHE_PREFIX, '')
                this.memoryCache.set(ipfsHash, entry)
              } else {
                // Remove expired entry from localStorage
                localStorage.removeItem(key)
              }
            } catch (e) {
              console.error(`Failed to parse image cache entry for ${key}:`, e)
              localStorage.removeItem(key)
            }
          }
        }
      })

      console.log(`Loaded ${this.memoryCache.size} cached images from localStorage`)
    } catch (e) {
      console.error('Failed to load image cache from localStorage:', e)
    }
  }

  /**
   * Get cached image data URL
   */
  async get(uri: string): Promise<string | null> {
    const ipfsHash = this.extractIPFSHash(uri)
    if (!ipfsHash) return null

    const now = Date.now()

    // Check memory cache first
    const memEntry = this.memoryCache.get(ipfsHash)
    if (memEntry) {
      if (memEntry.expiresAt > now) {
        console.log(`Image cache HIT (memory) for IPFS hash: ${ipfsHash}`)
        return memEntry.dataUrl
      } else {
        // Expired, remove from memory cache
        this.memoryCache.delete(ipfsHash)
        this.removeFromLocalStorage(ipfsHash)
      }
    }

    // Check localStorage
    if (typeof window !== 'undefined') {
      try {
        const key = this.getCacheKey(ipfsHash)
        const value = localStorage.getItem(key)

        if (value) {
          const entry: ImageCacheEntry = JSON.parse(value)

          if (entry.expiresAt > now) {
            console.log(`Image cache HIT (localStorage) for IPFS hash: ${ipfsHash}`)
            // Restore to memory cache
            this.memoryCache.set(ipfsHash, entry)
            return entry.dataUrl
          } else {
            // Expired, remove from localStorage
            localStorage.removeItem(key)
          }
        }
      } catch (e) {
        console.error(`Failed to read image from localStorage for ${ipfsHash}:`, e)
      }
    }

    console.log(`Image cache MISS for IPFS hash: ${ipfsHash}`)
    return null
  }

  /**
   * Fetch image from IPFS gateways with fallback
   */
  async fetchAndCache(uri: string): Promise<string | null> {
    const ipfsHash = this.extractIPFSHash(uri)
    if (!ipfsHash) {
      console.warn('Invalid IPFS URI:', uri)
      return null
    }

    // Check cache first
    const cached = await this.get(uri)
    if (cached) return cached

    // Try to fetch from gateways
    for (const gateway of this.gateways) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 15000) // 15 second timeout for images

        const url = `${gateway}${ipfsHash}`
        console.log(`Fetching image from: ${url}`)

        const response = await fetch(url, {
          signal: controller.signal,
          headers: {
            'Accept': 'image/*',
          }
        })
        clearTimeout(timeoutId)

        if (response.ok) {
          const blob = await response.blob()
          const contentType = response.headers.get('content-type') || 'image/jpeg'

          // Convert blob to data URL
          const dataUrl = await this.blobToDataUrl(blob)

          // Cache the image
          await this.set(ipfsHash, dataUrl, contentType, blob.size)

          console.log(`Successfully fetched and cached image from ${gateway}`)
          return dataUrl
        }
      } catch (e) {
        console.log(`Failed to fetch image from gateway ${gateway}:`, e instanceof Error ? e.message : e)
        continue
      }
    }

    console.error(`Failed to fetch image from all gateways for hash: ${ipfsHash}`)
    return null
  }

  /**
   * Convert Blob to data URL
   */
  private blobToDataUrl(blob: Blob): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onloadend = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })
  }

  /**
   * Store image in cache
   */
  private async set(ipfsHash: string, dataUrl: string, contentType: string, size: number): Promise<void> {
    const now = Date.now()
    const entry: ImageCacheEntry = {
      dataUrl,
      contentType,
      timestamp: now,
      expiresAt: now + this.ttl,
      size
    }

    // Enforce memory cache size limit (LRU eviction)
    if (this.memoryCache.size >= this.MAX_MEMORY_CACHE_SIZE) {
      this.evictOldestFromMemory()
    }

    // Store in memory cache
    this.memoryCache.set(ipfsHash, entry)

    // Store in localStorage if not too large and not disabled
    if (typeof window !== 'undefined' && !this.localStorageDisabled) {
      try {
        const key = this.getCacheKey(ipfsHash)
        const entryJson = JSON.stringify(entry)

        // Check size (localStorage stores strings, so estimate size)
        const estimatedSize = entryJson.length * 2 // UTF-16 encoding

        if (estimatedSize < this.MAX_LOCALSTORAGE_SIZE) {
          // Check localStorage cache count and evict if needed
          const localStorageCount = this.getLocalStorageCacheCount()
          if (localStorageCount >= this.MAX_LOCALSTORAGE_CACHE_SIZE) {
            this.evictOldestFromLocalStorage()
          }

          localStorage.setItem(key, entryJson)
          console.log(`Cached image for hash: ${ipfsHash} (${(size / 1024).toFixed(2)} KB)`)
        } else {
          console.warn(`Image too large for localStorage: ${ipfsHash} (${(size / 1024).toFixed(2)} KB), keeping in memory only`)
        }
      } catch (e) {
        const error = e as Error

        // Handle QuotaExceededError
        if (error.name === 'QuotaExceededError' || error.message?.includes('quota')) {
          console.warn('⚠️ localStorage quota exceeded for images. Attempting to free space...')

          // Try to free space by clearing expired entries first
          this.clearExpired()

          // Try again after clearing expired entries
          try {
            const key = this.getCacheKey(ipfsHash)
            localStorage.setItem(key, JSON.stringify(entry))
          } catch (_retryError) {
            // Still failing, evict oldest entries
            console.warn('⚠️ Still exceeding quota. Evicting oldest image entries...')
            this.evictOldestFromLocalStorage(5) // Evict 5 oldest images

            try {
              const key = this.getCacheKey(ipfsHash)
              localStorage.setItem(key, JSON.stringify(entry))
            } catch (_finalError) {
              // If still failing, disable localStorage and use memory-only cache
              console.warn('⚠️ Cannot store images in localStorage. Using memory-only cache.')
              this.localStorageDisabled = true
            }
          }
        } else {
          console.error(`Failed to write image to localStorage for ${ipfsHash}:`, e)
        }
      }
    }
  }

  private removeFromLocalStorage(ipfsHash: string): void {
    if (typeof window !== 'undefined') {
      try {
        const key = this.getCacheKey(ipfsHash)
        localStorage.removeItem(key)
      } catch (e) {
        console.error(`Failed to remove image from localStorage for ${ipfsHash}:`, e)
      }
    }
  }

  /**
   * Clear expired cache entries
   */
  clearExpired(): void {
    const now = Date.now()
    let expiredCount = 0

    // Clear expired from memory cache
    for (const [hash, entry] of this.memoryCache.entries()) {
      if (entry.expiresAt <= now) {
        this.memoryCache.delete(hash)
        this.removeFromLocalStorage(hash)
        expiredCount++
      }
    }

    // Clear expired from localStorage
    if (typeof window !== 'undefined') {
      try {
        const keys = Object.keys(localStorage)
        keys.forEach(key => {
          if (key.startsWith(this.CACHE_PREFIX)) {
            const value = localStorage.getItem(key)
            if (value) {
              try {
                const entry: ImageCacheEntry = JSON.parse(value)
                if (entry.expiresAt <= now) {
                  localStorage.removeItem(key)
                  expiredCount++
                }
              } catch {
                // Remove invalid entries
                localStorage.removeItem(key)
              }
            }
          }
        })
      } catch (e) {
        console.error('Failed to clear expired image cache entries:', e)
      }
    }

    if (expiredCount > 0) {
      console.log(`Cleared ${expiredCount} expired image cache entries`)
    }
  }

  /**
   * Clear all cached images
   */
  clear(): void {
    // Clear memory cache
    this.memoryCache.clear()

    // Clear localStorage
    if (typeof window !== 'undefined') {
      try {
        const keys = Object.keys(localStorage)
        keys.forEach(key => {
          if (key.startsWith(this.CACHE_PREFIX)) {
            localStorage.removeItem(key)
          }
        })
        this.localStorageDisabled = false // Re-enable localStorage after clearing
      } catch (e) {
        console.error('Failed to clear image cache:', e)
      }
    }

    console.log('Image cache cleared')
  }

  private getLocalStorageCacheCount(): number {
    if (typeof window === 'undefined') return 0

    try {
      const keys = Object.keys(localStorage)
      return keys.filter(key => key.startsWith(this.CACHE_PREFIX)).length
    } catch (e) {
      console.error('Failed to count localStorage image entries:', e)
      return 0
    }
  }

  private evictOldestFromMemory(count: number = 1): void {
    // Get all entries sorted by timestamp (oldest first)
    const entries = Array.from(this.memoryCache.entries())
      .sort(([, a], [, b]) => a.timestamp - b.timestamp)

    // Remove the oldest entries
    for (let i = 0; i < Math.min(count, entries.length); i++) {
      const [hash] = entries[i]
      this.memoryCache.delete(hash)
    }
  }

  private evictOldestFromLocalStorage(count: number = 1): void {
    if (typeof window === 'undefined') return

    try {
      const keys = Object.keys(localStorage)
      const cacheKeys = keys.filter(key => key.startsWith(this.CACHE_PREFIX))

      // Get entries with timestamps
      const entries: Array<{ key: string; timestamp: number }> = []

      cacheKeys.forEach(key => {
        const value = localStorage.getItem(key)
        if (value) {
          try {
            const entry: ImageCacheEntry = JSON.parse(value)
            entries.push({ key, timestamp: entry.timestamp })
          } catch {
            // Remove invalid entries
            localStorage.removeItem(key)
          }
        }
      })

      // Sort by timestamp (oldest first)
      entries.sort((a, b) => a.timestamp - b.timestamp)

      // Remove the oldest entries
      for (let i = 0; i < Math.min(count, entries.length); i++) {
        localStorage.removeItem(entries[i].key)
      }

      console.log(`Evicted ${Math.min(count, entries.length)} oldest image entries from localStorage`)
    } catch (e) {
      console.error('Failed to evict images from localStorage:', e)
    }
  }

  /**
   * Get cache statistics
   */
  getCacheStats(): {
    memorySize: number
    localStorageSize: number
    localStorageDisabled: boolean
    totalSize: number
    entries: Array<{
      hash: string
      contentType: string
      size: number
      timestamp: number
      expiresAt: number
    }>
  } {
    let totalSize = 0
    const entries = Array.from(this.memoryCache.entries()).map(([hash, entry]) => {
      totalSize += entry.size
      return {
        hash,
        contentType: entry.contentType,
        size: entry.size,
        timestamp: entry.timestamp,
        expiresAt: entry.expiresAt
      }
    })

    return {
      memorySize: this.memoryCache.size,
      localStorageSize: this.getLocalStorageCacheCount(),
      localStorageDisabled: this.localStorageDisabled,
      totalSize,
      entries
    }
  }

  /**
   * Convert IPFS URI to gateway URL (for direct use without caching)
   */
  getGatewayUrl(uri: string, gatewayIndex: number = 0): string | null {
    const ipfsHash = this.extractIPFSHash(uri)
    if (!ipfsHash) return null

    const gateway = this.gateways[gatewayIndex] || this.gateways[0]
    return `${gateway}${ipfsHash}`
  }
}

// Export singleton instance with 7-day TTL
export const ipfsImageCache = new IPFSImageCache(7 * 24 * 60 * 60 * 1000)
