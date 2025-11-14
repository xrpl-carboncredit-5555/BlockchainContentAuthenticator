"""
Example usage of Pinata, YouTube, and XRPL services
"""
from dotenv import load_dotenv
from src.services import create_pinata_service, create_youtube_service, create_xrpl_service

# Load environment variables
load_dotenv()


def pinata_examples():
    """Examples of using the Pinata service"""
    pinata = create_pinata_service()

    # Example 1: Upload JSON with category
    metadata = {
        "video_id": "abc123",
        "title": "Sample Video",
        "timestamp": "2025-10-27"
    }

    result = pinata.upload_json_with_category(
        json_data=metadata,
        category="youtube_videos",
        additional_tags={
            "source": "youtube",
            "status": "processed"
        }
    )
    print(f"Uploaded to IPFS: {result['IpfsHash']}")

    # Example 2: Upload JSON with custom tags
    result = pinata.upload_json(
        json_data=metadata,
        name="custom-metadata",
        keyvalues={
            "type": "video_metadata",
            "channel": "my_channel"
        }
    )
    print(f"Uploaded with custom tags: {result['IpfsHash']}")

    # Example 3: List files by category
    files = pinata.list_by_keyvalues({"category": "youtube_videos"})
    print(f"Found {len(files.get('rows', []))} files in category")

    # Example 4: Update metadata
    ipfs_hash = result['IpfsHash']
    pinata.update_metadata(ipfs_hash, {"status": "updated", "version": "2"})
    print(f"Updated metadata for {ipfs_hash}")


def youtube_examples():
    """Examples of using the YouTube service"""
    youtube = create_youtube_service()

    # Replace with actual channel ID
    channel_id = "UC_x5XG1OV2P6uZZ5FSM9Ttw"  # Example channel

    # Example 1: Fetch all videos from channel
    videos = youtube.fetch_all_videos_from_channel(channel_id, max_results=10)
    print(f"Found {len(videos)} videos")

    # Example 2: Get video description
    if videos:
        video_id = videos[0]["contentDetails"]["videoId"]
        description = youtube.get_video_description(video_id)
        print(f"Description: {description[:100]}...")

    # Example 3: Fetch all videos with descriptions
    videos_with_desc = youtube.fetch_channel_videos_with_descriptions(
        channel_id,
        max_results=5
    )
    for video in videos_with_desc:
        print(f"Video: {video['title']}")
        print(f"Description: {video['description'][:100]}...")
        print("---")

    # Example 4: Update video description (requires OAuth token)
    # oauth_token = "your_oauth_token_here"
    # youtube.update_video_description(
    #     video_id="video_id_here",
    #     new_description="Updated description",
    #     oauth_token=oauth_token
    # )

    # Example 5: Append to video description
    # youtube.append_to_video_description(
    #     video_id="video_id_here",
    #     text_to_append="Additional information",
    #     oauth_token=oauth_token
    # )


def xrpl_examples():
    """Examples of using the XRPL service"""
    xrpl = create_xrpl_service()

    # Example 1: Get account info
    account_info = xrpl.get_account_info()
    if account_info['success']:
        print(f"Account: {xrpl.wallet.address}")
        print(f"Balance: {account_info['account_data'].get('Balance')} drops")

    # Example 2: Mint NFT with URI
    uri = "ipfs://QmXxxx/metadata.json"
    result = xrpl.mint_nft(
        uri=uri,
        taxon=0,
        transfer_fee=0,
        flags=8  # tfTransferable
    )
    if result['success']:
        print(f"NFT minted: {result['nft_id']}")
        print(f"TX Hash: {result['tx_hash']}")

    # Example 3: Mint NFT with validation memo
    result = xrpl.mint_nft_with_metadata(
        uri="https://example.com/metadata.json",
        validation_text="This content is validated and authenticated",
        taxon=0,
        flags=8
    )
    if result['success']:
        print(f"NFT with memo minted: {result['nft_id']}")

    # Example 4: Set account domain
    domain_result = xrpl.set_domain("example.com")
    if domain_result['success']:
        print(f"Domain set: {domain_result['domain']}")
        print(f"TX Hash: {domain_result['tx_hash']}")

    # Example 5: Get NFTs owned by account
    nfts = xrpl.get_nfts()
    if nfts['success']:
        print(f"Total NFTs: {len(nfts['nfts'])}")
        for nft in nfts['nfts'][:5]:  # Show first 5
            print(f"  NFT ID: {nft.get('NFTokenID')}")


if __name__ == "__main__":
    print("=== Pinata Service Examples ===")
    try:
        pinata_examples()
    except Exception as e:
        print(f"Pinata error: {str(e)}")

    print("\n=== YouTube Service Examples ===")
    try:
        youtube_examples()
    except Exception as e:
        print(f"YouTube error: {str(e)}")

    print("\n=== XRPL Service Examples ===")
    try:
        xrpl_examples()
    except Exception as e:
        print(f"XRPL error: {str(e)}")
