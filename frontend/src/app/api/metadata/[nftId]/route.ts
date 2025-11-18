import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ nftId: string }> }
) {
  try {
    const { nftId } = await params

    // Read the full metadata file from the project root
    const metadataPath = path.join(process.cwd(), '..', 'metadata', `${nftId}.json`)

    // Check if file exists
    if (!fs.existsSync(metadataPath)) {
      return NextResponse.json(
        { error: 'NFT metadata not found' },
        { status: 404 }
      )
    }

    // Read the metadata file
    const fileContent = fs.readFileSync(metadataPath, 'utf8')
    const metadata = JSON.parse(fileContent)

    return NextResponse.json(metadata)
  } catch (error) {
    console.error('Error reading NFT metadata:', error)
    return NextResponse.json(
      { error: 'Failed to load NFT metadata' },
      { status: 500 }
    )
  }
}