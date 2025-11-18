/**
 * IPFS Cache Utility
 *
 * Dual-layer caching system for IPFS content fetched from Pinata:
 * - Layer 1: In-memory cache (Map) for fast access during current session
 * - Layer 2: localStorage for persistence across browser sessions
 *
 * Features:
 * - Automatic expiration with configurable TTL (default: 24 hours)
 * - Automatic cleanup of expired entries
 * - Fallback from memory to localStorage
 * - Cache statistics for monitoring
 *
 * Usage:
 * - Cache is automatically checked before fetching from IPFS gateways
 * - Successfully fetched data is automatically cached
 * - Use XRPLService methods to manage cache:
 *   - clearIPFSCache() - Clear all cached data
 *   - clearExpiredIPFSCache() - Remove only expired entries
 *   - getIPFSCacheStats() - View cache statistics
 */

import { NFTMetadata } from './xrpl'

interface CacheEntry<T> {
  data: T
  timestamp: number
  expiresAt: number
}

export class IPFSCache {
  private memoryCache: Map<string, CacheEntry<NFTMetadata>>
  private readonly CACHE_PREFIX = 'ipfs_cache_'
  private readonly DEFAULT_TTL = 24 * 60 * 60 * 1000 // 24 hours in milliseconds
  private readonly MAX_MEMORY_CACHE_SIZE = 200 // Maximum entries in memory
  private readonly MAX_LOCALSTORAGE_SIZE = 100 // Maximum entries in localStorage
  private localStorageDisabled = false // Flag to disable localStorage if quota exceeded

  constructor(private ttl: number = 24 * 60 * 60 * 1000) {
    this.memoryCache = new Map()
    this.loadFromLocalStorage()
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
              const entry: CacheEntry<NFTMetadata> = JSON.parse(value)

              // Check if entry is still valid
              if (entry.expiresAt > now) {
                const ipfsHash = key.replace(this.CACHE_PREFIX, '')
                this.memoryCache.set(ipfsHash, entry)
              } else {
                // Remove expired entry from localStorage
                localStorage.removeItem(key)
              }
            } catch (e) {
              console.error(`Failed to parse cache entry for ${key}:`, e)
              localStorage.removeItem(key)
            }
          }
        }
      })
    } catch (e) {
      console.error('Failed to load cache from localStorage:', e)
    }
  }

  get(ipfsHash: string): NFTMetadata | null {
    const now = Date.now()

    // Check memory cache first
    const memEntry = this.memoryCache.get(ipfsHash)
    if (memEntry) {
      if (memEntry.expiresAt > now) {
        console.log(`Cache HIT (memory) for IPFS hash: ${ipfsHash}`)
        return memEntry.data
      } else {
        // Expired, remove from memory cache
        this.memoryCache.delete(ipfsHash)
        this.removeFromLocalStorage(ipfsHash)
      }
    }

    // Check localStorage as fallback
    if (typeof window !== 'undefined') {
      try {
        const key = this.getCacheKey(ipfsHash)
        const value = localStorage.getItem(key)

        if (value) {
          const entry: CacheEntry<NFTMetadata> = JSON.parse(value)

          if (entry.expiresAt > now) {
            console.log(`Cache HIT (localStorage) for IPFS hash: ${ipfsHash}`)
            // Restore to memory cache
            this.memoryCache.set(ipfsHash, entry)
            return entry.data
          } else {
            // Expired, remove from localStorage
            localStorage.removeItem(key)
          }
        }
      } catch (e) {
        console.error(`Failed to read from localStorage for ${ipfsHash}:`, e)
      }
    }

    console.log(`Cache MISS for IPFS hash: ${ipfsHash}`)
    return null
  }

  set(ipfsHash: string, data: NFTMetadata): void {
    const now = Date.now()
    const entry: CacheEntry<NFTMetadata> = {
      data,
      timestamp: now,
      expiresAt: now + this.ttl
    }

    // Enforce memory cache size limit (LRU eviction)
    if (this.memoryCache.size >= this.MAX_MEMORY_CACHE_SIZE) {
      this.evictOldestFromMemory()
    }

    // Store in memory cache
    this.memoryCache.set(ipfsHash, entry)

    // Store in localStorage (if not disabled)
    if (typeof window !== 'undefined' && !this.localStorageDisabled) {
      try {
        // Check localStorage size and evict if needed
        const localStorageCount = this.getLocalStorageCacheCount()
        if (localStorageCount >= this.MAX_LOCALSTORAGE_SIZE) {
          this.evictOldestFromLocalStorage()
        }

        const key = this.getCacheKey(ipfsHash)
        localStorage.setItem(key, JSON.stringify(entry))
      } catch (e) {
        const error = e as Error

        // Handle QuotaExceededError
        if (error.name === 'QuotaExceededError' || error.message?.includes('quota')) {
          console.warn('⚠️ localStorage quota exceeded. Attempting to free space...')

          // Try to free space by clearing expired entries first
          this.clearExpired()

          // Try again after clearing expired entries
          try {
            const key = this.getCacheKey(ipfsHash)
            localStorage.setItem(key, JSON.stringify(entry))
          } catch (_retryError) {
            // Still failing, evict oldest entries
            console.warn('⚠️ Still exceeding quota. Evicting oldest entries...')
            this.evictOldestFromLocalStorage(10) // Evict 10 oldest entries

            try {
              const key = this.getCacheKey(ipfsHash)
              localStorage.setItem(key, JSON.stringify(entry))
            } catch (_finalError) {
              // If still failing, disable localStorage and use memory-only cache
              console.warn('⚠️ Cannot store in localStorage. Using memory-only cache.')
              this.localStorageDisabled = true
            }
          }
        } else {
          console.error(`Failed to write to localStorage for ${ipfsHash}:`, e)
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
        console.error(`Failed to remove from localStorage for ${ipfsHash}:`, e)
      }
    }
  }

  clearExpired(): void {
    const now = Date.now()

    // Clear expired from memory cache
    for (const [hash, entry] of this.memoryCache.entries()) {
      if (entry.expiresAt <= now) {
        this.memoryCache.delete(hash)
        this.removeFromLocalStorage(hash)
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
                const entry: CacheEntry<NFTMetadata> = JSON.parse(value)
                if (entry.expiresAt <= now) {
                  localStorage.removeItem(key)
                }
              } catch {
                // Remove invalid entries
                localStorage.removeItem(key)
              }
            }
          }
        })
      } catch (e) {
        console.error('Failed to clear expired cache entries:', e)
      }
    }
  }

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
        console.error('Failed to clear cache:', e)
      }
    }
  }

  private getLocalStorageCacheCount(): number {
    if (typeof window === 'undefined') return 0

    try {
      const keys = Object.keys(localStorage)
      return keys.filter(key => key.startsWith(this.CACHE_PREFIX)).length
    } catch (e) {
      console.error('Failed to count localStorage entries:', e)
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
            const entry: CacheEntry<NFTMetadata> = JSON.parse(value)
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

      console.log(`Evicted ${Math.min(count, entries.length)} oldest entries from localStorage`)
    } catch (e) {
      console.error('Failed to evict from localStorage:', e)
    }
  }

  getCacheStats(): {
    memorySize: number
    localStorageSize: number
    localStorageDisabled: boolean
    entries: Array<{ hash: string; timestamp: number; expiresAt: number }>
  } {
    const entries = Array.from(this.memoryCache.entries()).map(([hash, entry]) => ({
      hash,
      timestamp: entry.timestamp,
      expiresAt: entry.expiresAt
    }))

    return {
      memorySize: this.memoryCache.size,
      localStorageSize: this.getLocalStorageCacheCount(),
      localStorageDisabled: this.localStorageDisabled,
      entries
    }
  }
}

// Export singleton instance with 24-hour TTL
export const ipfsCache = new IPFSCache(24 * 60 * 60 * 1000)
