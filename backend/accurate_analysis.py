#!/usr/bin/env python3
"""
Accurate analysis based on YouTube's actual video duration data
"""
import json
from datetime import datetime
from collections import defaultdict


def analyze_videos_accurately(json_file_path):
    """
    Analyze videos using actual duration from contentDetails
    YouTube considers videos <= 60 seconds as Shorts
    """
    print("=" * 80)
    print("ACCURATE VIDEO ANALYTICS REPORT")
    print("=" * 80)

    # Load JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        videos = json.load(f)

    total_count = len(videos)
    print(f"\n📊 TOTAL VIDEOS: {total_count}")
    print("=" * 80)

    # Classification based on duration
    shorts = []
    regular_videos = []
    live_videos = []
    unknown = []

    total_views = 0
    total_likes = 0
    total_comments = 0

    years = defaultdict(int)
    months = defaultdict(int)

    for video in videos:
        snippet = video.get('snippet', {})
        content_details = video.get('contentDetails', {})
        statistics = video.get('statistics', {})
        video_id = video.get('id', 'unknown')

        # Get duration
        duration_str = content_details.get('duration', '')
        seconds = parse_duration(duration_str)

        # Check if it's a live broadcast
        live_broadcast = snippet.get('liveBroadcastContent', 'none')

        video_info = {
            'id': video_id,
            'title': snippet.get('title', 'Unknown'),
            'published': snippet.get('publishedAt', ''),
            'duration_seconds': seconds,
            'duration_str': duration_str,
            'views': int(statistics.get('viewCount', 0)),
            'likes': int(statistics.get('likeCount', 0)),
            'comments': int(statistics.get('commentCount', 0)),
            'live_broadcast': live_broadcast
        }

        # Classify based on actual YouTube criteria
        if live_broadcast in ['live', 'upcoming']:
            live_videos.append(video_info)
        elif 'liveStreamingDetails' in video:
            live_videos.append(video_info)
        elif seconds and seconds <= 60:
            shorts.append(video_info)
        elif seconds and seconds > 60:
            regular_videos.append(video_info)
        else:
            unknown.append(video_info)

        # Statistics
        total_views += video_info['views']
        total_likes += video_info['likes']
        total_comments += video_info['comments']

        # Date analysis
        published_at = snippet.get('publishedAt', '')
        if published_at:
            try:
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                years[dt.year] += 1
                months[f"{dt.year}-{dt.month:02d}"] += 1
            except:
                pass

    # Print results
    print("\n📹 VIDEO TYPE BREAKDOWN (Based on Duration):")
    print("-" * 80)
    print(f"  {'Shorts (<= 60s)':<30} : {len(shorts):>6} ({len(shorts)/total_count*100:>5.1f}%)")
    print(f"  {'Regular Videos (> 60s)':<30} : {len(regular_videos):>6} ({len(regular_videos)/total_count*100:>5.1f}%)")
    print(f"  {'Live Streams':<30} : {len(live_videos):>6} ({len(live_videos)/total_count*100:>5.1f}%)")
    if unknown:
        print(f"  {'Unknown/No Duration':<30} : {len(unknown):>6} ({len(unknown)/total_count*100:>5.1f}%)")

    print("\n⏱️  DURATION BREAKDOWN (Regular Videos Only):")
    print("-" * 80)
    short_vids = [v for v in regular_videos if v['duration_seconds'] <= 600]  # <= 10 min
    medium_vids = [v for v in regular_videos if 600 < v['duration_seconds'] <= 1800]  # 10-30 min
    long_vids = [v for v in regular_videos if v['duration_seconds'] > 1800]  # > 30 min

    print(f"  {'Short (1-10 min)':<30} : {len(short_vids):>6} ({len(short_vids)/total_count*100:>5.1f}%)")
    print(f"  {'Medium (10-30 min)':<30} : {len(medium_vids):>6} ({len(medium_vids)/total_count*100:>5.1f}%)")
    print(f"  {'Long (> 30 min)':<30} : {len(long_vids):>6} ({len(long_vids)/total_count*100:>5.1f}%)")

    print("\n📈 ENGAGEMENT STATISTICS:")
    print("-" * 80)
    print(f"  Total Views              : {total_views:>15,}")
    print(f"  Total Likes              : {total_likes:>15,}")
    print(f"  Total Comments           : {total_comments:>15,}")
    print()
    print(f"  Avg Views/Video          : {total_views/total_count:>15,.0f}")
    print(f"  Avg Likes/Video          : {total_likes/total_count:>15,.0f}")
    print(f"  Avg Comments/Video       : {total_comments/total_count:>15,.0f}")
    if total_views > 0:
        print(f"  Like Rate (%)            : {(total_likes/total_views)*100:>15,.2f}%")
        print(f"  Comment Rate (%)         : {(total_comments/total_views)*100:>15,.2f}%")

    print("\n📅 VIDEOS BY YEAR:")
    print("-" * 80)
    for year in sorted(years.keys()):
        count = years[year]
        percentage = (count / total_count) * 100
        print(f"  {year:<20} : {count:>6} ({percentage:>5.1f}%)")

    print("\n📆 TOP 10 MONTHS BY VIDEO COUNT:")
    print("-" * 80)
    sorted_months = sorted(months.items(), key=lambda x: x[1], reverse=True)[:10]
    for month, count in sorted_months:
        percentage = (count / total_count) * 100
        print(f"  {month:<20} : {count:>6} ({percentage:>5.1f}%)")

    # Sample videos from each category
    print("\n📝 SAMPLE VIDEOS BY CATEGORY:")
    print("-" * 80)

    if shorts:
        print("\n  SHORTS (Sample - <= 60 seconds):")
        for i, v in enumerate(shorts[:3], 1):
            print(f"    {i}. {v['title'][:70]}")
            print(f"       Duration: {v['duration_seconds']}s | Views: {v['views']:,} | ID: {v['id']}")

    if regular_videos:
        print("\n  REGULAR VIDEOS (Sample - > 60 seconds):")
        for i, v in enumerate(regular_videos[:3], 1):
            print(f"    {i}. {v['title'][:70]}")
            duration_min = v['duration_seconds'] // 60
            duration_sec = v['duration_seconds'] % 60
            print(f"       Duration: {duration_min}m {duration_sec}s | Views: {v['views']:,} | ID: {v['id']}")

    if live_videos:
        print("\n  LIVE STREAMS (Sample):")
        for i, v in enumerate(live_videos[:3], 1):
            print(f"    {i}. {v['title'][:70]}")
            print(f"       Live Status: {v['live_broadcast']} | Views: {v['views']:,} | ID: {v['id']}")

    # Top videos by views
    print("\n🏆 TOP 10 VIDEOS BY VIEWS:")
    print("-" * 80)
    all_videos = shorts + regular_videos + live_videos
    all_videos.sort(key=lambda x: x['views'], reverse=True)

    for i, v in enumerate(all_videos[:10], 1):
        video_type = "Short" if v in shorts else ("Live" if v in live_videos else "Regular")
        print(f"\n  {i}. [{video_type}] {v['title'][:60]}")
        print(f"     Views: {v['views']:,} | Likes: {v['likes']:,} | Comments: {v['comments']:,}")
        if v['duration_seconds']:
            if v['duration_seconds'] <= 60:
                print(f"     Duration: {v['duration_seconds']}s | Video ID: {v['id']}")
            else:
                duration_min = v['duration_seconds'] // 60
                duration_sec = v['duration_seconds'] % 60
                print(f"     Duration: {duration_min}m {duration_sec}s | Video ID: {v['id']}")

    # Top shorts by views
    if shorts:
        print("\n🎬 TOP 10 SHORTS BY VIEWS:")
        print("-" * 80)
        shorts.sort(key=lambda x: x['views'], reverse=True)
        for i, v in enumerate(shorts[:10], 1):
            print(f"\n  {i}. {v['title'][:65]}")
            print(f"     Views: {v['views']:,} | Likes: {v['likes']:,} | Duration: {v['duration_seconds']}s")
            print(f"     Video ID: {v['id']}")

    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(shorts)} Shorts | {len(regular_videos)} Regular Videos | {len(live_videos)} Live Streams")
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

    json_file = "complete_videos.json"
    if len(sys.argv) > 1:
        json_file = sys.argv[1]

    try:
        analyze_videos_accurately(json_file)
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file}' not found")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format - {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
