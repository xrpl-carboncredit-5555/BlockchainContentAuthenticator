'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { CheckCircle, AlertCircle, Youtube, ExternalLink, ArrowLeft } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { XRPLService, NFTMetadata } from '@/lib/xrpl'
import IPFSImage from '@/components/IPFSImage'

interface NFTData {
  nft_id: string
  metadata: NFTMetadata | null
  issuer: string
  flags: number
}

export default function VerifyNFTPage() {
  const params = useParams()
  const router = useRouter()
  const nftId = params.nftId as string

  const [loading, setLoading] = useState(true)
  const [nftData, setNftData] = useState<NFTData | null>(null)
  const [error, setError] = useState('')

  const xrplService = new XRPLService() // Uses NEXT_PUBLIC_XRPL_NETWORK env variable

  useEffect(() => {
    if (nftId) {
      handleVerify()
    }
  }, [nftId]) // eslint-disable-line react-hooks/exhaustive-deps

  const handleVerify = async () => {
    if (!nftId || nftId.length < 32) {
      setError('Invalid NFT ID format. Please check the URL.')
      setLoading(false)
      return
    }

    setLoading(true)
    setError('')
    setNftData(null)

    try {
      const walletAddress = process.env.NEXT_PUBLIC_WALLET_ADDRESS || 'rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp'
      console.log(`Verifying NFT ${nftId} against account ${walletAddress}`)

      const result = await xrplService.getNFTByTokenId(nftId, walletAddress)

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

  const getMetadataValue = (key: string): string | number | null | undefined => {
    if (!nftData?.metadata) return null
    const metadata = nftData.metadata

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

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Verifying NFT...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto p-4 max-w-2xl">
        <div className="py-8 space-y-6">
          {/* Header with Back Button */}
          <div className="flex items-center space-x-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/')}
              className="flex items-center space-x-2"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back</span>
            </Button>
          </div>

          <div className="text-center space-y-4">
            <div className="flex items-center justify-center space-x-2">
              <Youtube className="w-8 h-8 text-red-500" />
              <CheckCircle className="w-8 h-8 text-green-500" />
            </div>
            <h1 className="text-3xl font-bold text-gray-900">
              NFT Verification
            </h1>
          </div>

          {/* Error State */}
          {error && (
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center space-x-2 text-red-600">
                  <AlertCircle className="w-5 h-5" />
                  <span>{error}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Success State */}
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
                      </div>

                      {getThumbnailUrl() && (
                        <IPFSImage
                          src={getThumbnailUrl() as string}
                          alt={(getMetadataValue('title') as string) || 'NFT Thumbnail'}
                          className="w-full rounded-lg shadow-md"
                        />
                      )}
                    </div>

                    {/* Video Details */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-gray-700">Creator:</span>
                        <p className="text-gray-600 break-words">{getAttributeValue('channel') || 'All-Time High'}</p>
                      </div>
                      <div>
                        <span className="font-medium text-gray-700">Video ID:</span>
                        <p className="text-gray-600 font-mono text-xs break-all">{getVideoId() || 'N/A'}</p>
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
                        <div className="grid grid-cols-2 gap-2">
                          {nftData.metadata.attributes.map((attr, index) => (
                            <div key={index} className="bg-gray-50 rounded-lg p-2 text-xs">
                              <div className="font-medium text-gray-700 truncate">{attr.trait_type}</div>
                              <div className="text-gray-600 break-words">
                                {attr.display_type === 'date'
                                  ? formatDate(new Date(Number(attr.value) * 1000).toISOString())
                                  : String(attr.value)}
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
                  </div>
                )}

                {/* Technical Details */}
                <div className="border-t pt-4 space-y-2 text-xs text-gray-500">
                  <div className="break-all"><span className="font-medium">NFT ID:</span> {nftData.nft_id}</div>
                  <div className="break-all"><span className="font-medium">Issuer:</span> {nftData.issuer}</div>
                  <div><span className="font-medium">Flags:</span> {nftData.flags}</div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
