#!/usr/bin/env python3
"""
Fetch complete video data from YouTube channel with all details
Supports fetching private and scheduled videos with OAuth authentication
"""
import json
import argparse
from dotenv import load_dotenv
from src.services import create_youtube_service
from src.services.youtube_auth import get_youtube_token

load_dotenv()


def fetch_complete_channel_data(
    channel_id: str,
    output_file: str = "complete_videos.json",
    include_private: bool = False
):
    """
    Fetch all videos from a channel with complete details including
    statistics and content details

    Args:
        channel_id: YouTube channel ID
        output_file: Output JSON file path
        include_private: If True, uses OAuth to fetch private/scheduled
            videos too
    """
    print("=" * 80)
    print("FETCHING COMPLETE VIDEO DATA FROM YOUTUBE")
    print("=" * 80)
    print(f"\nChannel ID: {channel_id}")
    print(f"Include Private/Scheduled: {include_private}")

    # Get OAuth token if needed
    oauth_token = None
    if include_private:
        print("\n🔐 OAuth authentication required for private videos...")
        oauth_token = get_youtube_token()
        if not oauth_token:
            print(
                "❌ Failed to get OAuth token. "
                "Private videos will not be fetched."
            )
            print("   Run: python get_youtube_oauth_token.py")
            print("   Falling back to public videos only...")
            include_private = False
        else:
            print("✅ OAuth token obtained successfully")

    youtube = create_youtube_service(oauth_token=oauth_token)

    # Step 1: Get all video IDs from the channel
    print("\n[1/3] Fetching all video IDs from channel...")
    if include_private:
        print(
            "   📹 Fetching ALL videos "
            "(public, private, unlisted, scheduled)..."
        )
    else:
        print("   📹 Fetching public videos only...")

    playlist_videos = youtube.fetch_all_videos_from_channel(
        channel_id,
        max_results=50,
        include_private=include_private
    )
    print(f"✓ Found {len(playlist_videos)} videos")

    # Step 2: Extract video IDs
    video_ids = []
    for item in playlist_videos:
        video_id = item.get('contentDetails', {}).get('videoId')
        if not video_id:
            video_id = item.get('snippet', {}).get('resourceId', {}).get('videoId')
        if video_id:
            video_ids.append(video_id)

    print(f"✓ Extracted {len(video_ids)} unique video IDs")

    # Step 3: Fetch complete details for all videos
    print("\n[2/3] Fetching complete details for all videos...")
    print("This may take a while...")

    complete_videos = []
    batch_size = 50  # YouTube API allows fetching up to 50 videos at once

    for i in range(0, len(video_ids), batch_size):
        batch = video_ids[i:i + batch_size]
        batch_str = ",".join(batch)

        try:
            # Fetch video details with all parts
            import requests
            import os

            url = "https://www.googleapis.com/youtube/v3/videos"

            params = {
                "part": "snippet,contentDetails,statistics,status",
                "id": batch_str,
            }
            
            headers = {}
            # Use OAuth if available for private video details
            if oauth_token:
                headers["Authorization"] = f"Bearer {oauth_token}"
            else:
                params["key"] = os.getenv("YOUTUBE_API_KEY")

            response = requests.get(
                url,
                params=params,
                headers=headers if headers else None
            )
            response.raise_for_status()
            data = response.json()

            if 'items' in data:
                complete_videos.extend(data['items'])
                progress = f"{len(complete_videos)}/{len(video_ids)}"
                print(f"  Progress: {progress} videos fetched")

        except Exception as e:
            print(f"  ⚠️  Error fetching batch: {str(e)}")
            continue

    records_msg = (
        f"✓ Successfully fetched {len(complete_videos)} "
        "complete video records"
    )
    print(records_msg)

    # Step 4: Filter videos - keep only public and scheduled
    print("\n[3/4] Filtering videos...")
    if include_private:
        print("   🔍 Filtering: Keeping public and scheduled videos only")
        print("   🗑️  Removing: private, unlisted, and drafted videos")
        
        filtered_videos = []
        removed_private = 0
        removed_unlisted = 0
        removed_draft = 0
        kept_scheduled = 0
        
        for video in complete_videos:
            status = video.get('status', {})
            privacy_status = status.get('privacyStatus', '')
            publish_at = status.get('publishAt')
            upload_status = status.get('uploadStatus', '')
            
            # Check if it's a draft
            if upload_status == 'draft':
                removed_draft += 1
                continue
            
            # Check if it's scheduled (private with publishAt date)
            if privacy_status == 'private' and publish_at:
                filtered_videos.append(video)
                kept_scheduled += 1
                continue
            
            # Keep public videos
            if privacy_status == 'public':
                filtered_videos.append(video)
                continue
            
            # Remove other private videos (non-scheduled)
            if privacy_status == 'private':
                removed_private += 1
                continue
            
            # Remove unlisted videos
            if privacy_status == 'unlisted':
                removed_unlisted += 1
                continue
        
        print(f"   ✓ Kept {len(filtered_videos)} videos")
        print(f"   ✓ Scheduled videos found: {kept_scheduled}")
        print(f"   ✗ Removed {removed_private} private")
        print(f"   ✗ Removed {removed_unlisted} unlisted")
        print(f"   ✗ Removed {removed_draft} drafted")
        
        complete_videos = filtered_videos
    else:
        print("   ℹ️  No filtering applied (public videos only mode)")

    # Step 5: Save to file
    print(f"\n[4/4] Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_videos, f, indent=2, ensure_ascii=False)

    print("✓ Data saved successfully!")

    # Quick analysis
    print("\n" + "=" * 80)
    print("FINAL VIDEO ANALYSIS")
    if include_private:
        print("(After filtering - Public + Scheduled only)")
    print("=" * 80)

    shorts_count = 0
    regular_count = 0
    live_count = 0
    scheduled_count = 0
    public_count = 0

    for video in complete_videos:
        snippet = video.get('snippet', {})
        content_details = video.get('contentDetails', {})
        status = video.get('status', {})

        # Get privacy status
        privacy_status = status.get('privacyStatus', 'unknown')
        if privacy_status == 'public':
            public_count += 1
        
        # Check if scheduled (private with publishAt)
        if status.get('publishAt'):
            scheduled_count += 1

        # Get duration
        duration_str = content_details.get('duration', '')
        title = snippet.get('title', '').lower()

        # Parse duration
        seconds = parse_duration(duration_str)

        # Classify video
        if seconds and seconds <= 60:
            shorts_count += 1
        elif '#shorts' in title or 'shorts' in title:
            shorts_count += 1
        elif 'live' in title.lower():
            live_count += 1
        else:
            regular_count += 1

    print(f"\nTotal Videos in Final Output: {len(complete_videos)}")
    
    print("\nBy Type:")
    print(f"  Shorts: {shorts_count}")
    print(f"  Regular Videos: {regular_count}")
    print(f"  Live Streams: {live_count}")

    print("\nBy Status:")
    print(f"  Public (Live Now): {public_count}")
    print(f"  Scheduled (Future): {scheduled_count}")
    
    if include_private and scheduled_count > 0:
        print(
            "\n📅 Note: Scheduled videos will be "
            "published at their set dates"
        )

    print("\n" + "=" * 80)
    print("COMPLETE!")
    print("=" * 80)


def parse_duration(duration_str):
    """Parse ISO 8601 duration format to seconds"""
    try:
        import re
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
    except (AttributeError, ValueError, TypeError):
        pass
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch complete video data from YouTube channel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch only public videos (default)
  python fetch_complete_videos.py
  
  # Fetch public + scheduled videos (requires OAuth)
  # Note: Filters out private, unlisted, and drafted videos
  python fetch_complete_videos.py --include-private
  
  # Specify custom channel ID
  python fetch_complete_videos.py \\
      --channel-id UCxxxxxxxxxxxxx --include-private
  
  # Custom output file
  python fetch_complete_videos.py \\
      --include-private --output my_videos.json

What gets included with --include-private:
  ✓ Public videos (already live)
  ✓ Scheduled videos (set to publish in future)
  ✗ Private videos (not scheduled)
  ✗ Unlisted videos
  ✗ Drafted videos

Note: To use --include-private, you must first authenticate with:
  python get_youtube_oauth_token.py
        """
    )

    parser.add_argument(
        "--channel-id",
        default="UCcjrHH8MSp8UZdFre4OkT7g",
        help="YouTube channel ID (default: UCcjrHH8MSp8UZdFre4OkT7g)"
    )

    parser.add_argument(
        "--output",
        "-o",
        default="complete_videos.json",
        help="Output JSON file path (default: complete_videos.json)"
    )

    parser.add_argument(
        "--include-private",
        action="store_true",
        help=(
            "Include scheduled videos. Filters out private, unlisted, "
            "and drafted videos. Only keeps public + scheduled "
            "(requires OAuth authentication)"
        )
    )

    args = parser.parse_args()

    try:
        fetch_complete_channel_data(
            channel_id=args.channel_id,
            output_file=args.output,
            include_private=args.include_private
        )
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
