'use client'

import { useState, useEffect, useCallback } from 'react'
import { Search, ExternalLink, Youtube, Copy, Share2, RefreshCw, ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { XRPLService, NFTResult, NFTMetadata } from '@/lib/xrpl'
import IPFSImage from '@/components/IPFSImage'
import { CacheHelpers } from '@/lib/cache'

interface VideoData {
  nft_id: string
  title: string
  video_url: string
  thumbnail_url?: string
  channel_title?: string
  published_at?: string | number
  minted_at?: string
  wallet_address?: string
  category?: string
  metadata?: NFTMetadata
  issuer?: string
}

interface PaginationInfo {
  page: number
  limit: number
  total: number
  totalPages: number
  hasNext: boolean
  hasPrev: boolean
}

const VIDEOS_PER_PAGE = 12

export default function VideoGallery() {
  const [videos, setVideos] = useState<VideoData[]>([])
  const [allVideos, setAllVideos] = useState<VideoData[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')
  const [walletAddress, setWalletAddress] = useState<string>('')
  const [xrplService] = useState(() => new XRPLService())
  const [networkUsed, setNetworkUsed] = useState<string>(xrplService.getNetworkName())
  const [isCached, setIsCached] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string | null>(null)
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    limit: VIDEOS_PER_PAGE,
    total: 0,
    totalPages: 0,
    hasNext: false,
    hasPrev: false
  })

  // Load videos on mount
  useEffect(() => {
    loadVideos()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  // Handle search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (isCached) {
        // If cached, fetch from API with search
        fetchFromCache(1, searchTerm)
      } else {
        // If not cached, filter locally
        filterLocalVideos()
      }
    }, 300)

    return () => clearTimeout(timer)
  }, [searchTerm]) // eslint-disable-line react-hooks/exhaustive-deps

  const filterLocalVideos = useCallback(() => {
    if (!searchTerm) {
      const total = allVideos.length
      const totalPages = Math.ceil(total / VIDEOS_PER_PAGE)
      const startIndex = (pagination.page - 1) * VIDEOS_PER_PAGE
      const endIndex = startIndex + VIDEOS_PER_PAGE
      setVideos(allVideos.slice(startIndex, endIndex))
      setPagination(prev => ({
        ...prev,
        total,
        totalPages,
        hasNext: prev.page < totalPages,
        hasPrev: prev.page > 1
      }))
    } else {
      const filtered = allVideos.filter(video =>
        video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        video.channel_title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        video.category?.toLowerCase().includes(searchTerm.toLowerCase())
      )
      const total = filtered.length
      const totalPages = Math.ceil(total / VIDEOS_PER_PAGE)
      setVideos(filtered.slice(0, VIDEOS_PER_PAGE))
      setPagination({
        page: 1,
        limit: VIDEOS_PER_PAGE,
        total,
        totalPages,
        hasNext: totalPages > 1,
        hasPrev: false
      })
    }
  }, [allVideos, searchTerm, pagination.page])

  const fetchFromCache = async (page: number, search: string = '') => {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: VIDEOS_PER_PAGE.toString(),
        ...(search && { search })
      })

      const response = await fetch(`/api/video-cache?${params}`)
      const data = await response.json()

      if (data.success && data.cached) {
        setVideos(data.videos)
        setPagination(data.pagination)
        setIsCached(true)
        setLastUpdated(data.lastUpdated)
        setWalletAddress(data.walletAddress)
      }
    } catch (err) {
      console.error('Error fetching from cache:', err)
    }
  }

  const loadVideos = async () => {
    try {
      setLoading(true)
      setError('')

      // First, try to load from JSON cache
      const response = await fetch('/api/video-cache?page=1&limit=' + VIDEOS_PER_PAGE)
      const cacheData = await response.json()

      if (cacheData.success && cacheData.cached && cacheData.videos.length > 0) {
        // Cache exists, load from it
        console.log('Loading from JSON cache...')
        setVideos(cacheData.videos)
        setPagination(cacheData.pagination)
        setIsCached(true)
        setLastUpdated(cacheData.lastUpdated)
        setWalletAddress(cacheData.walletAddress)
        setLoading(false)
        return
      }

      // No cache, load from XRPL and create cache
      console.log('No cache found, loading from XRPL...')
      const addr = process.env.NEXT_PUBLIC_WALLET_ADDRESS || 'rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp'
      setWalletAddress(addr)
      await loadFromXRPLedger(addr, true)
    } catch (err) {
      console.error('Error loading videos:', err)
      // Fallback to XRPL if cache API fails
      const addr = process.env.NEXT_PUBLIC_WALLET_ADDRESS || 'rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp'
      setWalletAddress(addr)
      await loadFromXRPLedger(addr, true)
    }
  }

  const refreshVideos = async () => {
    try {
      setRefreshing(true)
      setError('')

      // Clear local cache
      CacheHelpers.invalidateWallet(walletAddress)

      const addr = process.env.NEXT_PUBLIC_WALLET_ADDRESS || 'rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp'
      setWalletAddress(addr)

      // Load fresh from XRPL and update cache
      await loadFromXRPLedger(addr, true)
    } catch (err) {
      console.error('Error refreshing videos:', err)
      setError('Failed to refresh videos')
    } finally {
      setRefreshing(false)
    }
  }

  const loadFromXRPLedger = async (address: string, saveToCache: boolean = false) => {
    try {
      setLoading(true)
      setError('')

      console.log(`Loading NFTs from account: ${address}`)

      let allNfts: NFTResult[] = []
      const networkUsedValue = xrplService.getNetworkName()

      // Use cache helper for NFT list with 6-hour cache
      const fetchNFTs = async () => {
        return await xrplService.getAllNFTs(address)
      }

      try {
        allNfts = await CacheHelpers.getNFTList<NFTResult[]>(
          `video_gallery_${address}`,
          fetchNFTs
        )
        console.log(`Found ${allNfts.length} total NFTs (cached or fresh)`)
      } catch (error) {
        console.error('Failed to load NFTs:', error)
        throw new Error(`Account not found: ${address}`)
      }

      setNetworkUsed(networkUsedValue)

      // Enhanced filtering - be more inclusive to catch all possible YouTube NFTs
      const youtubeNfts = allNfts.filter(nft => {
        if (!nft.metadata) {
          return true
        }

        const metadata = nft.metadata

        const hasYouTubeIndicators =
          metadata.video_id ||
          metadata.videoId ||
          metadata.id ||
          metadata.v ||
          metadata.u?.includes('youtube.com') ||
          metadata.u?.includes('youtu.be') ||
          metadata.video_url?.includes('youtube.com') ||
          metadata.video_url?.includes('youtu.be') ||
          metadata.source?.includes('youtube.com') ||
          metadata.source?.includes('youtu.be') ||
          metadata.redirects?.youtube ||
          metadata.name?.toLowerCase().includes('youtube') ||
          metadata.title?.toLowerCase().includes('youtube') ||
          metadata.attributes?.some((attr: { trait_type: string; value: string | number }) =>
            attr.trait_type === 'contextType' && (attr.value === 'YouTube_NFT' || attr.value === 'YouTube')
          ) ||
          metadata.attributes?.some((attr: { trait_type: string; value: string | number }) =>
            attr.trait_type === 'platform' && attr.value === 'YouTube'
          ) ||
          metadata.attributes?.some((attr: { trait_type: string; value: string | number }) =>
            attr.trait_type === 'videoId'
          )

        return hasYouTubeIndicators
      })

      // Process videos
      let videoData: VideoData[]

      if (youtubeNfts.length === 0 && allNfts.length > 0) {
        videoData = allNfts.map(nft => {
          const metadata = nft.metadata || {}
          return {
            nft_id: nft.nft_id,
            title: metadata.name || metadata.title || metadata.n || `NFT ${nft.nft_id.substring(0, 8)}...`,
            video_url: metadata.video_url || metadata.url || metadata.u || metadata.source || '#',
            thumbnail_url: metadata.image || metadata.thumbnail_url || '',
            channel_title: metadata.channel || metadata.channel_title || metadata.c || 'Unknown',
            published_at: metadata.published_at || metadata.p || '',
            minted_at: new Date().toISOString(),
            wallet_address: address,
            category: 'NFT',
            metadata: metadata,
            issuer: nft.issuer
          }
        })
      } else if (allNfts.length === 0) {
        setError('No NFTs found on this account. Please verify the account address.')
        return
      } else {
        videoData = youtubeNfts.map(nft => {
          const metadata = nft.metadata || {}

          const getAttributeValue = (trait_type: string) => {
            if (!metadata.attributes) return null
            const attr = metadata.attributes.find((attr: { trait_type: string; value: string | number }) =>
              attr.trait_type === trait_type ||
              attr.trait_type.toLowerCase() === trait_type.toLowerCase()
            )
            return attr ? attr.value : null
          }

          const videoId = metadata.v || metadata.videoId || metadata.video_id ||
                         metadata.id || getAttributeValue('videoId') ||
                         getAttributeValue('v')

          const thumbnailUrl = metadata.image ||
                             metadata.thumbnail_url ||
                             metadata.redirects?.thumbnail ||
                             (videoId ? `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg` : '') ||
                             getAttributeValue('thumbnail')

          const videoUrl = metadata.u || metadata.video_url || metadata.url ||
                          metadata.source || metadata.redirects?.youtube ||
                          getAttributeValue('source') || getAttributeValue('url') ||
                          (videoId ? `https://www.youtube.com/watch?v=${videoId}` : '')

          const title = metadata.n || metadata.name || metadata.title ||
                       getAttributeValue('title') || getAttributeValue('name') ||
                       'YouTube NFT'

          const publishedAt = metadata.p || metadata.published || metadata.published_at ||
                             metadata.publishedDate || getAttributeValue('publishedDate') ||
                             getAttributeValue('published')

          return {
            nft_id: nft.nft_id,
            title: String(title),
            video_url: String(videoUrl),
            thumbnail_url: thumbnailUrl ? String(thumbnailUrl) : undefined,
            channel_title: String(metadata.c || metadata.channel || metadata.channel_title ||
                          getAttributeValue('channel') || getAttributeValue('creator') || 'Jim Flint'),
            published_at: publishedAt ? (typeof publishedAt === 'number' ?
                         new Date(publishedAt * 1000).toISOString() : String(publishedAt)) : '',
            minted_at: new Date().toISOString(),
            wallet_address: address,
            category: String(metadata.category || getAttributeValue('category') || 'Video'),
            metadata: metadata,
            issuer: nft.issuer
          }
        })
      }

      // Store all videos for local filtering
      setAllVideos(videoData)

      // Apply pagination
      const total = videoData.length
      const totalPages = Math.ceil(total / VIDEOS_PER_PAGE)
      setVideos(videoData.slice(0, VIDEOS_PER_PAGE))
      setPagination({
        page: 1,
        limit: VIDEOS_PER_PAGE,
        total,
        totalPages,
        hasNext: totalPages > 1,
        hasPrev: false
      })

      // Save to JSON cache if requested
      if (saveToCache && videoData.length > 0) {
        try {
          await fetch('/api/video-cache', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ videos: videoData, walletAddress: address })
          })
          setIsCached(true)
          setLastUpdated(new Date().toISOString())
          console.log('Videos saved to JSON cache')
        } catch (err) {
          console.error('Failed to save to cache:', err)
        }
      }

      console.log(`Processed ${videoData.length} video NFTs`)
    } catch (err) {
      console.error('Error loading from XRPL:', err)
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(`Failed to load NFTs from the ledger: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
  }

  const handlePageChange = (newPage: number) => {
    if (newPage < 1 || newPage > pagination.totalPages) return

    if (isCached) {
      fetchFromCache(newPage, searchTerm)
    } else {
      // Local pagination
      const startIndex = (newPage - 1) * VIDEOS_PER_PAGE
      const endIndex = startIndex + VIDEOS_PER_PAGE

      let sourceVideos = allVideos
      if (searchTerm) {
        sourceVideos = allVideos.filter(video =>
          video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          video.channel_title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          video.category?.toLowerCase().includes(searchTerm.toLowerCase())
        )
      }

      setVideos(sourceVideos.slice(startIndex, endIndex))
      setPagination(prev => ({
        ...prev,
        page: newPage,
        hasNext: newPage < prev.totalPages,
        hasPrev: newPage > 1
      }))
    }

    // Scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const getShareUrl = (nftId: string) => {
    if (typeof window !== 'undefined') {
      return `${window.location.origin}/verify/${nftId}`
    }
    return `/verify/${nftId}`
  }

  const copyShareUrl = (nftId: string) => {
    const url = getShareUrl(nftId)
    navigator.clipboard.writeText(url)
    alert('Share URL copied to clipboard!')
  }

  const formatDate = (dateString: string | number | undefined) => {
    if (!dateString) return 'Unknown'

    try {
      const date = typeof dateString === 'number' ? new Date(dateString * 1000) : new Date(dateString)
      if (isNaN(date.getTime())) return 'Invalid date'

      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    } catch {
      return 'Invalid date'
    }
  }

  const formatLastUpdated = (isoString: string | null) => {
    if (!isoString) return null
    try {
      const date = new Date(isoString)
      return date.toLocaleString()
    } catch {
      return null
    }
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto pt-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading videos{isCached ? ' from cache' : ' from XRPL'}...</p>
          <p className="mt-2 text-sm text-gray-500">This may take a moment for large collections (500+ NFTs)</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6 p-4">
      {/* Header */}
      <div className="text-center space-y-4 pt-8">
        <h1 className="text-3xl font-bold text-gray-900">
          Video Gallery
        </h1>
        <p className="text-gray-600 text-lg">
          All verified YouTube videos with their NFT authentication details
        </p>
      </div>

      {/* Search, Refresh, and Load Options */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search videos by title, channel, or category..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            <Button
              onClick={refreshVideos}
              disabled={refreshing}
              variant="outline"
              className="flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>

          {/* Status Info */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex flex-wrap items-center gap-2">
              {/* <Badge variant="outline" className={isCached ? 'text-blue-600 border-blue-200' : 'text-green-600 border-green-200'}>
                {isCached ? 'Loaded from Cache' : 'Loaded from XRPL Ledger'}
              </Badge> */}
              <Badge variant="secondary" className={networkUsed === 'mainnet' ? 'bg-green-100 text-green-800' : ''}>
                {networkUsed === 'mainnet' ? 'Mainnet' : 'Testnet'}
              </Badge>
              {lastUpdated && (
                <span className="text-xs text-gray-500">
                  Last updated: {formatLastUpdated(lastUpdated)}
                </span>
              )}
            </div>
            {walletAddress && (
              <div className="text-xs text-gray-500 font-mono">
                {walletAddress.substring(0, 12)}...{walletAddress.substring(walletAddress.length - 8)}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="text-2xl font-bold text-blue-600">{pagination.total}</div>
            <div className="text-sm text-gray-600">Total Videos</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="text-2xl font-bold text-green-600">{pagination.total}</div>
            <div className="text-sm text-gray-600">Verified NFTs</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="text-2xl font-bold text-purple-600">100%</div>
            <div className="text-sm text-gray-600">No AI Content</div>
          </CardContent>
        </Card>
      </div>

      {/* Video Grid */}
      {videos.length === 0 && searchTerm ? (
        <Card>
          <CardContent className="pt-6 text-center py-12">
            <Search className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              No videos found
            </h3>
            <p className="text-gray-600">
              Try adjusting your search terms
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {videos.map((video) => (
            <Card key={video.nft_id} className="overflow-hidden hover:shadow-lg transition-shadow">
              {/* Thumbnail Preview */}
              {video.thumbnail_url && (
                <div className="aspect-video bg-gray-100 relative overflow-hidden">
                  <IPFSImage
                    src={video.thumbnail_url}
                    alt={video.title}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 right-2">
                    <Youtube className="w-6 h-6 text-white drop-shadow-lg" />
                  </div>
                </div>
              )}

              <CardHeader className="pb-3">
                <CardTitle className="text-lg line-clamp-2">
                  {video.title}
                </CardTitle>
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">Verified</Badge>
                  {video.category && (
                    <Badge variant="outline">{video.category}</Badge>
                  )}
                  {video.channel_title && (
                    <Badge variant="outline" className="text-blue-600 border-blue-200">
                      {video.channel_title}
                    </Badge>
                  )}
                </div>
              </CardHeader>

              <CardContent className="space-y-4">
                {/* NFT ID */}
                <div>
                  <label className="text-xs font-medium text-gray-700 uppercase tracking-wide">
                    NFT Token ID
                  </label>
                  <div className="flex items-center space-x-2 mt-1">
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono flex-1 truncate break-all">
                      {video.nft_id}
                    </code>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => copyToClipboard(video.nft_id)}
                      className="p-1 h-6 w-6 flex-shrink-0"
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  </div>
                </div>

                {/* Share URL */}
                <div>
                  <label className="text-xs font-medium text-gray-700 uppercase tracking-wide">
                    Share Link
                  </label>
                  <div className="flex items-center space-x-2 mt-1">
                    <code className="text-xs bg-blue-50 px-2 py-1 rounded text-blue-600 flex-1 truncate">
                      {getShareUrl(video.nft_id)}
                    </code>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => copyShareUrl(video.nft_id)}
                      className="p-1 h-6 w-6 flex-shrink-0"
                    >
                      <Share2 className="w-3 h-3" />
                    </Button>
                  </div>
                </div>

                {/* Dates */}
                <div className="grid grid-cols-2 gap-2">
                  {video.published_at && (
                    <div>
                      <label className="text-xs font-medium text-gray-700 uppercase tracking-wide">
                        Published
                      </label>
                      <p className="text-sm text-gray-600 mt-1">
                        {formatDate(video.published_at)}
                      </p>
                    </div>
                  )}
                  {video.minted_at && (
                    <div>
                      <label className="text-xs font-medium text-gray-700 uppercase tracking-wide">
                        Minted
                      </label>
                      <p className="text-sm text-gray-600 mt-1">
                        {formatDate(video.minted_at)}
                      </p>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-2">
                  <Button
                    asChild
                    className="w-full"
                    size="sm"
                  >
                    <a
                      href={video.video_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center space-x-2"
                    >
                      <Youtube className="w-4 h-4" />
                      <span>Watch Video</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </Button>

                  <Button
                    asChild
                    variant="outline"
                    size="sm"
                    className="w-full"
                  >
                    <a
                      href={xrplService.getBithompExplorerUrl(video.nft_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center space-x-2"
                    >
                      <span>View NFT</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination.totalPages > 1 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="text-sm text-gray-600">
                Showing {((pagination.page - 1) * pagination.limit) + 1} - {Math.min(pagination.page * pagination.limit, pagination.total)} of {pagination.total} videos
              </div>
              <div className="flex items-center gap-1 sm:gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={!pagination.hasPrev}
                  className="px-2 sm:px-3"
                >
                  <ChevronLeft className="w-4 h-4" />
                  <span className="hidden sm:inline">Previous</span>
                </Button>
                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(3, pagination.totalPages) }, (_, i) => {
                    let pageNum: number
                    if (pagination.totalPages <= 3) {
                      pageNum = i + 1
                    } else if (pagination.page <= 2) {
                      pageNum = i + 1
                    } else if (pagination.page >= pagination.totalPages - 1) {
                      pageNum = pagination.totalPages - 2 + i
                    } else {
                      pageNum = pagination.page - 1 + i
                    }
                    return (
                      <Button
                        key={pageNum}
                        variant={pagination.page === pageNum ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => handlePageChange(pageNum)}
                        className="w-8 h-8 p-0"
                      >
                        {pageNum}
                      </Button>
                    )
                  })}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={!pagination.hasNext}
                  className="px-2 sm:px-3"
                >
                  <span className="hidden sm:inline">Next</span>
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {error && (
        <Card>
          <CardContent className="pt-6 text-center py-8">
            <div className="text-red-600">{error}</div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
