'use client'

import { useState, useEffect, useCallback, useMemo } from 'react'
import { XRPLService, NFTResult } from '@/lib/xrpl'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ExternalLink, Youtube, Copy, RefreshCw, Share2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import IPFSImage from '@/components/IPFSImage'
import { CacheHelpers } from '@/lib/cache'

export default function NFTsPage() {
  const [nfts, setNfts] = useState<NFTResult[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const xrplService = useMemo(() => new XRPLService(), []) // Uses NEXT_PUBLIC_XRPL_NETWORK env variable
  const walletAddress = process.env.NEXT_PUBLIC_WALLET_ADDRESS || 'rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp'

  const loadNFTs = useCallback(async () => {
    setLoading(true)
    setError('')

    try {
      // Use cache helper to get NFT list with 6-hour cache
      const allNFTs = await CacheHelpers.getNFTList<NFTResult[]>(
        walletAddress,
        () => xrplService.getAllNFTs(walletAddress)
      )
      setNfts(allNFTs)
    } catch (err) {
      setError('Failed to load NFTs: ' + (err as Error).message)
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [xrplService, walletAddress])

  useEffect(() => {
    loadNFTs()
  }, [loadNFTs])

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

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">All NFTs from Wallet</h1>
        <p className="text-gray-600">Wallet: {walletAddress}</p>
        <Button onClick={loadNFTs} className="mt-4" disabled={loading}>
          <RefreshCw className={`mr-2 h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 p-4 rounded mb-6">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="text-center py-10">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4">Loading NFTs from XRPL...</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {nfts.map((nft, index) => (
            <Card key={nft.nft_id || index} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="text-sm font-medium truncate">
                  {nft.metadata?.name || nft.metadata?.title || `NFT #${index + 1}`}
                </CardTitle>
                <div className="flex items-center gap-2 mt-2">
                  <Badge variant="outline" className="text-xs">
                    {nft.metadata?.attributes?.find((a: { trait_type: string; value: string | number }) => a.trait_type === 'contextType')?.value || 'NFT'}
                  </Badge>
                  {nft.metadata?.category && (
                    <Badge variant="secondary" className="text-xs">
                      {nft.metadata.category}
                    </Badge>
                  )}
                </div>
              </CardHeader>

              <CardContent className="space-y-3">
                {/* Thumbnail */}
                {nft.metadata?.image && (
                  <IPFSImage
                    src={nft.metadata.image}
                    alt={nft.metadata.name || 'NFT'}
                    className="w-full h-32 object-cover rounded"
                  />
                )}

                {/* NFT ID */}
                <div>
                  <p className="text-xs text-gray-500">NFT ID:</p>
                  <div className="flex items-center gap-1">
                    <p className="text-xs font-mono truncate break-all">{nft.nft_id}</p>
                    <Copy
                      className="h-3 w-3 flex-shrink-0 cursor-pointer text-gray-400 hover:text-gray-600"
                      onClick={() => copyToClipboard(nft.nft_id)}
                    />
                  </div>
                </div>

                {/* Share URL */}
                <div>
                  <p className="text-xs text-gray-500">Share URL:</p>
                  <div className="flex items-center gap-1">
                    <p className="text-xs text-blue-500 truncate">{getShareUrl(nft.nft_id)}</p>
                    <Share2
                      className="h-3 w-3 flex-shrink-0 cursor-pointer text-gray-400 hover:text-blue-600"
                      onClick={() => copyShareUrl(nft.nft_id)}
                    />
                  </div>
                </div>

                {/* Video URL */}
                {(nft.metadata?.video_url || nft.metadata?.source) && (
                  <div>
                    <p className="text-xs text-gray-500">Video:</p>
                    <a
                      href={nft.metadata.video_url || nft.metadata.source}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-blue-500 hover:underline flex items-center gap-1 truncate"
                    >
                      <Youtube className="h-3 w-3 flex-shrink-0" />
                      <span className="truncate">Watch on YouTube</span>
                      <ExternalLink className="h-3 w-3 flex-shrink-0" />
                    </a>
                  </div>
                )}

                {/* Metadata Details */}
                {nft.metadata && (
                  <details className="text-xs">
                    <summary className="cursor-pointer text-gray-500 hover:text-gray-700">
                      View Metadata
                    </summary>
                    <pre className="mt-2 p-2 bg-gray-50 rounded overflow-x-auto text-xs">
                      {JSON.stringify(nft.metadata, null, 2)}
                    </pre>
                  </details>
                )}

                {/* Explorer Link */}
                <a
                  href={xrplService.getXRPLExplorerUrl(nft.nft_id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-blue-500 hover:underline flex items-center gap-1"
                >
                  View on XRPL Explorer
                  <ExternalLink className="h-3 w-3" />
                </a>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {!loading && nfts.length === 0 && (
        <div className="text-center py-10">
          <p className="text-gray-500">No NFTs found in this wallet</p>
        </div>
      )}

      {!loading && nfts.length > 0 && (
        <div className="mt-6 text-center text-sm text-gray-500">
          Total NFTs: {nfts.length}
        </div>
      )}
    </div>
  )
}