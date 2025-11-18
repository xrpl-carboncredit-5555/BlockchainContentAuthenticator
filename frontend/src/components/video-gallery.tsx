'use client'

import { useState, useEffect } from 'react'
import { Search, ExternalLink, Youtube, Copy, Share2 } from 'lucide-react'
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

export default function VideoGallery() {
  const [videos, setVideos] = useState<VideoData[]>([])
  const [filteredVideos, setFilteredVideos] = useState<VideoData[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [walletAddress, setWalletAddress] = useState<string>('')
  const [xrplService] = useState(() => new XRPLService()) // Uses NEXT_PUBLIC_XRPL_NETWORK env variable
  const [networkUsed, setNetworkUsed] = useState<string>(xrplService.getNetworkName())

  useEffect(() => {
    loadVideos()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const filtered = videos.filter(video =>
      video.title.toLowerCase().includes(searchTerm.toLowerCase())
    )
    setFilteredVideos(filtered)
  }, [searchTerm, videos])

  const loadVideos = async () => {
    try {
      // Use the actual wallet address
      const addr = process.env.NEXT_PUBLIC_WALLET_ADDRESS || 'rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp'
      setWalletAddress(addr)

      // Always load directly from XRPL ledger
      await loadFromXRPLedger(addr)
    } catch (err) {
      console.error('Error loading videos:', err)
      setError('Failed to load videos from ledger')
    } finally {
      setLoading(false)
    }
  }

  const loadFromXRPLedger = async (address: string) => {
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

      console.log('All NFTs:', allNfts)

      // Log each NFT's metadata for debugging
      allNfts.forEach((nft, index) => {
        console.log(`NFT ${index + 1}:`, {
          id: nft.nft_id,
          hasMetadata: !!nft.metadata,
          metadata: nft.metadata
        })
      })

      // Enhanced filtering - be more inclusive to catch all possible YouTube NFTs
      const youtubeNfts = allNfts.filter(nft => {
        if (!nft.metadata) {
          console.log(`NFT ${nft.nft_id} has no metadata, checking if it should be included anyway`)
          // Include NFTs without metadata for now to debug
          return true
        }

        const metadata = nft.metadata

        // Check various indicators that this is a YouTube NFT
        const hasYouTubeIndicators =
          metadata.video_id ||
          metadata.videoId ||
          metadata.id ||
          metadata.v || // compact format video ID
          metadata.u?.includes('youtube.com') || // compact format URL
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

        console.log(`NFT ${nft.nft_id} YouTube indicators:`, hasYouTubeIndicators)
        return hasYouTubeIndicators
      })

      console.log(`Found ${youtubeNfts.length} YouTube NFTs`)

      // Don't error out if no YouTube NFTs found, show all NFTs for debugging
      if (youtubeNfts.length === 0 && allNfts.length > 0) {
        console.log('No YouTube NFTs detected, showing all NFTs for debugging')
        // Use all NFTs if no YouTube-specific ones are found
        const allAsVideo = allNfts.map(nft => {
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
        setVideos(allAsVideo)
        return
      }

      if (allNfts.length === 0) {
        setError('No NFTs found on this account. Please verify the account address.')
        return
      }

      // Transform NFT data to VideoData format with comprehensive metadata extraction
      const videoData: VideoData[] = youtubeNfts.map(nft => {
        const metadata = nft.metadata || {}

        // Enhanced attribute extraction
        const getAttributeValue = (trait_type: string) => {
          if (!metadata.attributes) return null
          const attr = metadata.attributes.find((attr: { trait_type: string; value: string | number }) =>
            attr.trait_type === trait_type ||
            attr.trait_type.toLowerCase() === trait_type.toLowerCase()
          )
          return attr ? attr.value : null
        }

        // Enhanced video ID extraction
        const videoId = metadata.v || metadata.videoId || metadata.video_id ||
                       metadata.id || getAttributeValue('videoId') ||
                       getAttributeValue('v')

        // Enhanced thumbnail URL extraction
        const thumbnailUrl = metadata.image ||
                           metadata.thumbnail_url ||
                           metadata.redirects?.thumbnail ||
                           (videoId ? `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg` : '') ||
                           getAttributeValue('thumbnail')

        // Enhanced video URL extraction
        const videoUrl = metadata.u || metadata.video_url || metadata.url ||
                        metadata.source || metadata.redirects?.youtube ||
                        getAttributeValue('source') || getAttributeValue('url') ||
                        (videoId ? `https://www.youtube.com/watch?v=${videoId}` : '')

        // Enhanced title extraction
        const title = metadata.n || metadata.name || metadata.title ||
                     getAttributeValue('title') || getAttributeValue('name') ||
                     'YouTube NFT'

        // Enhanced published date extraction
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

      console.log(`Processed ${videoData.length} video NFTs`)
      setVideos(videoData)
    } catch (err) {
      console.error('Error loading from XRPL:', err)
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred'
      setError(`Failed to load NFTs from the ledger: ${errorMessage}`)
    } finally {
      setLoading(false)
    }
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

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto pt-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading videos from XRPL...</p>
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

      {/* Search and Load Options */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <Input
              placeholder="Search videos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Wallet Info */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Badge variant="outline" className="text-green-600 border-green-200">
                Loading from XRPL Ledger
              </Badge>
              <Badge variant="secondary" className={networkUsed === 'mainnet' ? 'bg-green-100 text-green-800' : ''}>
                {networkUsed === 'mainnet' ? 'Mainnet' : 'Testnet'}
              </Badge>
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
            <div className="text-2xl font-bold text-blue-600">{videos.length}</div>
            <div className="text-sm text-gray-600">Total Videos</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6 text-center">
            <div className="text-2xl font-bold text-green-600">{videos.length}</div>
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
      {filteredVideos.length === 0 && searchTerm ? (
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
          {filteredVideos.map((video) => (
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