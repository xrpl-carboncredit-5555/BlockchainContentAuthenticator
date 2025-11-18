import { NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

interface VideoData {
  nft_id: string
  title: string
  video_url: string
  thumbnail_url?: string
  channel_title?: string
  minted_at: string
  wallet_address?: string
}

type VideoMapping = Record<string, VideoData>

export async function GET() {
  try {
    // Read the mapping file from the project root
    const mappingPath = path.join(process.cwd(), '..', 'video_nft_mapping.json')

    // Check if file exists
    if (!fs.existsSync(mappingPath)) {
      // Try alternate path
      const altPath = path.join(process.cwd(), '../../', 'video_nft_mapping.json')
      if (fs.existsSync(altPath)) {
        const fileContent = fs.readFileSync(altPath, 'utf8')
        const mapping = JSON.parse(fileContent) as VideoMapping

        const videos = Object.entries(mapping).map(([videoId, data]) => ({
          video_id: videoId,
          nft_id: data.nft_id,
          title: data.title,
          video_url: data.video_url,
          thumbnail_url: data.thumbnail_url,
          channel_title: data.channel_title,
          minted_at: data.minted_at,
          wallet_address: data.wallet_address || 'rrn5TTseRjmcV3Da3Z4ituzKsoXWVqYpbg'
        }))

        return NextResponse.json(videos)
      }

      // Return empty array if no mapping exists
      return NextResponse.json([])
    }

    // Read the actual mapping file
    const fileContent = fs.readFileSync(mappingPath, 'utf8')
    const mapping = JSON.parse(fileContent) as VideoMapping

    // Convert mapping object to array format expected by frontend
    const videos = Object.entries(mapping).map(([videoId, data]) => ({
      video_id: videoId,
      nft_id: data.nft_id,
      title: data.title,
      video_url: data.video_url,
      minted_at: data.minted_at,
      wallet_address: data.wallet_address
    }))

    return NextResponse.json(videos)
  } catch (error) {
    console.error('Error reading video mapping:', error)

    // Return mock data on error
    return NextResponse.json([
      {
        nft_id: '0A6AB0DD8D02442612473E9AE60502E0CDE439B1D7C24BED3DFE701DE6CCAC6A',
        title: 'NFL Players\' Faith.',
        video_url: 'https://www.youtube.com/watch?v=jsw6W-ml6zE',
        minted_at: '2025-09-17T19:51:39.075485',
        wallet_address: 'rfPebuKUnW8xnansvo6WiM7i76YxT9chgh'
      },
      {
        nft_id: '25A43E25C70AA06C295BD16D35424D3FDD85F4136554938695208C9EB1691964',
        title: 'From Losing to Winning!',
        video_url: 'https://www.youtube.com/watch?v=d3Hyjj83jf4',
        minted_at: '2025-09-17T19:51:49.270967',
        wallet_address: 'rfPebuKUnW8xnansvo6WiM7i76YxT9chgh'
      },
      {
        nft_id: '0FDCE4749C7474101E955B0FE103D639E931E2310EF5CC0BD3CB1488F30ACAB3',
        title: 'The 50% Rule!',
        video_url: 'https://www.youtube.com/watch?v=8_hJnhQH8UI',
        minted_at: '2025-09-17T19:51:56.450075',
        wallet_address: 'rfPebuKUnW8xnansvo6WiM7i76YxT9chgh'
      }
    ])
  }
}