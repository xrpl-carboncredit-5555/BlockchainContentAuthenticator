'use client'

import { useState } from 'react'
import { Search, ExternalLink, CheckCircle, AlertCircle, Youtube, Share2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { XRPLService, NFTMetadata } from '@/lib/xrpl'
import IPFSImage from '@/components/IPFSImage'
import { CacheHelpers } from '@/lib/cache'

interface NFTData {
  nft_id: string
  metadata: NFTMetadata | null
  issuer: string
  flags: number
}

export default function NFTVerifier() {
  const [nftId, setNftId] = useState('')
  const [loading, setLoading] = useState(false)
  const [nftData, setNftData] = useState<NFTData | null>(null)
  const [error, setError] = useState('')

  const xrplService = new XRPLService() // Uses NEXT_PUBLIC_XRPL_NETWORK env variable

  const handleVerify = async () => {
    if (!nftId.trim()) {
      setError('Please enter an NFT ID')
      return
    }

    // Basic NFT ID format validation
    if (nftId.length < 32) {
      setError('Invalid NFT ID format. Please enter a valid NFT Token ID.')
      return
    }

    setLoading(true)
    setError('')
    setNftData(null)

    try {
      // Use the actual wallet address from your minting
      const walletAddress = process.env.NEXT_PUBLIC_WALLET_ADDRESS || 'rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp'

      console.log(`Verifying NFT ${nftId} against account ${walletAddress}`)

      // Use cache helper for NFT data
      const result = await CacheHelpers.getNFTData(
        nftId,
        () => xrplService.getNFTByTokenId(nftId, walletAddress)
      )

      if (result) {
        console.log('NFT verification successful:', result)
        setNftData(result)
      } else {
        setError(`NFT not found on account ${walletAddress}. Please verify the NFT ID belongs to this account.`)
      }
    } catch (err) {
      console.error('NFT verification error:', err)
      if (err instanceof Error) {
        setError(`Verification failed: ${err.message}`)
      } else {
        setError('Error verifying NFT. Please check your connection and try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string | number | null | undefined) => {
    if (!dateString) return 'Unknown date'

    try {
      let date: Date

      if (typeof dateString === 'number') {
        // Handle Unix timestamps
        date = new Date(dateString * 1000)
      } else {
        date = new Date(dateString)
      }

      if (isNaN(date.getTime())) {
        return 'Invalid date'
      }

      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    } catch {
      return 'Invalid date'
    }
  }

  // Helper functions to extract data from metadata and attributes
  const getMetadataValue = (key: string): string | number | null | undefined => {
    if (!nftData?.metadata) return null
    const metadata = nftData.metadata

    // Handle compact format first
    if (key === 'title' || key === 'name') {
      return metadata.n || metadata.name || metadata.title
    }
    if (key === 'videoId' || key === 'video_id') {
      return metadata.v || metadata.videoId || metadata.video_id || metadata.id
    }
    if (key === 'video_url' || key === 'url') {
      return metadata.u || metadata.video_url || metadata.url || metadata.source
    }
    if (key === 'published' || key === 'published_at') {
      return metadata.p || metadata.published || metadata.published_at
    }
    if (key === 'verified' || key === 'verification_timestamp') {
      return metadata.vf || metadata.verified || metadata.verification_timestamp
    }
    if (key === 'channel') {
      return metadata.c || metadata.channel || metadata.channel_title
    }

    return (metadata as Record<string, unknown>)[key] as string | number | null | undefined
  }

  const getAttributeValue = (trait_type: string) => {
    if (!nftData?.metadata?.attributes) return null
    const attr = nftData.metadata.attributes.find((a: { trait_type: string; value: string | number }) =>
      a.trait_type === trait_type ||
      a.trait_type.toLowerCase() === trait_type.toLowerCase()
    )
    return attr ? attr.value : null
  }

  const getVideoId = (): string | null => {
    const value = getMetadataValue('videoId') ||
           getMetadataValue('video_id') ||
           getAttributeValue('videoId') ||
           getAttributeValue('v')
    return typeof value === 'string' ? value : null
  }

  const getThumbnailUrl = (): string | null => {
    const directImage = getMetadataValue('image') || getMetadataValue('thumbnail_url')
    if (directImage && typeof directImage === 'string') return directImage

    const videoId = getVideoId()
    if (videoId) {
      return `https://i.ytimg.com/vi/${videoId}/hqdefault.jpg`
    }
    return null
  }

  const getVideoUrl = (): string | null => {
    const directUrl = getMetadataValue('video_url') || getMetadataValue('url') ||
                     getAttributeValue('source') || getAttributeValue('url')
    if (directUrl && typeof directUrl === 'string') return directUrl

    const videoId = getVideoId()
    if (videoId) {
      return `https://www.youtube.com/watch?v=${videoId}`
    }
    return null
  }

  const getShareUrl = () => {
    if (nftData && typeof window !== 'undefined') {
      return `${window.location.origin}/verify/${nftData.nft_id}`
    }
    return ''
  }

  const copyShareUrl = () => {
    const url = getShareUrl()
    navigator.clipboard.writeText(url)
    alert('Share URL copied to clipboard!')
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6 p-4">
      {/* Header */}
      <div className="text-center space-y-4 pt-8">
        <div className="flex items-center justify-center space-x-2">
          <Youtube className="w-8 h-8 text-red-500" />
          <CheckCircle className="w-8 h-8 text-green-500" />
        </div>
        <h1 className="text-3xl font-bold text-gray-900">
          YouTube NFT Verifier
        </h1>
        <p className="text-gray-600 text-lg">
          Verify authentic YouTube videos using XRPL NFTs
        </p>
      </div>

      {/* Search Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Search className="w-5 h-5" />
            <span>Verify NFT</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex space-x-2">
            <Input
              placeholder="Enter NFT Token ID"
              value={nftId}
              onChange={(e) => setNftId(e.target.value)}
              className="flex-1"
            />
            <Button
              onClick={handleVerify}
              disabled={loading}
              className="px-6"
            >
              {loading ? 'Verifying...' : 'Verify'}
            </Button>
          </div>

          {error && (
            <div className="flex items-center space-x-2 text-red-600 bg-red-50 p-3 rounded-lg">
              <AlertCircle className="w-4 h-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Card */}
      {nftData && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-500" />
              <span>Verified NFT</span>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {nftData.metadata ? (
              <>
                {/* Video Info */}
                <div className="space-y-3">
                  <h3 className="text-xl font-semibold text-gray-900">
                    {getMetadataValue('title') || getMetadataValue('name') || 'YouTube NFT'}
                  </h3>

                  <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">
                      {getAttributeValue('contextType') || 'YouTube'}
                    </Badge>
                    <Badge variant="secondary">
                      {getAttributeValue('category') || getMetadataValue('category') || 'Video'}
                    </Badge>
                    <Badge variant="outline" className="text-green-600 border-green-200">
                      Verified Content
                    </Badge>
                    {getAttributeValue('network') && (
                      <Badge variant="outline">
                        {getAttributeValue('network')}
                      </Badge>
                    )}
                  </div>

                  {getThumbnailUrl() && (
                    <IPFSImage
                      src={getThumbnailUrl() as string}
                      alt={(getMetadataValue('title') as string) || 'NFT Thumbnail'}
                      className="w-full rounded-lg shadow-md"
                    />
                  )}

                  <p className="text-gray-600">
                    {getMetadataValue('description') ||
                     `Verified YouTube video from ${getAttributeValue('channel') || 'Jim Flint'}. This NFT represents authentic content on the XRPL blockchain.`}
                  </p>
                </div>

                {/* Video Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Creator:</span>
                    <p className="text-gray-600">All-Time High</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Video ID:</span>
                    <p className="text-gray-600 font-mono text-xs">{getVideoId() || 'N/A'}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Published:</span>
                    <p className="text-gray-600">
                      {formatDate(getMetadataValue('published') || getMetadataValue('published_at'))}
                    </p>
                  </div>
                  {/* <div>
                    <span className="font-medium text-gray-700">Verified:</span>
                    <p className="text-gray-600">
                      {formatDate(getMetadataValue('verified') || getMetadataValue('verification_timestamp') || Date.now())}
                    </p>
                  </div> */}
                </div>

                {/* Attributes Display */}
                {nftData.metadata.attributes && nftData.metadata.attributes.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-700">Attributes & Traits</h4>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                      {nftData.metadata.attributes.map((attr, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-2 text-xs">
                          <div className="font-medium text-gray-700">{attr.trait_type}</div>
                          <div className="text-gray-600">
                            {attr.display_type === 'date'
                              ? formatDate(new Date(Number(attr.value) * 1000).toISOString())
                              : attr.display_type === 'boost_percentage'
                              ? `${attr.value}%`
                              : attr.value
                            }
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI Content Claim */}
                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="w-5 h-5 text-green-600" />
                    <span className="font-medium text-green-800">Content Verification</span>
                  </div>
                  <p className="text-green-700 mt-1">
                    {(nftData.metadata.ai === 'none' || nftData.metadata.ai === 'no')
                      ? 'This video is certified to contain no AI-generated content'
                      : nftData.metadata.ai_content_claim || 'Content verification status confirmed'}
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3">
                  <Button
                    asChild
                    className="flex-1"
                    variant="default"
                  >
                    <a
                      href={getVideoUrl() || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center space-x-2"
                    >
                      <Youtube className="w-4 h-4" />
                      <span>Watch Video</span>
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </Button>

                  <Button
                    asChild
                    variant="outline"
                    className="flex-1"
                  >
                    <a
                      href={xrplService.getBithompExplorerUrl(nftData.nft_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center space-x-2"
                    >
                      <span>View on Bithomp</span>
                      <ExternalLink className="w-4 h-4" />
                    </a>
                  </Button>
                </div>
              </>
            ) : (
              <div className="text-center py-8">
                <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  NFT Found but Metadata Unavailable
                </h3>
                <p className="text-gray-600 mb-4">
                  The NFT exists but metadata could not be parsed.
                </p>
                <Button
                  asChild
                  variant="outline"
                >
                  <a
                    href={xrplService.getBithompExplorerUrl(nftData.nft_id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-2"
                  >
                    <span>View on Bithomp</span>
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </Button>
              </div>
            )}

            {/* Share URL */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium text-blue-800">Share this NFT</span>
                <Share2 className="w-4 h-4 text-blue-600" />
              </div>
              <div className="flex items-center space-x-2">
                <code className="text-xs bg-white px-3 py-2 rounded text-blue-600 flex-1 truncate border border-blue-200">
                  {getShareUrl()}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={copyShareUrl}
                  className="flex-shrink-0"
                >
                  Copy
                </Button>
              </div>
            </div>

            {/* Technical Details */}
            <div className="border-t pt-4 space-y-2 text-xs text-gray-500">
              <div className="break-all"><span className="font-medium">NFT ID:</span> {nftData.nft_id}</div>
              <div className="break-all"><span className="font-medium">Issuer:</span> {nftData.issuer}</div>
              <div><span className="font-medium">Flags:</span> {nftData.flags}</div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">How it works</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm text-gray-600">
          <p>
            1. Each YouTube video from All-Time High is minted as an NFT on the XRPL {xrplService.getNetworkName()}
          </p>
          <p>
            2. The NFT contains metadata including title, URL, thumbnail, and AI content verification
          </p>
          <p>
            3. Enter the NFT ID (found in video comments) to verify authenticity
          </p>
          <p>
            4. Verified videos are guaranteed to contain no AI-generated content
          </p>
        </CardContent>
      </Card>
    </div>
  )
}