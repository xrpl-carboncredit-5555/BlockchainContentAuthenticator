#!/usr/bin/env python3
"""
Fetch complete video data from YouTube channel with all details
"""
import json
from dotenv import load_dotenv
from src.services import create_youtube_service

load_dotenv()


def fetch_complete_channel_data(channel_id: str, output_file: str = "complete_videos.json"):
    """
    Fetch all videos from a channel with complete details including statistics and content details
    """
    print("=" * 80)
    print("FETCHING COMPLETE VIDEO DATA FROM YOUTUBE")
    print("=" * 80)
    print(f"\nChannel ID: {channel_id}")

    youtube = create_youtube_service()

    # Step 1: Get all video IDs from the channel
    print("\n[1/3] Fetching all video IDs from channel...")
    playlist_videos = youtube.fetch_all_videos_from_channel(channel_id, max_results=50)
    print(f"✓ Found {len(playlist_videos)} videos in playlist")

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

            api_key = os.getenv("YOUTUBE_API_KEY")
            url = "https://www.googleapis.com/youtube/v3/videos"

            params = {
                "part": "snippet,contentDetails,statistics,status",
                "id": batch_str,
                "key": api_key
            }

            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if 'items' in data:
                complete_videos.extend(data['items'])
                print(f"  Progress: {len(complete_videos)}/{len(video_ids)} videos fetched")

        except Exception as e:
            print(f"  ⚠️  Error fetching batch: {str(e)}")
            continue

    print(f"✓ Successfully fetched {len(complete_videos)} complete video records")

    # Step 4: Save to file
    print(f"\n[3/3] Saving to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(complete_videos, f, indent=2, ensure_ascii=False)

    print(f"✓ Data saved successfully!")

    # Quick analysis
    print("\n" + "=" * 80)
    print("QUICK ANALYSIS")
    print("=" * 80)

    shorts_count = 0
    regular_count = 0
    live_count = 0

    for video in complete_videos:
        snippet = video.get('snippet', {})
        content_details = video.get('contentDetails', {})

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

    print(f"\nTotal Videos: {len(complete_videos)}")
    print(f"  Shorts: {shorts_count}")
    print(f"  Regular Videos: {regular_count}")
    print(f"  Live Streams: {live_count}")

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
    except:
        pass
    return None


if __name__ == "__main__":
    import sys

    # Default channel ID
    channel_id = "UCcjrHH8MSp8UZdFre4OkT7g"

    if len(sys.argv) > 1:
        channel_id = sys.argv[1]

    try:
        fetch_complete_channel_data(channel_id)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
