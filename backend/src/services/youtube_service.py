import os
import requests
from typing import Dict, Any, List, Optional


class YouTubeService:
    """Service for interacting with YouTube Data API v3"""

    def __init__(self, api_key: str):
        """
        Initialize YouTube service

        Args:
            api_key: YouTube Data API key
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def get_channel_uploads_playlist_id(self, channel_id: str) -> str:
        """
        Get the uploads playlist ID for a channel

        Args:
            channel_id: YouTube channel ID

        Returns:
            Uploads playlist ID
        """
        params = {
            "part": "contentDetails",
            "id": channel_id,
            "key": self.api_key
        }

        try:
            response = requests.get(
                f"{self.base_url}/channels",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("items"):
                raise Exception(f"Channel not found: {channel_id}")

            uploads_playlist_id = data["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            return uploads_playlist_id
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get channel info: {str(e)}")

    def fetch_all_videos_from_channel(
        self,
        channel_id: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch all video IDs from a channel's uploads playlist

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum results per page (1-50)

        Returns:
            List of video items with video IDs and basic info
        """
        uploads_playlist_id = self.get_channel_uploads_playlist_id(channel_id)

        all_videos = []
        next_page_token = None

        while True:
            params = {
                "part": "snippet,contentDetails",
                "playlistId": uploads_playlist_id,
                "maxResults": min(max_results, 50),
                "key": self.api_key
            }

            if next_page_token:
                params["pageToken"] = next_page_token

            try:
                response = requests.get(
                    f"{self.base_url}/playlistItems",
                    params=params
                )
                response.raise_for_status()
                data = response.json()

                all_videos.extend(data.get("items", []))

                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break

            except requests.exceptions.RequestException as e:
                raise Exception(f"Failed to fetch videos: {str(e)}")

        return all_videos

    def get_video_details(
        self,
        video_id: str,
        include_parts: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a video including description

        Args:
            video_id: YouTube video ID
            include_parts: Parts to include (snippet, contentDetails, statistics, etc.)

        Returns:
            Dict with video details
        """
        if include_parts is None:
            include_parts = ["snippet", "contentDetails", "statistics"]

        params = {
            "part": ",".join(include_parts),
            "id": video_id,
            "key": self.api_key
        }

        try:
            response = requests.get(
                f"{self.base_url}/videos",
                params=params
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("items"):
                raise Exception(f"Video not found: {video_id}")

            return data["items"][0]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get video details: {str(e)}")

    def get_video_description(self, video_id: str) -> str:
        """
        Get the description of a specific video

        Args:
            video_id: YouTube video ID

        Returns:
            Video description text
        """
        video_details = self.get_video_details(video_id, include_parts=["snippet"])
        return video_details["snippet"]["description"]

    def get_multiple_video_descriptions(
        self,
        video_ids: List[str]
    ) -> Dict[str, str]:
        """
        Get descriptions for multiple videos

        Args:
            video_ids: List of YouTube video IDs

        Returns:
            Dict mapping video IDs to descriptions
        """
        descriptions = {}
        for video_id in video_ids:
            try:
                descriptions[video_id] = self.get_video_description(video_id)
            except Exception as e:
                descriptions[video_id] = f"Error: {str(e)}"

        return descriptions

    def update_video_description(
        self,
        video_id: str,
        new_description: str,
        oauth_token: str
    ) -> Dict[str, Any]:
        """
        Update a video's description
        Note: Requires OAuth 2.0 authentication token

        Args:
            video_id: YouTube video ID
            new_description: New description text
            oauth_token: OAuth 2.0 access token

        Returns:
            Dict with updated video details
        """
        # First, get current video details
        current_video = self.get_video_details(video_id, include_parts=["snippet"])

        # Update the description while keeping other fields
        snippet = current_video["snippet"]
        snippet["description"] = new_description

        payload = {
            "id": video_id,
            "snippet": {
                "title": snippet["title"],
                "description": new_description,
                "categoryId": snippet["categoryId"],
                "tags": snippet.get("tags", []),
            }
        }

        headers = {
            "Authorization": f"Bearer {oauth_token}",
            "Content-Type": "application/json"
        }

        params = {
            "part": "snippet"
        }

        try:
            response = requests.put(
                f"{self.base_url}/videos",
                params=params,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to update video description: {str(e)}")

    def append_to_video_description(
        self,
        video_id: str,
        text_to_append: str,
        oauth_token: str,
        separator: str = "\n\n"
    ) -> Dict[str, Any]:
        """
        Append text to a video's existing description

        Args:
            video_id: YouTube video ID
            text_to_append: Text to append to description
            oauth_token: OAuth 2.0 access token
            separator: Separator between old and new text

        Returns:
            Dict with updated video details
        """
        current_description = self.get_video_description(video_id)
        new_description = current_description + separator + text_to_append

        return self.update_video_description(video_id, new_description, oauth_token)

    def fetch_channel_videos_with_descriptions(
        self,
        channel_id: str,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Fetch all videos from a channel with their descriptions

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum results per page

        Returns:
            List of dicts with video ID, title, and description
        """
        videos = self.fetch_all_videos_from_channel(channel_id, max_results)

        videos_with_descriptions = []
        for video in videos:
            video_id = video["contentDetails"]["videoId"]
            try:
                details = self.get_video_details(video_id, include_parts=["snippet"])
                videos_with_descriptions.append({
                    "videoId": video_id,
                    "title": details["snippet"]["title"],
                    "description": details["snippet"]["description"],
                    "publishedAt": details["snippet"]["publishedAt"],
                    "thumbnails": details["snippet"]["thumbnails"]
                })
            except Exception as e:
                print(f"Error fetching details for video {video_id}: {str(e)}")
                continue

        return videos_with_descriptions


def create_youtube_service() -> YouTubeService:
    """
    Factory function to create YouTubeService instance from environment variables

    Returns:
        YouTubeService instance
    """
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        raise ValueError("YOUTUBE_API_KEY environment variable is required")

    return YouTubeService(api_key)
