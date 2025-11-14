#!/usr/bin/env python3
"""
Query and display NFT data from MongoDB
"""

import sys
from datetime import datetime
from dotenv import load_dotenv
from src.services import create_mongodb_service

load_dotenv()


def display_nft(nft, detailed=False):
    """Display NFT information"""
    print(f"\n{'=' * 70}")
    print(f"🎨 NFT: {nft.get('video_id', 'Unknown')}")
    print(f"{'=' * 70}")

    # Essential fields
    print(f"\n📊 Core Information:")
    print(f"   NFT Token ID: {nft.get('nft_id', 'N/A')}")
    print(f"   Video ID: {nft.get('video_id', 'N/A')}")
    print(f"   TX Hash: {nft.get('tx_hash', 'N/A')}")
    print(f"   Account: {nft.get('account', 'N/A')}")
    print(f"   Network: {nft.get('network', 'testnet')}")

    # IPFS Data
    print(f"\n📦 IPFS Storage:")
    print(f"   Metadata: {nft.get('metadata_ipfs_hash', 'N/A')}")
    print(f"   Image: {nft.get('image_ipfs_hash', 'N/A')}")
    print(f"   URI: {nft.get('uri', 'N/A')}")

    # Video Info
    if nft.get('metadata'):
        meta = nft['metadata']
        print(f"\n🎬 Video Information:")
        print(f"   Title: {meta.get('name', 'N/A')[:60]}...")
        print(f"   External URL: {meta.get('external_url', 'N/A')}")

        # Attributes
        if meta.get('attributes'):
            print(f"\n🏷️  Attributes:")
            for attr in meta['attributes']:
                print(f"   {attr['trait_type']}: {attr['value']}")

    # Memo Data
    if nft.get('memo_data'):
        memo = nft['memo_data']
        print(f"\n📝 On-Chain Memo:")
        print(f"   {memo}")

    # Timestamps
    if nft.get('minted_at'):
        minted = nft['minted_at']
        if isinstance(minted, datetime):
            print(f"\n⏰ Minted: {minted.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        else:
            print(f"\n⏰ Minted: {minted}")

    if detailed:
        print(f"\n📋 Full Data:")
        import json
        print(json.dumps(nft, indent=2, default=str))


def query_nft_by_video_id(video_id):
    """Query NFT by video ID"""
    print(f"\n🔍 Querying NFT for video: {video_id}")

    mongodb = create_mongodb_service()
    nft = mongodb.get_nft_by_video_id(video_id)
    mongodb.close()

    if nft:
        display_nft(nft, detailed=True)
    else:
        print(f"   ❌ No NFT found for video: {video_id}")


def query_nft_by_nft_id(nft_id):
    """Query NFT by NFT token ID"""
    print(f"\n🔍 Querying NFT: {nft_id}")

    mongodb = create_mongodb_service()
    nft = mongodb.get_nft_by_nft_id(nft_id)
    mongodb.close()

    if nft:
        display_nft(nft, detailed=True)
    else:
        print(f"   ❌ No NFT found with ID: {nft_id}")


def list_all_nfts(limit=10):
    """List all NFTs"""
    print(f"\n📋 Listing NFTs (limit: {limit})")

    mongodb = create_mongodb_service()
    nfts = mongodb.get_all_nfts(limit=limit)
    mongodb.close()

    if not nfts:
        print(f"   ℹ️  No NFTs found in database")
        return

    print(f"\n   Found {len(nfts)} NFT(s):\n")

    for i, nft in enumerate(nfts, 1):
        video_id = nft.get('video_id', 'Unknown')
        nft_id = nft.get('nft_id', 'N/A')[:30]
        category = nft.get('memo_data', {}).get('category', 'N/A')
        minted = nft.get('minted_at', 'N/A')

        if isinstance(minted, datetime):
            minted_str = minted.strftime('%Y-%m-%d')
        else:
            minted_str = str(minted)[:10]

        print(f"   {i}. {video_id}")
        print(f"      NFT: {nft_id}...")
        print(f"      Category: {category} | Minted: {minted_str}\n")


def verify_nft_fields(nft_id=None, video_id=None):
    """Verify all required fields are present in NFT record"""
    print(f"\n✅ Verifying NFT Fields")

    mongodb = create_mongodb_service()

    if nft_id:
        nft = mongodb.get_nft_by_nft_id(nft_id)
    elif video_id:
        nft = mongodb.get_nft_by_video_id(video_id)
    else:
        # Get latest NFT
        nfts = mongodb.get_all_nfts(limit=1)
        nft = nfts[0] if nfts else None

    mongodb.close()

    if not nft:
        print("   ❌ No NFT found to verify")
        return

    print(f"\n   Verifying NFT: {nft.get('video_id', 'Unknown')}")

    # Required fields
    required_fields = {
        'nft_id': 'NFT Token ID',
        'video_id': 'Video ID',
        'tx_hash': 'Transaction Hash',
        'uri': 'IPFS URI',
        'metadata_ipfs_hash': 'Metadata IPFS Hash',
        'image_ipfs_hash': 'Image IPFS Hash',
        'taxon': 'Taxon',
        'account': 'Wallet Account',
        'minted_at': 'Minted Timestamp',
        'metadata': 'Full Metadata',
        'memo_data': 'Compact Memo',
        'network': 'Network'
    }

    missing = []
    present = []

    print(f"\n   Field Verification:")
    for field, name in required_fields.items():
        if field in nft and nft[field]:
            print(f"   ✅ {name}: Present")
            present.append(field)
        else:
            print(f"   ❌ {name}: Missing")
            missing.append(field)

    print(f"\n   Summary:")
    print(f"   ✅ Present: {len(present)}/{len(required_fields)}")
    print(f"   ❌ Missing: {len(missing)}/{len(required_fields)}")

    if missing:
        print(f"\n   ⚠️  Missing fields: {', '.join(missing)}")
    else:
        print(f"\n   🎉 All required fields present!")

    return len(missing) == 0


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python query_nfts.py list [limit]          # List all NFTs")
        print("  python query_nfts.py video <video_id>      # Query by video ID")
        print("  python query_nfts.py nft <nft_id>          # Query by NFT ID")
        print("  python query_nfts.py verify [video_id]     # Verify NFT fields")
        print("\nExamples:")
        print("  python query_nfts.py list 10")
        print("  python query_nfts.py video abc123")
        print("  python query_nfts.py nft 000B0000...")
        print("  python query_nfts.py verify")
        sys.exit(1)

    command = sys.argv[1]

    if command == "list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        list_all_nfts(limit)

    elif command == "video":
        if len(sys.argv) < 3:
            print("❌ Please provide video ID")
            sys.exit(1)
        video_id = sys.argv[2]
        query_nft_by_video_id(video_id)

    elif command == "nft":
        if len(sys.argv) < 3:
            print("❌ Please provide NFT ID")
            sys.exit(1)
        nft_id = sys.argv[2]
        query_nft_by_nft_id(nft_id)

    elif command == "verify":
        if len(sys.argv) > 2:
            verify_nft_fields(video_id=sys.argv[2])
        else:
            verify_nft_fields()

    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
