#!/usr/bin/env python3
"""
YouTube NFT Minting Management Script
Uses services from src/services for all operations
"""

import json
import hashlib
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import List
from xrpl.models.transactions import Memo
from xrpl.utils import str_to_hex

from src.services import (
    create_pinata_service,
    create_youtube_service,
    create_xrpl_service,
    create_mongodb_service
)

load_dotenv()


def categorize_video(title: str, description: str = "") -> str:
    """Determine video category based on title and description"""
    text = (title + " " + description).lower()

    if any(word in text for word in ['ai', 'chatgpt', 'grok', 'llm', 'artificial intelligence']):
        return "AI & Technology"
    elif any(word in text for word in ['car', 'dealer', 'automotive', 'vehicle']):
        return "Automotive"
    elif any(word in text for word in ['nfl', 'football', 'sports', 'game']):
        return "Sports"
    elif any(word in text for word in ['business', 'entrepreneur', 'marketing']):
        return "Business"
    else:
        return "General"


def transform_youtube_video(raw_video: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Transform YouTube API format to our internal format"""
    try:
        # Handle both formats: direct format and YouTube API format
        if 'snippet' in raw_video:
            # YouTube API format
            video_id = raw_video['id']
            snippet = raw_video['snippet']

            # Get best thumbnail
            thumbnails = snippet.get('thumbnails', {})
            thumbnail_url = (
                thumbnails.get('maxres', {}).get('url') or
                thumbnails.get('high', {}).get('url') or
                thumbnails.get('medium', {}).get('url') or
                thumbnails.get('default', {}).get('url', '')
            )

            video_data = {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'description': snippet.get('description', ''),
                'published_at': snippet.get('publishedAt', ''),
                'thumbnail_url': thumbnail_url,
                'video_url': f"https://www.youtube.com/watch?v={video_id}",
                'channel_title': snippet.get('channelTitle', 'Unknown'),
                'channel_id': snippet.get('channelId', '')
            }
        else:
            # Already in our format
            video_data = raw_video

            # Ensure required fields
            if 'video_id' not in video_data:
                return None

        return video_data

    except Exception as e:
        print(f"   ⚠️  Error transforming video: {e}")
        return None


def mint_video_nft(
    video_data: Dict[str, Any],
    pinata,
    xrpl,
    mongodb,
    testnet: bool = True
) -> Optional[Dict[str, Any]]:
    """Mint a single video as NFT with MongoDB tracking"""
    try:
        print(f"\n🎬 Minting: {video_data['title'][:60]}...")

        video_id = video_data['video_id']

        # Check if already minted
        existing_nft = mongodb.get_nft_by_video_id(video_id)
        if existing_nft:
            print(f"   ⚠️  Already minted: {existing_nft['nft_id']}")
            return None

        # 1. Upload thumbnail to IPFS
        print(f"   📸 Uploading thumbnail to IPFS...")
        try:
            img_result = pinata.upload_image_from_url(
                image_url=video_data['thumbnail_url'],
                name=f"thumbnail-{video_id}.jpg",
                keyvalues={"type": "youtube_thumbnail", "video_id": video_id}
            )
            image_ipfs_hash = img_result['IpfsHash']
            image_url = f"ipfs://{image_ipfs_hash}"
            print(f"   ✅ Thumbnail: {image_ipfs_hash}")
        except Exception as e:
            print(f"   ⚠️  Thumbnail upload failed, using YouTube URL: {e}")
            image_ipfs_hash = ""
            image_url = video_data['thumbnail_url']

        # 2. Create metadata
        pub_date = datetime.fromisoformat(video_data['published_at'].replace('Z', '+00:00'))
        category = categorize_video(video_data['title'], video_data.get('description', ''))

        metadata = {
            "name": video_data['title'],
            "description": (
                f"YouTube video from @{video_data.get('channel_title', 'JimFlintLSG')}. "
                f"Published on {pub_date.strftime('%B %d, %Y')}. "
                f"This NFT represents verified content on the XRPL blockchain. "
                f"Original video: {video_data['video_url']}"
            ),
            "image": image_url,
            "external_url": video_data['video_url'],
            "attributes": [
                {"trait_type": "contextType", "value": "YouTube_NFT"},
                {"trait_type": "source", "value": video_data['video_url']},
                {"trait_type": "channel", "value": video_data.get('channel_title', 'JimFlintLSG')},
                {"trait_type": "videoId", "value": video_id},
                # {"trait_type": "category", "value": category},
                {"trait_type": "publishedDate", "value": pub_date.strftime('%Y-%m-%d')},
                {"trait_type": "accountXRPL", "value": xrpl.wallet.address}
            ]
        }

        # 3. Upload metadata to IPFS
        print(f"   📦 Uploading metadata to IPFS...")
        metadata_result = pinata.upload_json(
            json_data=metadata,
            name=f"metadata-{video_id}",
            keyvalues={"type": "youtube_nft_metadata", "video_id": video_id, "category": category}
        )
        metadata_ipfs_hash = metadata_result['IpfsHash']
        print(f"   ✅ Metadata: {metadata_ipfs_hash}")

        # 4. Create XRPL URI
        uri = f"ipfs://{metadata_ipfs_hash}"

        # 4a. Check for duplicate CID on-chain
        print(f"   🔍 Checking for duplicate CID on XRPL...")
        existing_onchain_nft = xrpl.find_nft_by_uri(uri)
        if existing_onchain_nft:
            nft_id = existing_onchain_nft.get('NFTokenID')
            print(f"   ⚠️  DUPLICATE DETECTED!")
            print(f"      CID: {metadata_ipfs_hash}")
            print(f"      Existing NFT ID: {nft_id}")
            print(f"      This CID is already minted on XRPL")

            # Check if it's in our database
            db_nft = mongodb.get_nft_by_nft_id(nft_id)
            if db_nft:
                print(f"      Found in database for video: {db_nft.get('video_id')}")
            else:
                print(f"      NOT in our database (minted elsewhere or orphaned)")

            # Ask user what to do
            print(f"\n   ❓ What would you like to do?")
            print(f"      1. Skip this video (will not retry)")
            print(f"      2. Continue anyway (will attempt to mint duplicate)")
            print(f"      3. Abort minting process")

            choice = input("\n   Enter choice (1/2/3): ").strip()

            if choice == "1":
                print(f"   ⏭️  Skipping video {video_id}")
                mongodb.mark_video_skipped(video_id, f"Duplicate CID: {metadata_ipfs_hash}")
                return None
            elif choice == "3":
                print(f"   🛑 Aborting minting process")
                raise Exception("User aborted minting due to duplicate CID")
            else:
                print(f"   ⚠️  Continuing with mint (may create duplicate)")

        # 5. Create unique taxon
        token_taxon = int(hashlib.sha256(video_id.encode()).hexdigest()[:8], 16)

        # # 6. Create compact MEMO (same format as reference code)
        # memo_data = {
        #     "id": video_id,
        #     "title": video_data['title'],
        #     "url": video_data['video_url'],
        #     "thumb": video_data['thumbnail_url'],
        #     "channel": video_data.get('channel_title', 'JimFlintLSG'),
        #     "date": pub_date.strftime('%Y-%m-%d'),
        #     "category": category
        # }
        
        memo_data = "This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger"

        # 7. Mint NFT on XRPL
        print(f"   ⛓️  Minting on XRPL...")
        mint_result = xrpl.mint_nft(
            uri=uri,
            taxon=0,
            memo_data=memo_data,
            memo_type="YouTubeNFTValidation"
        )

        nft_id = None
        tx_hash = None

        if not mint_result['success']:
            print(f"   ❌ Minting appears to have failed: {mint_result.get('error')}")

            # CRITICAL: Verify if transaction actually succeeded despite error
            # This handles network failures where TX succeeded but response failed
            if 'tx_hash' in mint_result and mint_result['tx_hash']:
                print(f"   🔍 Transaction was submitted, verifying on-chain status...")
                tx_hash = mint_result['tx_hash']
                verified_nft_id = xrpl.verify_transaction_success(tx_hash)

                if verified_nft_id:
                    print(f"   ✅ Transaction actually SUCCEEDED on-chain!")
                    print(f"      NFT ID: {verified_nft_id}")
                    print(f"      TX Hash: {tx_hash}")
                    nft_id = verified_nft_id
                else:
                    # Check if NFT with this URI exists (might have been minted in previous attempt)
                    print(f"   🔍 Checking if NFT already exists with this URI...")
                    existing_nft = xrpl.find_nft_by_uri(uri)
                    if existing_nft:
                        nft_id = existing_nft.get('NFTokenID')
                        print(f"   ✅ Found existing NFT with matching URI!")
                        print(f"      NFT ID: {nft_id}")
                        print(f"      This was likely minted in a previous attempt")
                    else:
                        print(f"   ❌ Transaction genuinely failed - NFT not found on-chain")
                        mongodb.log_minting_operation(video_id, False, error=mint_result.get('error'))
                        return None
            else:
                mongodb.log_minting_operation(video_id, False, error=mint_result.get('error'))
                return None
        else:
            nft_id = mint_result['nft_id']
            tx_hash = mint_result['tx_hash']
            print(f"   ✅ NFT Minted!")
            print(f"      NFT ID: {nft_id}")
            print(f"      TX Hash: {tx_hash}")

        # 8. Save to MongoDB
        print(f"   💾 Saving to MongoDB...")
        mongodb.save_video({**video_data, "category": category})

        nft_save_data = {
            "nft_id": nft_id,                               # XRPL NFT Token ID
            "video_id": video_id,                           # YouTube video ID
            "tx_hash": tx_hash,                             # XRPL transaction hash
            "uri": uri,                                     # ipfs://metadata_hash
            "metadata_ipfs_hash": metadata_ipfs_hash,       # Metadata IPFS hash
            "image_ipfs_hash": image_ipfs_hash,             # Image IPFS hash
            "taxon": token_taxon,                           # NFT taxon (from video_id hash)
            "account": xrpl.wallet.address,                 # Minting wallet address
            "minted_at": datetime.now(timezone.utc),        # Minting timestamp
            "metadata": metadata,                           # Full OpenSea metadata
            "memo_data": memo_data,                         # Compact memo (on-chain)
            "network": "testnet" if testnet else "mainnet"  # Network identifier
        }

        save_result = mongodb.save_nft(nft_save_data)
        if not save_result['success']:
            print(f"   ⚠️  MongoDB save warning: {save_result.get('error')}")

        mongodb.log_minting_operation(video_id, True, nft_id, tx_hash)

        print(f"   ✅ Saved to MongoDB")

        return {
            'success': True,
            'nft_id': nft_id,
            'tx_hash': tx_hash,
            'video_id': video_id
        }

    except Exception as e:
        print(f"   ❌ Error: {e}")
        mongodb.log_minting_operation(video_data['video_id'], False, error=str(e))
        return None


def sync_videos_to_mongodb(json_file: str, mongodb) -> Dict[str, Any]:
    """Sync videos from JSON file to MongoDB"""
    try:
        print(f"\n📥 Syncing videos from {json_file}...")
        with open(json_file, 'r') as f:
            raw_videos = json.load(f)

        print(f"   Found {len(raw_videos)} videos")

        synced = 0
        errors = 0

        for raw_video in raw_videos:
            try:
                # Transform YouTube API format to our format
                video_data = transform_youtube_video(raw_video)

                if video_data:
                    result = mongodb.save_video(video_data)
                    if result['success']:
                        synced += 1
                    else:
                        errors += 1
                        print(f"   ⚠️  Failed to save {video_data.get('video_id')}: {result.get('error')}")
                else:
                    errors += 1
            except Exception as e:
                errors += 1
                print(f"   ⚠️  Error processing video: {e}")

        print(f"   ✅ Synced {synced}/{len(raw_videos)} videos")
        if errors > 0:
            print(f"   ⚠️  {errors} errors")

        return {'success': True, 'total': len(raw_videos), 'synced': synced, 'errors': errors}
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {'success': False, 'error': str(e)}


def check_for_duplicate_cids(xrpl, mongodb) -> Dict[str, Any]:
    """
    Fetch all existing NFTs and check for potential duplicates

    Args:
        xrpl: XRPL service instance
        mongodb: MongoDB service instance

    Returns:
        Dict with existing NFT CIDs mapped to NFT IDs
    """
    print("\n🔍 Fetching existing NFTs from XRPL to check for duplicates...")

    result = xrpl.get_nfts()
    if not result['success']:
        print(f"   ⚠️  Could not fetch NFTs: {result.get('error')}")
        return {}

    nfts = result.get('nfts', [])
    print(f"   Found {len(nfts)} existing NFTs on XRPL")

    # Build CID -> NFT ID mapping
    cid_to_nft = {}

    for nft in nfts:
        try:
            from xrpl.utils import hex_to_str
            nft_uri = nft.get('URI', '')
            if nft_uri:
                decoded_uri = hex_to_str(nft_uri)
                # Extract CID from ipfs:// format
                cid = decoded_uri.replace('ipfs://', '').strip()
                nft_id = nft.get('NFTokenID')
                if cid and nft_id:
                    cid_to_nft[cid] = {
                        'nft_id': nft_id,
                        'uri': decoded_uri
                    }
        except Exception as e:
            continue

    print(f"   Indexed {len(cid_to_nft)} unique CIDs")
    return cid_to_nft


def sync_nfts_from_blockchain(xrpl, mongodb, testnet: bool = True) -> Dict[str, Any]:
    """
    Sync NFTs from blockchain to MongoDB

    Args:
        xrpl: XRPL service instance
        mongodb: MongoDB service instance
        testnet: Whether using testnet or mainnet

    Returns:
        Dict with sync analytics
    """
    print("\n" + "=" * 70)
    print("🔄 NFT Blockchain → MongoDB Sync")
    print("=" * 70)

    # Step 1: Fetch all NFTs from XRPL
    print("\n📡 Step 1: Fetching NFTs from XRPL blockchain...")
    result = xrpl.get_nfts()

    if not result['success']:
        print(f"   ❌ Error: {result.get('error')}")
        return {'success': False, 'error': result.get('error')}

    blockchain_nfts = result.get('nfts', [])
    print(f"   ✅ Found {len(blockchain_nfts)} NFTs on blockchain")

    # Step 2: Fetch all NFTs from MongoDB
    print("\n💾 Step 2: Fetching NFTs from MongoDB...")
    db_nfts = mongodb.get_all_nfts(limit=10000)
    db_nft_ids = {nft['nft_id'] for nft in db_nfts}
    print(f"   ✅ Found {len(db_nfts)} NFTs in database")

    # Step 3: Compare and analyze
    print("\n🔍 Step 3: Comparing blockchain vs database...")

    analytics = {
        'total_blockchain': len(blockchain_nfts),
        'total_database': len(db_nfts),
        'matched': 0,
        'missing_in_db': [],
        'extra_in_db': 0,
        'parse_errors': 0
    }

    from xrpl.utils import hex_to_str

    for nft in blockchain_nfts:
        nft_id = nft.get('NFTokenID')

        if nft_id in db_nft_ids:
            analytics['matched'] += 1
        else:
            # NFT on blockchain but not in database
            try:
                uri_hex = nft.get('URI', '')
                uri = hex_to_str(uri_hex) if uri_hex else ''

                analytics['missing_in_db'].append({
                    'nft_id': nft_id,
                    'uri': uri,
                    'flags': nft.get('Flags', 0),
                    'issuer': nft.get('Issuer', ''),
                    'nft_taxon': nft.get('NFTokenTaxon', 0),
                    'transfer_fee': nft.get('TransferFee', 0)
                })
            except Exception as e:
                analytics['parse_errors'] += 1
                analytics['missing_in_db'].append({
                    'nft_id': nft_id,
                    'uri': 'ERROR_PARSING',
                    'error': str(e)
                })

    # Check for NFTs in DB but not on blockchain (orphaned)
    blockchain_nft_ids = {nft.get('NFTokenID') for nft in blockchain_nfts}
    for db_nft_id in db_nft_ids:
        if db_nft_id not in blockchain_nft_ids:
            analytics['extra_in_db'] += 1

    # Step 4: Display analytics
    print("\n" + "=" * 70)
    print("📊 SYNC ANALYTICS")
    print("=" * 70)
    print(f"📡 NFTs on Blockchain:     {analytics['total_blockchain']}")
    print(f"💾 NFTs in Database:       {analytics['total_database']}")
    print(f"✅ Matched (in sync):      {analytics['matched']}")
    print(f"⚠️  Missing in DB:         {len(analytics['missing_in_db'])}")
    if analytics['extra_in_db'] > 0:
        print(f"🔍 Extra in DB (orphaned): {analytics['extra_in_db']}")
    if analytics['parse_errors'] > 0:
        print(f"❌ Parse Errors:           {analytics['parse_errors']}")
    print("=" * 70)

    # Step 5: Show missing NFTs if any
    if analytics['missing_in_db']:
        print(f"\n⚠️  {len(analytics['missing_in_db'])} NFT(s) on blockchain but NOT in database:")
        print("=" * 70)

        for i, missing_nft in enumerate(analytics['missing_in_db'][:10], 1):
            print(f"\n{i}. NFT ID: {missing_nft['nft_id']}")
            print(f"   URI: {missing_nft.get('uri', 'N/A')[:80]}...")

            # Try to find associated video
            if missing_nft.get('uri', '').startswith('ipfs://'):
                cid = missing_nft['uri'].replace('ipfs://', '').strip()
                # Check if video exists with this metadata CID
                video = mongodb.videos.find_one({"metadata_ipfs_hash": cid})
                if video:
                    print(f"   📺 Associated Video: {video.get('video_id')} - {video.get('title', 'Unknown')[:50]}")
                else:
                    print(f"   📺 Associated Video: Not found in database")

        if len(analytics['missing_in_db']) > 10:
            print(f"\n   ... and {len(analytics['missing_in_db']) - 10} more")

        print("\n" + "=" * 70)

        # Step 6: Prompt user for action
        print("\n❓ What would you like to do?")
        print("   1. Update ALL missing NFTs to database")
        print("   2. Select specific NFTs to update")
        print("   3. Show detailed info for each missing NFT")
        print("   4. Export missing NFT list to file")
        print("   5. Skip update (view only)")

        choice = input("\nEnter choice (1/2/3/4/5): ").strip()

        if choice == "1":
            # Update all missing NFTs
            return update_missing_nfts(analytics['missing_in_db'], mongodb, testnet, select_mode=False)

        elif choice == "2":
            # Select specific NFTs
            return update_missing_nfts(analytics['missing_in_db'], mongodb, testnet, select_mode=True)

        elif choice == "3":
            # Show detailed info
            show_detailed_nft_info(analytics['missing_in_db'], mongodb)
            return analytics

        elif choice == "4":
            # Export to file
            export_missing_nfts(analytics['missing_in_db'])
            return analytics

        else:
            print("\n✅ Skipping update - view only mode")
            return analytics

    else:
        print("\n✅ All blockchain NFTs are synced to database!")
        print("   No action needed.")

    return analytics


def update_missing_nfts(
    missing_nfts: List[Dict[str, Any]],
    mongodb,
    testnet: bool,
    select_mode: bool = False
) -> Dict[str, Any]:
    """
    Update missing NFTs to MongoDB

    Args:
        missing_nfts: List of missing NFT data
        mongodb: MongoDB service instance
        testnet: Whether using testnet
        select_mode: If True, allow user to select which NFTs to update

    Returns:
        Dict with update results
    """
    to_update = []

    if select_mode:
        print("\n📝 Select NFTs to update (enter numbers separated by comma, or 'all'):")
        for i, nft in enumerate(missing_nfts, 1):
            print(f"   {i}. {nft['nft_id'][:20]}... - {nft.get('uri', 'N/A')[:50]}")

        selection = input("\nEnter selection: ").strip()

        if selection.lower() == 'all':
            to_update = missing_nfts
        else:
            try:
                indices = [int(x.strip()) - 1 for x in selection.split(',')]
                to_update = [missing_nfts[i] for i in indices if 0 <= i < len(missing_nfts)]
            except Exception as e:
                print(f"❌ Invalid selection: {e}")
                return {'success': False, 'error': 'Invalid selection'}
    else:
        to_update = missing_nfts

    print(f"\n🔄 Updating {len(to_update)} NFT(s) to database...")

    updated_count = 0
    failed_count = 0

    for i, nft in enumerate(to_update, 1):
        print(f"\n[{i}/{len(to_update)}] Updating {nft['nft_id'][:20]}...")

        try:
            # Extract metadata CID from URI
            uri = nft.get('uri', '')
            metadata_ipfs_hash = uri.replace('ipfs://', '').strip() if uri.startswith('ipfs://') else ''

            # Try to find associated video by metadata CID
            video_id = None
            video_data = None

            if metadata_ipfs_hash:
                # Search in videos collection for matching metadata hash
                video_data = mongodb.videos.find_one({"metadata_ipfs_hash": metadata_ipfs_hash})
                if video_data:
                    video_id = video_data.get('video_id')
                    print(f"   ✅ Found associated video: {video_id}")

            # If no video found, create a placeholder entry
            if not video_id:
                # Generate a placeholder video_id from NFT ID
                video_id = f"unknown_{nft['nft_id'][:16]}"
                print(f"   ⚠️  No associated video found - using placeholder: {video_id}")

            # Prepare NFT data for MongoDB
            nft_save_data = {
                "nft_id": nft['nft_id'],
                "video_id": video_id,
                "tx_hash": "RECOVERED_FROM_BLOCKCHAIN",
                "uri": uri,
                "metadata_ipfs_hash": metadata_ipfs_hash,
                "image_ipfs_hash": "",  # Unknown from blockchain data
                "taxon": nft.get('nft_taxon', 0),
                "account": nft.get('issuer', ''),
                "minted_at": datetime.now(timezone.utc),  # Use current time as we don't have original
                "metadata": {},  # Would need to fetch from IPFS
                "memo_data": "",  # Not available from AccountNFTs
                "network": "testnet" if testnet else "mainnet",
                "synced_from_blockchain": True,  # Flag to indicate this was synced
                "sync_date": datetime.now(timezone.utc)
            }

            # Save to MongoDB
            save_result = mongodb.save_nft(nft_save_data)

            if save_result['success']:
                print(f"   ✅ Saved to MongoDB")
                updated_count += 1

                # Log the sync operation
                mongodb.log_minting_operation(
                    video_id,
                    True,
                    nft['nft_id'],
                    "SYNCED_FROM_BLOCKCHAIN",
                    error=None
                )
            else:
                print(f"   ❌ Failed: {save_result.get('error')}")
                failed_count += 1

        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            failed_count += 1

    print(f"\n" + "=" * 70)
    print("📊 UPDATE RESULTS")
    print("=" * 70)
    print(f"✅ Successfully updated: {updated_count}")
    print(f"❌ Failed: {failed_count}")
    print("=" * 70)

    return {
        'success': True,
        'updated': updated_count,
        'failed': failed_count
    }


def show_detailed_nft_info(missing_nfts: List[Dict[str, Any]], mongodb):
    """Show detailed information for each missing NFT"""
    print("\n" + "=" * 70)
    print("📋 DETAILED NFT INFORMATION")
    print("=" * 70)

    for i, nft in enumerate(missing_nfts, 1):
        print(f"\n{'=' * 70}")
        print(f"NFT #{i}")
        print(f"{'=' * 70}")
        print(f"NFT ID:       {nft['nft_id']}")
        print(f"URI:          {nft.get('uri', 'N/A')}")
        print(f"Issuer:       {nft.get('issuer', 'N/A')}")
        print(f"Taxon:        {nft.get('nft_taxon', 'N/A')}")
        print(f"Transfer Fee: {nft.get('transfer_fee', 0)}")
        print(f"Flags:        {nft.get('flags', 0)}")

        # Try to find associated video
        if nft.get('uri', '').startswith('ipfs://'):
            cid = nft['uri'].replace('ipfs://', '').strip()
            video = mongodb.videos.find_one({"metadata_ipfs_hash": cid})
            if video:
                print(f"\n📺 Associated Video:")
                print(f"   Video ID: {video.get('video_id')}")
                print(f"   Title:    {video.get('title', 'Unknown')}")
                print(f"   URL:      {video.get('video_url', 'N/A')}")

        if i < len(missing_nfts):
            input("\nPress Enter for next NFT...")


def export_missing_nfts(missing_nfts: List[Dict[str, Any]]):
    """Export missing NFTs to JSON file"""
    filename = f"missing_nfts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        with open(filename, 'w') as f:
            json.dump(missing_nfts, f, indent=2, default=str)

        print(f"\n✅ Exported {len(missing_nfts)} missing NFTs to: {filename}")
    except Exception as e:
        print(f"\n❌ Export failed: {str(e)}")


def display_status(mongodb):
    """Display minting status"""
    stats = mongodb.get_minting_stats()
    unminted = mongodb.get_unminted_videos(limit=5)

    print("\n" + "=" * 70)
    print("📊 YouTube NFT Minting Status")
    print("=" * 70)
    print(f"📺 Total Videos: {stats['total_videos']}")
    print(f"✅ Minted NFTs: {stats['total_nfts']}")
    print(f"⏳ Unminted: {stats['unminted_count']}")

    # Count skipped videos
    skipped_count = mongodb.videos.count_documents({"skip_minting": True})
    if skipped_count > 0:
        print(f"⏭️  Skipped: {skipped_count}")

    if stats['category_breakdown']:
        print(f"\n📂 Category Breakdown:")
        for cat in stats['category_breakdown']:
            print(f"   {cat['_id']}: {cat['count']} videos")

    if unminted:
        print(f"\n⏳ Next Unminted Videos:")
        for i, video in enumerate(unminted, 1):
            print(f"   {i}. {video['title'][:60]}...")

    print("=" * 70)


def confirm_mainnet_operation(operation: str) -> bool:
    """
    Require explicit confirmation for mainnet operations

    Args:
        operation: Description of the operation

    Returns:
        True if confirmed, False otherwise
    """
    print("\n" + "=" * 70)
    print("⚠️  MAINNET OPERATION WARNING")
    print("=" * 70)
    print(f"You are about to perform: {operation}")
    print("This will use REAL XRP on the XRPL mainnet.")
    print("Transactions are PERMANENT and CANNOT be reversed.")
    print("=" * 70)

    response = input("\nType 'CONFIRM' to proceed with mainnet operation: ")

    if response.strip() == "CONFIRM":
        print("✅ Mainnet operation confirmed")
        return True
    else:
        print("❌ Operation cancelled")
        return False


def main():
    """Main entry point"""
    print("🎨 YouTube NFT Minting Platform")
    print("=" * 70)

    # Initialize services
    print("Initializing services...")
    pinata = create_pinata_service()
    youtube = create_youtube_service()
    xrpl = create_xrpl_service()
    mongodb = create_mongodb_service()

    # Determine if testnet
    testnet = "testnet" in xrpl.node_url.lower() or "altnet" in xrpl.node_url.lower()

    print(f"\n✅ Services Ready")
    print(f"   Wallet: {xrpl.wallet.address}")
    print(f"   Network: {'Testnet' if testnet else 'Mainnet'}")

    # Mainnet safety check
    if not testnet:
        print("\n🔴 MAINNET MODE DETECTED")
        print("   Real XRP will be used for all transactions")
        print("   See MAINNET_DEPLOYMENT.md for safety guidelines")

    # Check arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "sync":
            json_file = sys.argv[2] if len(sys.argv) > 2 else "complete_videos.json"
            sync_videos_to_mongodb(json_file, mongodb)
            display_status(mongodb)

        elif command == "mint":
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 1

            # Mainnet confirmation required
            if not testnet:
                operation = f"Mint {count} NFT(s) on MAINNET"
                if not confirm_mainnet_operation(operation):
                    return

            # Pre-mint duplicate check
            print(f"\n🔍 Pre-minting duplicate check...")
            existing_cids = check_for_duplicate_cids(xrpl, mongodb)

            print(f"\n🚀 Minting {count} NFT(s)...")

            unminted = mongodb.get_unminted_videos(limit=count)
            if not unminted:
                print("✅ All videos already minted!")
                return

            success_count = 0
            skip_count = 0
            for i, video in enumerate(unminted, 1):
                print(f"\n[{i}/{len(unminted)}]")
                result = mint_video_nft(video, pinata, xrpl, mongodb, testnet)
                if result:
                    success_count += 1
                elif result is None:
                    # Check if video was skipped
                    video_data = mongodb.get_video(video['video_id'])
                    if video_data and video_data.get('skip_minting'):
                        skip_count += 1

            print(f"\n📊 Results:")
            print(f"   ✅ Minted successfully: {success_count}/{len(unminted)}")
            if skip_count > 0:
                print(f"   ⏭️  Skipped: {skip_count}/{len(unminted)}")
            print(f"   ❌ Failed: {len(unminted) - success_count - skip_count}/{len(unminted)}")
            display_status(mongodb)

        elif command == "status":
            display_status(mongodb)

        elif command == "sync-nfts":
            # Sync NFTs from blockchain to MongoDB
            sync_nfts_from_blockchain(xrpl, mongodb, testnet)

        else:
            print(f"❌ Unknown command: {command}")
            print_usage()

    else:
        print_usage()
        display_status(mongodb)

    mongodb.close()


def print_usage():
    """Print usage information"""
    print("\nUsage:")
    print("  python mint_nfts.py sync [json_file]     # Sync videos to MongoDB")
    print("  python mint_nfts.py mint [count]         # Mint NFTs")
    print("  python mint_nfts.py status               # Show status")
    print("  python mint_nfts.py sync-nfts            # Sync blockchain NFTs to MongoDB")
    print("\nExamples:")
    print("  python mint_nfts.py sync complete_videos.json")
    print("  python mint_nfts.py mint 1               # Mint first unminted")
    print("  python mint_nfts.py mint 10              # Mint 10 NFTs")
    print("  python mint_nfts.py status")
    print("  python mint_nfts.py sync-nfts            # Reconcile blockchain with database")
    print("\nNetwork Verification:")
    print("  python verify_network.py                 # Check network configuration")


if __name__ == "__main__":
    main()
