#!/usr/bin/env python3
"""
Analyze videos.json and provide comprehensive analytics
"""
import json
from datetime import datetime
from collections import defaultdict


def analyze_videos(json_file_path):
    """
    Analyze videos.json and provide comprehensive statistics
    """
    print("=" * 80)
    print("VIDEO ANALYTICS REPORT")
    print("=" * 80)

    # Load JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different JSON structures
    if isinstance(data, dict):
        if 'items' in data:
            videos = data['items']
        elif 'videos' in data:
            videos = data['videos']
        else:
            # Assume the dict itself contains video data
            videos = [data]
    elif isinstance(data, list):
        videos = data
    else:
        print("❌ Unsupported JSON structure")
        return

    total_count = len(videos)
    print(f"\n📊 TOTAL VIDEOS: {total_count}")
    print("=" * 80)

    # Initialize counters
    video_types = defaultdict(int)
    durations = {
        'shorts': 0,  # <= 60 seconds
        'short_videos': 0,  # 1-10 minutes
        'medium_videos': 0,  # 10-30 minutes
        'long_videos': 0,  # > 30 minutes
        'live_streams': 0
    }

    privacy_status = defaultdict(int)
    years = defaultdict(int)
    months = defaultdict(int)

    total_views = 0
    total_likes = 0
    total_comments = 0

    has_views = 0
    has_likes = 0
    has_comments = 0

    # Analyze each video
    shorts_keywords = ['#shorts', '#short', 'shorts', '(short)']
    live_keywords = ['live', 'livestream', 'live stream']

    for idx, video in enumerate(videos):
        # Try to determine structure
        snippet = video.get('snippet', {})
        content_details = video.get('contentDetails', {})
        statistics = video.get('statistics', {})
        status = video.get('status', {})

        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()

        # Video type detection based on title/description
        is_short = False
        is_live = False

        # Check for shorts indicators
        for keyword in shorts_keywords:
            if keyword in title or keyword in description:
                is_short = True
                video_types['shorts'] += 1
                durations['shorts'] += 1
                break

        # Check for live stream indicators
        if not is_short:
            for keyword in live_keywords:
                if keyword in title or keyword in description:
                    is_live = True
                    video_types['live/stream'] += 1
                    durations['live_streams'] += 1
                    break

        # If neither short nor live, it's a regular video
        if not is_short and not is_live:
            video_types['regular_video'] += 1

        # Check if it's a live stream from API data
        live_broadcast = snippet.get('liveBroadcastContent', 'none')
        if live_broadcast in ['live', 'upcoming'] and not is_live:
            video_types['live'] += 1
            durations['live_streams'] += 1
            is_live = True
        elif live_broadcast == 'none' and 'liveStreamingDetails' in video and not is_live:
            video_types['past_live'] += 1
            is_live = True

        # Duration analysis (only if duration field exists)
        duration_str = content_details.get('duration', '')
        if duration_str and not is_short:
            seconds = parse_duration(duration_str)
            if seconds:
                if seconds <= 60 and not is_short:
                    durations['shorts'] += 1
                    video_types['shorts'] += 1
                elif seconds <= 600:  # 10 minutes
                    durations['short_videos'] += 1
                elif seconds <= 1800:  # 30 minutes
                    durations['medium_videos'] += 1
                else:
                    durations['long_videos'] += 1

        # Privacy status
        privacy = status.get('privacyStatus', 'unknown')
        privacy_status[privacy] += 1

        # Published date analysis
        published_at = snippet.get('publishedAt', '')
        if published_at:
            try:
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                years[dt.year] += 1
                months[f"{dt.year}-{dt.month:02d}"] += 1
            except:
                pass

        # Statistics
        try:
            views = int(statistics.get('viewCount', 0))
            likes = int(statistics.get('likeCount', 0))
            comments = int(statistics.get('commentCount', 0))

            if views > 0:
                total_views += views
                has_views += 1
            if likes > 0:
                total_likes += likes
                has_likes += 1
            if comments > 0:
                total_comments += comments
                has_comments += 1
        except:
            pass

    # Print results
    print("\n📹 VIDEO TYPES:")
    print("-" * 80)
    for vtype, count in sorted(video_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_count) * 100
        print(f"  {vtype.upper():<20} : {count:>6} ({percentage:>5.1f}%)")

    print("\n⏱️  VIDEO DURATIONS:")
    print("-" * 80)
    print(f"  {'Shorts (<= 60s)':<20} : {durations['shorts']:>6} ({(durations['shorts']/total_count)*100:>5.1f}%)")
    print(f"  {'Short (1-10 min)':<20} : {durations['short_videos']:>6} ({(durations['short_videos']/total_count)*100:>5.1f}%)")
    print(f"  {'Medium (10-30 min)':<20} : {durations['medium_videos']:>6} ({(durations['medium_videos']/total_count)*100:>5.1f}%)")
    print(f"  {'Long (> 30 min)':<20} : {durations['long_videos']:>6} ({(durations['long_videos']/total_count)*100:>5.1f}%)")
    if durations['live_streams'] > 0:
        print(f"  {'Live Streams':<20} : {durations['live_streams']:>6} ({(durations['live_streams']/total_count)*100:>5.1f}%)")

    print("\n🔒 PRIVACY STATUS:")
    print("-" * 80)
    for status, count in sorted(privacy_status.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_count) * 100
        print(f"  {status.upper():<20} : {count:>6} ({percentage:>5.1f}%)")

    print("\n📈 ENGAGEMENT STATISTICS:")
    print("-" * 80)
    print(f"  Total Views          : {total_views:>15,}")
    print(f"  Total Likes          : {total_likes:>15,}")
    print(f"  Total Comments       : {total_comments:>15,}")
    print()
    if has_views > 0:
        print(f"  Avg Views/Video      : {total_views/has_views:>15,.0f}")
    if has_likes > 0:
        print(f"  Avg Likes/Video      : {total_likes/has_likes:>15,.0f}")
    if has_comments > 0:
        print(f"  Avg Comments/Video   : {total_comments/has_comments:>15,.0f}")
    if total_views > 0 and total_likes > 0:
        print(f"  Like Rate (%)        : {(total_likes/total_views)*100:>15,.2f}%")
    if total_views > 0 and total_comments > 0:
        print(f"  Comment Rate (%)     : {(total_comments/total_views)*100:>15,.2f}%")

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

    # Show sample videos by category
    print("\n📝 SAMPLE VIDEOS BY CATEGORY:")
    print("-" * 80)

    # Collect sample shorts
    sample_shorts = []
    sample_regular = []
    sample_live = []

    for video in videos:
        snippet = video.get('snippet', {})
        content_details = video.get('contentDetails', {})
        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()
        video_id = content_details.get('videoId', snippet.get('resourceId', {}).get('videoId', 'unknown'))

        is_short = any(kw in title or kw in description for kw in shorts_keywords)
        is_live = any(kw in title or kw in description for kw in live_keywords)

        if is_short and len(sample_shorts) < 3:
            sample_shorts.append({
                'title': snippet.get('title', 'Unknown'),
                'published': snippet.get('publishedAt', ''),
                'video_id': video_id
            })
        elif is_live and len(sample_live) < 3:
            sample_live.append({
                'title': snippet.get('title', 'Unknown'),
                'published': snippet.get('publishedAt', ''),
                'video_id': video_id
            })
        elif not is_short and not is_live and len(sample_regular) < 3:
            sample_regular.append({
                'title': snippet.get('title', 'Unknown'),
                'published': snippet.get('publishedAt', ''),
                'video_id': video_id
            })

    if sample_shorts:
        print("\n  SHORTS (Sample):")
        for i, v in enumerate(sample_shorts, 1):
            print(f"    {i}. {v['title']}")
            print(f"       Published: {v['published'][:10]} | ID: {v['video_id']}")

    if sample_regular:
        print("\n  REGULAR VIDEOS (Sample):")
        for i, v in enumerate(sample_regular, 1):
            print(f"    {i}. {v['title']}")
            print(f"       Published: {v['published'][:10]} | ID: {v['video_id']}")

    if sample_live:
        print("\n  LIVE/STREAM VIDEOS (Sample):")
        for i, v in enumerate(sample_live, 1):
            print(f"    {i}. {v['title']}")
            print(f"       Published: {v['published'][:10]} | ID: {v['video_id']}")

    # Find top videos if statistics available
    if has_views > 0:
        print("\n🏆 TOP 10 VIDEOS BY VIEWS:")
        print("-" * 80)
        videos_with_stats = []
        for video in videos:
            snippet = video.get('snippet', {})
            statistics = video.get('statistics', {})
            try:
                views = int(statistics.get('viewCount', 0))
                if views > 0:
                    videos_with_stats.append({
                        'title': snippet.get('title', 'Unknown'),
                        'views': views,
                        'likes': int(statistics.get('likeCount', 0)),
                        'comments': int(statistics.get('commentCount', 0)),
                        'video_id': video.get('id', snippet.get('resourceId', {}).get('videoId', 'unknown'))
                    })
            except:
                pass

        videos_with_stats.sort(key=lambda x: x['views'], reverse=True)
        for i, v in enumerate(videos_with_stats[:10], 1):
            print(f"\n  {i}. {v['title'][:60]}")
            print(f"     Views: {v['views']:,} | Likes: {v['likes']:,} | Comments: {v['comments']:,}")
            print(f"     Video ID: {v['video_id']}")

    print("\n" + "=" * 80)
    print("END OF REPORT")
    print("=" * 80)


def parse_duration(duration_str):
    """
    Parse ISO 8601 duration format (e.g., PT1H2M10S) to seconds
    """
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
        analyze_videos(json_file)
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file}' not found")
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format - {str(e)}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
