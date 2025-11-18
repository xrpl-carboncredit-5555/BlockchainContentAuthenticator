'use client'

import { useState, useEffect } from 'react'
import { ipfsImageCache } from '@/lib/ipfsImageCache'

interface IPFSImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
  src: string
  alt: string
  fallbackSrc?: string
  loadingComponent?: React.ReactNode
}

/**
 * IPFSImage Component
 *
 * Smart image component that handles IPFS URIs with caching:
 * - Automatically detects IPFS URIs (ipfs://, Qm..., bafy...)
 * - Fetches from IPFS gateways with fallback
 * - Caches images in localStorage and memory (7-day TTL)
 * - Falls back to regular image loading for non-IPFS URLs
 * - Shows loading state while fetching
 * - Handles errors gracefully with fallback image
 *
 * Usage:
 * <IPFSImage
 *   src="ipfs://QmHash..."
 *   alt="NFT Image"
 *   className="w-full h-32"
 *   fallbackSrc="/placeholder.png"
 * />
 */
export default function IPFSImage({
  src,
  alt,
  fallbackSrc,
  loadingComponent,
  onError,
  ...props
}: IPFSImageProps) {
  const [imageSrc, setImageSrc] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  useEffect(() => {
    let isMounted = true

    const loadImage = async () => {
      if (!src) {
        setIsLoading(false)
        return
      }

      setIsLoading(true)
      setHasError(false)

      // Check if it's an IPFS URL
      if (ipfsImageCache.isIPFSUrl(src)) {
        try {
          // Try to fetch from cache or IPFS gateways
          const dataUrl = await ipfsImageCache.fetchAndCache(src)

          if (isMounted) {
            if (dataUrl) {
              setImageSrc(dataUrl)
            } else {
              // IPFS fetch failed, try fallback or show error
              if (fallbackSrc) {
                setImageSrc(fallbackSrc)
              } else {
                setHasError(true)
              }
            }
            setIsLoading(false)
          }
        } catch (error) {
          console.error('Error loading IPFS image:', error)
          if (isMounted) {
            if (fallbackSrc) {
              setImageSrc(fallbackSrc)
            } else {
              setHasError(true)
            }
            setIsLoading(false)
          }
        }
      } else {
        // Regular URL, use directly
        if (isMounted) {
          setImageSrc(src)
          setIsLoading(false)
        }
      }
    }

    loadImage()

    return () => {
      isMounted = false
    }
  }, [src, fallbackSrc])

  const handleError = (e: React.SyntheticEvent<HTMLImageElement, Event>) => {
    console.error('Image load error:', src)
    setHasError(true)

    // Try fallback if available
    if (fallbackSrc && imageSrc !== fallbackSrc) {
      setImageSrc(fallbackSrc)
      setHasError(false)
    } else {
      // Hide image on error
      (e.target as HTMLImageElement).style.display = 'none'
    }

    // Call custom onError handler if provided
    if (onError) {
      onError(e)
    }
  }

  if (isLoading) {
    return (
      loadingComponent || (
        <div
          className={`bg-gray-200 animate-pulse ${props.className || ''}`}
          style={props.style}
        >
          <div className="flex items-center justify-center h-full w-full text-gray-400 text-xs">
            Loading...
          </div>
        </div>
      )
    )
  }

  if (hasError && !fallbackSrc) {
    return null
  }

  return (
    <img
      {...props}
      src={imageSrc || fallbackSrc || ''}
      alt={alt}
      onError={handleError}
    />
  )
}
