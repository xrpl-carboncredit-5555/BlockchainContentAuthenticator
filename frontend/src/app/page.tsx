'use client'

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import NFTVerifier from '@/components/nft-verifier'
import VideoGallery from '@/components/video-gallery'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto p-4">
        <div className="max-w-7xl mx-auto mb-8">
          <div className="flex flex-col items-center gap-6 mb-8">
            <img
              src="/JF-Logo-horz-White.png"
              alt="Logo"
              className="h-40 w-auto"   // <--- Increased from h-16 to h-24
            />
            <h1 className="text-4xl font-bold text-center bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              Blockchain Content Authenticator
            </h1>
          </div>
        </div>

        <Tabs defaultValue="verify" className="max-w-7xl mx-auto">
          <div className="flex justify-center mb-6">
            <TabsList className="grid w-full max-w-md grid-cols-2">
              <TabsTrigger value="verify">Verify NFT</TabsTrigger>
              <TabsTrigger value="gallery">Video Gallery</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="verify" className="mt-0">
            <NFTVerifier />
          </TabsContent>

          <TabsContent value="gallery" className="mt-0">
            <VideoGallery />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
