import { NextResponse } from 'next/server'
import { promises as fs } from 'fs'
import path from 'path'

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
  metadata?: Record<string, unknown>
  issuer?: string
}

interface CacheData {
  videos: VideoData[]
  lastUpdated: string
  walletAddress: string
  totalCount: number
}

const CACHE_FILE_PATH = path.join(process.cwd(), 'data', 'video-cache.json')

async function ensureDataDirectory() {
  const dataDir = path.join(process.cwd(), 'data')
  try {
    await fs.access(dataDir)
  } catch {
    await fs.mkdir(dataDir, { recursive: true })
  }
}

async function readCacheFile(): Promise<CacheData | null> {
  try {
    await fs.access(CACHE_FILE_PATH)
    const data = await fs.readFile(CACHE_FILE_PATH, 'utf-8')
    return JSON.parse(data) as CacheData
  } catch {
    return null
  }
}

async function writeCacheFile(data: CacheData): Promise<void> {
  await ensureDataDirectory()
  await fs.writeFile(CACHE_FILE_PATH, JSON.stringify(data, null, 2), 'utf-8')
}

// GET - Retrieve cached videos with pagination
export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const page = parseInt(searchParams.get('page') || '1', 10)
    const limit = parseInt(searchParams.get('limit') || '12', 10)
    const search = searchParams.get('search') || ''

    const cacheData = await readCacheFile()

    if (!cacheData) {
      return NextResponse.json({
        success: false,
        cached: false,
        message: 'No cache file found. Please load videos from XRPL first.',
        videos: [],
        pagination: {
          page: 1,
          limit,
          total: 0,
          totalPages: 0,
          hasNext: false,
          hasPrev: false
        }
      })
    }

    let filteredVideos = cacheData.videos

    // Apply search filter
    if (search) {
      const searchLower = search.toLowerCase()
      filteredVideos = filteredVideos.filter(video =>
        video.title.toLowerCase().includes(searchLower) ||
        video.channel_title?.toLowerCase().includes(searchLower) ||
        video.category?.toLowerCase().includes(searchLower)
      )
    }

    const total = filteredVideos.length
    const totalPages = Math.ceil(total / limit)
    const startIndex = (page - 1) * limit
    const endIndex = startIndex + limit
    const paginatedVideos = filteredVideos.slice(startIndex, endIndex)

    return NextResponse.json({
      success: true,
      cached: true,
      lastUpdated: cacheData.lastUpdated,
      walletAddress: cacheData.walletAddress,
      videos: paginatedVideos,
      pagination: {
        page,
        limit,
        total,
        totalPages,
        hasNext: page < totalPages,
        hasPrev: page > 1
      }
    })
  } catch (error) {
    console.error('Error reading cache:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to read cache' },
      { status: 500 }
    )
  }
}

// POST - Save videos to cache
export async function POST(request: Request) {
  try {
    const body = await request.json()
    const { videos, walletAddress } = body as { videos: VideoData[]; walletAddress: string }

    if (!videos || !Array.isArray(videos)) {
      return NextResponse.json(
        { success: false, error: 'Invalid videos data' },
        { status: 400 }
      )
    }

    const cacheData: CacheData = {
      videos,
      lastUpdated: new Date().toISOString(),
      walletAddress: walletAddress || 'unknown',
      totalCount: videos.length
    }

    await writeCacheFile(cacheData)

    return NextResponse.json({
      success: true,
      message: 'Cache updated successfully',
      totalCount: videos.length,
      lastUpdated: cacheData.lastUpdated
    })
  } catch (error) {
    console.error('Error writing cache:', error)
    return NextResponse.json(
      { success: false, error: 'Failed to write cache' },
      { status: 500 }
    )
  }
}

// DELETE - Clear the cache
export async function DELETE() {
  try {
    await fs.unlink(CACHE_FILE_PATH)
    return NextResponse.json({
      success: true,
      message: 'Cache cleared successfully'
    })
  } catch (error) {
    // File might not exist, which is fine
    console.log('Cache file not found or already deleted:', error)
    return NextResponse.json({
      success: true,
      message: 'Cache cleared (file did not exist)'
    })
  }
}
