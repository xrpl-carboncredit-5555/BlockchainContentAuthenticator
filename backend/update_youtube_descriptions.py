
#!/usr/bin/env python3
"""
YouTube Description Updater for NFT Minted Videos

This script updates YouTube video descriptions to include BCA (Blockchain Content Authenticator)
validation information after NFTs are minted on the XRPL.

Features:
- Cross-references MongoDB NFT data with YouTube videos
- Checks if BCA validation text already exists
- Updates or adds BCA validation text before metadata tags
- Validates NFToken ID matches between YouTube and database
- Dry-run mode for safe testing
- Detailed logging of all operations
- Batch processing with configurable limits

Usage:
    python update_youtube_descriptions.py --help
    python update_youtube_descriptions.py --dry-run  # Test without making changes
    python update_youtube_descriptions.py --execute  # Update descriptions
    python update_youtube_descriptions.py --execute --limit 5  # Update only 5 videos
    python update_youtube_descriptions.py --check-only  # Just check status
"""

import os
import re
import argparse
import logging
import time
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from dotenv import load_dotenv

from src.services.youtube_service import create_youtube_service, YouTubeService
from src.services.mongodb_service import create_mongodb_service, MongoDBService
from src.services.youtube_auth import get_youtube_token


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_description_updates.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class YouTubeDescriptionUpdater:
    """Manages YouTube description updates for NFT-minted videos"""

    # YouTube description character limit
    MAX_DESCRIPTION_LENGTH = 5000

    # BCA validation text template
    BCA_TEMPLATE = """This episode, validated by BCA - Blockchain Content Authenticator- permanently recorded on the XRP Ledger — proof it's the genuine article from the official series run. BCA: https://bca.jimflint.com/verify/{nft_token_id}"""

    # Expected domain for BCA URLs
    EXPECTED_DOMAIN = "bca.jimflint.com"

    # Regex patterns to detect existing BCA text (matches all URL formats: old domain, new domain, with/without "Reference")
    BCA_PATTERN = re.compile(
        r'This episode,\s*validated by BCA.*?'
        r'BCA(?:\s+Reference)?\s*:\s*https://(?:bca-xrpl-c2hjpnej4q-uc\.a\.run\.app|bca\.jimflint\.com)(?:/verify)?/([A-F0-9]+)',
        re.IGNORECASE | re.DOTALL
    )

    # Regex to extract the domain from BCA URL
    BCA_DOMAIN_PATTERN = re.compile(
        r'BCA(?:\s+Reference)?\s*:\s*https://([^/]+)',
        re.IGNORECASE
    )

    def __init__(
        self,
        youtube_service: YouTubeService,
        mongodb_service: MongoDBService,
        oauth_token: Optional[str] = None
    ):
        """
        Initialize the updater

        Args:
            youtube_service: YouTube API service instance
            mongodb_service: MongoDB service instance
            oauth_token: OAuth 2.0 token for YouTube API (required for updates)
        """
        self.youtube = youtube_service
        self.db = mongodb_service
        self.oauth_token = oauth_token

    def get_minted_videos(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get all minted videos from database

        Args:
            limit: Maximum number of videos to process

        Returns:
            List of NFT records with video_id and nft_id
        """
        logger.info("Fetching minted videos from database...")
        nfts = self.db.get_all_nfts(limit=limit or 1000)
        logger.info(f"Found {len(nfts)} minted NFTs")
        return nfts

    def extract_nft_id_from_description(self, description: str) -> Optional[str]:
        """
        Extract NFT token ID from existing BCA text in description

        Args:
            description: Video description text

        Returns:
            NFT token ID if found, None otherwise
        """
        match = self.BCA_PATTERN.search(description)
        if match:
            return match.group(1)
        return None

    def extract_domain_from_description(self, description: str) -> Optional[str]:
        """
        Extract domain from existing BCA URL in description

        Args:
            description: Video description text

        Returns:
            Domain if found, None otherwise
        """
        match = self.BCA_DOMAIN_PATTERN.search(description)
        if match:
            return match.group(1)
        return None

    def verify_nft_exists(self, video_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Verify that an NFT exists for the given video in the database

        Args:
            video_id: YouTube video ID

        Returns:
            Tuple of (exists, nft_id, error_message)
            - exists: True if NFT exists and is valid
            - nft_id: The NFT token ID if exists
            - error_message: Error message if validation fails
        """
        try:
            # Check if NFT exists in database
            nft_record = self.db.get_nft_by_video_id(video_id)

            if not nft_record:
                return False, None, "No NFT found in database for this video"

            # Validate NFT has required fields
            nft_id = nft_record.get("nft_id")
            if not nft_id:
                return False, None, "NFT record exists but missing nft_id field"

            # Additional validation: check if nft_id is valid format (hex string)
            if not isinstance(nft_id, str) or len(nft_id) < 10:
                return False, None, f"Invalid NFT ID format: {nft_id}"

            logger.debug(f"NFT verified for video {video_id}: {nft_id}")
            return True, nft_id, None

        except Exception as e:
            error_msg = f"Error verifying NFT: {str(e)}"
            logger.error(f"Video {video_id}: {error_msg}")
            return False, None, error_msg

    def sync_description_from_youtube(self, video_id: str) -> Optional[str]:
        """
        Fetch the latest description from YouTube API and sync to MongoDB

        Args:
            video_id: YouTube video ID

        Returns:
            Latest description from YouTube, or None if error
        """
        try:
            logger.info(f"Syncing latest description for video {video_id} from YouTube...")
            latest_description = self.youtube.get_video_description(video_id)

            # Update video in MongoDB with latest description
            video_data = self.db.get_video(video_id)
            if video_data:
                video_data['description'] = latest_description
                self.db.save_video(video_data)
                logger.info(f"Updated MongoDB with latest description for {video_id}")

            return latest_description
        except Exception as e:
            logger.error(f"Error syncing description for video {video_id}: {str(e)}")
            return None

    def generate_bca_text(self, nft_token_id: str) -> str:
        """
        Generate BCA validation text with NFT token ID

        Args:
            nft_token_id: The NFT token ID from XRPL

        Returns:
            Formatted BCA validation text
        """
        return self.BCA_TEMPLATE.format(nft_token_id=nft_token_id)

    def check_description_status(
        self,
        video_id: str,
        nft_token_id: str
    ) -> Tuple[str, bool, Optional[str]]:
        """
        Check the current status of a video's description
        Also syncs latest description from YouTube to MongoDB

        Args:
            video_id: YouTube video ID
            nft_token_id: Expected NFT token ID from database

        Returns:
            Tuple of (status, needs_update, current_nft_id)
            - status: Description status message
            - needs_update: Whether description needs to be updated
            - current_nft_id: NFT ID currently in description (if any)
        """
        try:
            # Sync latest description from YouTube
            current_description = self.sync_description_from_youtube(video_id)
            if current_description is None:
                return "Error fetching description", False, None

            current_nft_id = self.extract_nft_id_from_description(current_description)
            current_domain = self.extract_domain_from_description(current_description)

            if current_nft_id is None:
                return "BCA text not found", True, None
            elif current_nft_id != nft_token_id:
                return "BCA text exists but NFT ID mismatch", True, current_nft_id
            elif current_domain and current_domain != self.EXPECTED_DOMAIN:
                return f"BCA text exists but using old domain ({current_domain})", True, current_nft_id
            else:
                return "BCA text exists and matches", False, current_nft_id

        except Exception as e:
            logger.error(f"Error checking video {video_id}: {str(e)}")
            return f"Error: {str(e)}", False, None

    def refresh_oauth_token(self) -> bool:
        """
        Refresh the OAuth token

        Returns:
            bool: True if refresh successful
        """
        try:
            logger.info("Attempting to refresh OAuth token...")
            new_token = get_youtube_token()

            if new_token:
                self.oauth_token = new_token
                logger.info("✅ OAuth token refreshed successfully")
                return True
            else:
                logger.error("❌ Failed to refresh OAuth token")
                return False

        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return False

    def update_description(
        self,
        video_id: str,
        nft_token_id: str,
        dry_run: bool = True,
        retry_count: int = 3
    ) -> Tuple[bool, str]:
        """
        Update a video's description with BCA validation text at the top

        Args:
            video_id: YouTube video ID
            nft_token_id: NFT token ID to add to description
            dry_run: If True, only simulate the update
            retry_count: Number of retries for failed requests

        Returns:
            Tuple of (success, message)
        """
        if not self.oauth_token and not dry_run:
            return False, "OAuth token required for actual updates"

        for attempt in range(retry_count):
            try:
                return self._attempt_update(video_id, nft_token_id, dry_run)

            except Exception as e:
                error_str = str(e)

                # Check if it's an auth error (401)
                if "401" in error_str or "Unauthorized" in error_str:
                    logger.warning(f"❌ OAuth token expired or invalid (attempt {attempt + 1}/{retry_count})")

                    if attempt < retry_count - 1:
                        # Try to refresh token
                        if self.refresh_oauth_token():
                            logger.info(f"🔄 Retrying with refreshed token...")
                            time.sleep(1)  # Brief delay before retry
                            continue
                        else:
                            return False, "Failed to refresh OAuth token. Please run: python get_youtube_oauth_token.py"
                    else:
                        return False, "OAuth token refresh failed after all retries"

                # Check if it's a quota/forbidden error (403)
                elif "403" in error_str or "Forbidden" in error_str:
                    logger.error(f"❌ 403 Forbidden Error - Likely API quota exhausted")
                    logger.error(f"   YouTube Data API v3 has a quota limit of 10,000 units/day")
                    logger.error(f"   Each video update costs ~50 units (≈200 updates/day max)")
                    logger.error(f"   Solution: Wait 24 hours for quota reset, or request quota increase from Google")
                    return False, "QUOTA_EXCEEDED: YouTube API quota exhausted (403 Forbidden). Wait 24 hours or request quota increase."

                # Check if it's a rate limit error (429)
                elif "429" in error_str or "Too Many Requests" in error_str:
                    if attempt < retry_count - 1:
                        wait_time = 30  # Wait longer for rate limits
                        logger.warning(f"⚠️  Rate limit hit (attempt {attempt + 1}/{retry_count})")
                        logger.info(f"   Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return False, "Rate limit exceeded after all retries"

                # Other errors - retry with exponential backoff
                elif attempt < retry_count - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"⚠️  Error (attempt {attempt + 1}/{retry_count}): {error_str}")
                    logger.info(f"   Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    # Final attempt failed
                    error_msg = f"Failed to update video {video_id}: {error_str}"
                    logger.error(error_msg)
                    return False, error_msg

        return False, "Update failed after all retries"

    def _attempt_update(
        self,
        video_id: str,
        nft_token_id: str,
        dry_run: bool = True
    ) -> Tuple[bool, str]:
        """
        Single attempt to update video description

        Args:
            video_id: YouTube video ID
            nft_token_id: NFT token ID to add to description
            dry_run: If True, only simulate the update

        Returns:
            Tuple of (success, message)
        """
        try:
            # STEP 1: Sync latest description from YouTube API
            current_description = self.sync_description_from_youtube(video_id)
            if current_description is None:
                return False, "Failed to fetch description from YouTube"

            # STEP 2: Check if BCA text already exists
            current_nft_id = self.extract_nft_id_from_description(current_description)

            # STEP 3: Generate new BCA text
            new_bca_text = self.generate_bca_text(nft_token_id)

            # STEP 4: Remove existing BCA text if present
            if current_nft_id:
                # Remove old BCA text
                description_without_bca = self.BCA_PATTERN.sub('', current_description).strip()
                action = f"Replaced at top (old ID: {current_nft_id})"
            else:
                description_without_bca = current_description.strip()
                action = "Added at top"

            # STEP 5: Add BCA text at the very top
            new_description = new_bca_text + "\n\n" + description_without_bca

            # STEP 6: Check character limit (YouTube max is 5000)
            if len(new_description) > self.MAX_DESCRIPTION_LENGTH:
                warning_msg = (
                    f"Description exceeds {self.MAX_DESCRIPTION_LENGTH} characters "
                    f"({len(new_description)} chars). Skipping to avoid truncation."
                )
                logger.warning(f"Video {video_id}: {warning_msg}")
                return False, f"SKIPPED: {warning_msg}"

            # STEP 7: Update or simulate
            if dry_run:
                logger.info(f"[DRY RUN] Would update video {video_id}: {action}")
                logger.info(f"[DRY RUN] New length: {len(new_description)} chars")
                logger.debug(f"[DRY RUN] New description preview:\n{new_description[:300]}...")
                return True, f"Dry run: {action}"
            else:
                # Perform actual update
                self.youtube.update_video_description(
                    video_id=video_id,
                    new_description=new_description,
                    oauth_token=self.oauth_token
                )
                logger.info(f"Successfully updated video {video_id}: {action}")
                logger.info(f"Final description length: {len(new_description)} chars")
                return True, f"Updated: {action}"

        except Exception as e:
            error_msg = f"Failed to update video {video_id}: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def process_all_videos(
        self,
        limit: Optional[int] = None,
        skip: int = 0,
        dry_run: bool = True,
        check_only: bool = False,
        rate_limit_delay: float = 1.0
    ) -> Dict:
        """
        Process all minted videos and update their descriptions

        Args:
            limit: Maximum number of videos to process (after skipping)
            skip: Number of videos to skip from the beginning (default 0)
            dry_run: If True, only simulate updates
            check_only: If True, only check status without updating
            rate_limit_delay: Delay in seconds between API requests (default 1.0)

        Returns:
            Dictionary with processing statistics
        """
        stats = {
            "total_processed": 0,
            "needs_update": 0,
            "already_correct": 0,
            "updated_successfully": 0,
            "update_failed": 0,
            "skipped_char_limit": 0,
            "skipped_no_nft": 0,
            "quota_exceeded": 0,
            "errors": 0,
            "results": [],
            "start_time": time.time(),
            "stopped_early": False,
            "stop_reason": None
        }

        # Track consecutive quota failures to detect exhaustion early
        consecutive_quota_failures = 0
        max_consecutive_quota_failures = 5  # Stop after 5 consecutive quota errors

        # Get all minted videos
        all_nfts = self.get_minted_videos(None)  # Get all videos first
        total_available = len(all_nfts)

        if total_available == 0:
            logger.info("No minted videos found to process")
            return stats

        # Apply skip
        if skip > 0:
            if skip >= total_available:
                logger.error(f"Skip value ({skip}) is greater than or equal to total videos ({total_available})")
                return stats
            logger.info(f"⏩ Skipping first {skip} videos (as requested)")
            all_nfts = all_nfts[skip:]

        # Apply limit
        if limit:
            nfts = all_nfts[:limit]
        else:
            nfts = all_nfts

        videos_to_process = len(nfts)

        logger.info(f"📊 Total videos in database: {total_available}")
        if skip > 0:
            logger.info(f"⏩ Skipping: {skip} videos")
            logger.info(f"📹 Processing videos {skip + 1} to {skip + videos_to_process} of {total_available}")
        else:
            logger.info(f"📹 Processing: {videos_to_process} videos")
        logger.info(f"Mode: {'CHECK ONLY' if check_only else 'DRY RUN' if dry_run else 'EXECUTE'}")
        logger.info(f"Rate limit: {rate_limit_delay}s delay between requests")

        for idx, nft in enumerate(nfts, 1):
            # Add rate limiting delay (except for first video)
            if idx > 1 and not check_only:
                time.sleep(rate_limit_delay)

            # Calculate current position (accounting for skip)
            current_position = skip + idx

            # Calculate and display progress
            progress_pct = (idx / videos_to_process) * 100
            elapsed_time = time.time() - stats["start_time"]
            avg_time_per_video = elapsed_time / idx
            remaining_videos = videos_to_process - idx
            eta_seconds = avg_time_per_video * remaining_videos
            eta_minutes = eta_seconds / 60

            logger.info(f"\n[{current_position}/{total_available}] Progress: {progress_pct:.1f}% | ETA: {eta_minutes:.1f} min")
            video_id = nft.get("video_id")
            nft_token_id = nft.get("nft_id")

            if not video_id or not nft_token_id:
                logger.warning(f"Skipping NFT record with missing data: {nft.get('_id')}")
                stats["errors"] += 1
                continue

            logger.info(f"Processing video: {video_id}")

            # CRITICAL: Verify NFT exists in database before attempting update
            nft_exists, verified_nft_id, error_msg = self.verify_nft_exists(video_id)

            if not nft_exists:
                logger.warning(f"  ⚠️  SKIPPED: {error_msg}")
                result = {
                    "video_id": video_id,
                    "nft_token_id": "N/A",
                    "status": "No NFT minted",
                    "needs_update": False,
                    "current_nft_id": None,
                    "video_title": nft.get("metadata", {}).get("name", "Unknown"),
                    "action_taken": f"SKIPPED: {error_msg}"
                }
                stats["skipped_no_nft"] += 1
                stats["results"].append(result)
                continue

            # Use verified NFT ID (more reliable than data from loop)
            nft_token_id = verified_nft_id

            # Check current status
            status, needs_update, current_nft_id = self.check_description_status(
                video_id, nft_token_id
            )

            result = {
                "video_id": video_id,
                "nft_token_id": nft_token_id,
                "status": status,
                "needs_update": needs_update,
                "current_nft_id": current_nft_id,
                "video_title": nft.get("metadata", {}).get("name", "Unknown"),
                "action_taken": None
            }

            stats["total_processed"] += 1

            if needs_update:
                stats["needs_update"] += 1
                logger.info(f"  Status: {status}")

                if not check_only:
                    # Perform update
                    success, message = self.update_description(
                        video_id, nft_token_id, dry_run
                    )
                    result["action_taken"] = message

                    if success:
                        stats["updated_successfully"] += 1
                        consecutive_quota_failures = 0  # Reset on success
                    else:
                        # Check if it was skipped due to character limit
                        if "SKIPPED" in message and "character" in message:
                            stats["skipped_char_limit"] += 1
                        # Check if it's quota exhaustion
                        elif "QUOTA_EXCEEDED" in message or "403" in message:
                            stats["quota_exceeded"] += 1
                            consecutive_quota_failures += 1
                            logger.error(f"⚠️  Quota failure #{consecutive_quota_failures}")

                            # Stop processing if we hit too many consecutive quota failures
                            if consecutive_quota_failures >= max_consecutive_quota_failures:
                                stats["stopped_early"] = True
                                stats["stop_reason"] = "YouTube API quota exhausted"
                                logger.error(f"\n{'='*70}")
                                logger.error(f"🛑 STOPPING: {consecutive_quota_failures} consecutive quota failures detected")
                                logger.error(f"   YouTube API quota appears to be exhausted")
                                logger.error(f"   Successfully updated {stats['updated_successfully']} videos before quota exhaustion")
                                logger.error(f"   Remaining videos will be skipped")
                                logger.error(f"{'='*70}\n")
                                break
                        else:
                            consecutive_quota_failures = 0  # Reset on non-quota failure

                        stats["update_failed"] += 1
            else:
                # Only show checkmark if NFT exists AND description is correct
                stats["already_correct"] += 1
                logger.info(f"  Status: {status} ✓ (NFT verified)")
                result["action_taken"] = "No update needed (NFT verified)"

            stats["results"].append(result)

        # Calculate final timing statistics
        stats["end_time"] = time.time()
        stats["total_duration"] = stats["end_time"] - stats["start_time"]
        stats["avg_time_per_video"] = stats["total_duration"] / videos_to_process if videos_to_process > 0 else 0
        stats["videos_skipped"] = skip
        stats["total_available"] = total_available

        # Log completion
        logger.info(f"\n{'='*70}")
        logger.info(f"Processing complete!")
        if skip > 0:
            logger.info(f"Skipped: {skip} videos | Processed: {videos_to_process} videos")
        logger.info(f"Total time: {stats['total_duration']/60:.1f} minutes")
        logger.info(f"Average: {stats['avg_time_per_video']:.2f} seconds per video")
        logger.info(f"{'='*70}")

        return stats

    def print_summary(self, stats: Dict):
        """
        Print a summary of processing results

        Args:
            stats: Statistics dictionary from process_all_videos
        """
        print("\n" + "=" * 70)
        print("YOUTUBE DESCRIPTION UPDATE SUMMARY")
        print("=" * 70)

        # Skip information
        if stats.get('videos_skipped', 0) > 0:
            print(f"⏩ Skipped first {stats['videos_skipped']} videos (as requested)")
            print(f"📊 Total available: {stats.get('total_available', 'N/A')} videos")
            print("-" * 70)

        # Timing information
        if 'total_duration' in stats:
            duration_minutes = stats['total_duration'] / 60
            avg_time = stats.get('avg_time_per_video', 0)
            print(f"⏱️  Total time: {duration_minutes:.1f} minutes")
            print(f"⏱️  Average: {avg_time:.2f} seconds per video")
            print("-" * 70)

        # Early stop warning
        if stats.get('stopped_early', False):
            print(f"🛑 STOPPED EARLY: {stats.get('stop_reason', 'Unknown reason')}")
            print("-" * 70)

        # Processing statistics
        print(f"📊 Total videos processed: {stats['total_processed']}")
        print(f"✅ Already correct (NFT verified): {stats['already_correct']}")
        print(f"🔄 Need update: {stats['needs_update']}")
        print(f"✅ Updated successfully: {stats['updated_successfully']}")
        print(f"❌ Update failed: {stats['update_failed']}")
        if stats.get('quota_exceeded', 0) > 0:
            print(f"   └─ Quota exhausted (403): {stats['quota_exceeded']}")
        if stats['skipped_char_limit'] > 0:
            print(f"   └─ Skipped (5000 char limit): {stats['skipped_char_limit']}")
        if stats['skipped_no_nft'] > 0:
            print(f"⚠️  Skipped (No NFT minted): {stats['skipped_no_nft']}")
        if stats['errors'] > 0:
            print(f"❌ Errors: {stats['errors']}")
        print("=" * 70)

        # Quota information
        if stats.get('quota_exceeded', 0) > 0:
            print("\n⚠️  YOUTUBE API QUOTA INFORMATION")
            print("=" * 70)
            print("YouTube Data API v3 has a default quota of 10,000 units per day")
            print("Each video update costs approximately 50 units")
            print(f"Maximum updates per day: ~200 videos")
            print(f"\nYou successfully updated {stats['updated_successfully']} videos")
            print(f"Then hit quota limit at video #{stats['total_processed']}")
            print(f"\n💡 Solutions:")
            print("   1. Wait 24 hours for quota reset (resets at midnight Pacific Time)")
            print("   2. Request quota increase from Google Cloud Console:")
            print("      https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas")
            print("=" * 70)

        if stats['needs_update'] > 0:
            print("\nVideos needing update:")
            for result in stats['results']:
                if result['needs_update']:
                    print(f"  - {result['video_id']}: {result['status']}")
                    print(f"    Title: {result['video_title']}")
                    print(f"    Expected NFT: {result['nft_token_id']}")
                    if result['current_nft_id']:
                        print(f"    Current NFT: {result['current_nft_id']}")
                    print(f"    Action: {result['action_taken']}")
                    print()

        if stats['skipped_no_nft'] > 0:
            print("\n⚠️  Videos skipped (No NFT minted):")
            for result in stats['results']:
                if result.get('status') == 'No NFT minted':
                    print(f"  - {result['video_id']}: {result['video_title']}")
                    print(f"    Reason: {result['action_taken']}")
                    print()


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Update YouTube video descriptions with BCA validation text"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check status without making any updates"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate updates without actually modifying descriptions"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute actual updates (requires OAuth token)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of videos to process"
    )
    parser.add_argument(
        "--skip",
        type=int,
        default=0,
        help="Skip first N videos (useful for resuming after quota exhaustion). Example: --skip 180 to start from video 181"
    )
    parser.add_argument(
        "--oauth-token",
        type=str,
        help="YouTube OAuth 2.0 access token (or set YOUTUBE_OAUTH_TOKEN env var)"
    )
    parser.add_argument(
        "--rate-limit",
        type=float,
        default=1.0,
        help="Delay in seconds between API requests (default: 1.0, for scale operations use 0.5-2.0)"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Determine execution mode
    if args.execute and args.dry_run:
        logger.error("Cannot use --execute and --dry-run together")
        return

    check_only = args.check_only
    dry_run = args.dry_run or not args.execute

    # Get OAuth token if needed
    oauth_token = args.oauth_token or os.getenv("YOUTUBE_OAUTH_TOKEN")
    if args.execute and not oauth_token:
        logger.error("OAuth token required for --execute mode")
        logger.error("Set YOUTUBE_OAUTH_TOKEN environment variable or use --oauth-token")
        return

    try:
        # Initialize services
        logger.info("Initializing services...")
        youtube_service = create_youtube_service()
        mongodb_service = create_mongodb_service()

        # Create updater
        updater = YouTubeDescriptionUpdater(
            youtube_service=youtube_service,
            mongodb_service=mongodb_service,
            oauth_token=oauth_token
        )

        # Process videos
        stats = updater.process_all_videos(
            limit=args.limit,
            skip=args.skip,
            dry_run=dry_run,
            check_only=check_only,
            rate_limit_delay=args.rate_limit
        )

        # Print summary
        updater.print_summary(stats)

        # Save detailed results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"youtube_update_results_{timestamp}.log"
        with open(results_file, 'w') as f:
            f.write(f"YouTube Description Update Results - {datetime.now()}\n")
            f.write(f"Mode: {'CHECK ONLY' if check_only else 'DRY RUN' if dry_run else 'EXECUTE'}\n")
            f.write(f"Rate Limit: {args.rate_limit}s delay between requests\n")
            if 'total_duration' in stats:
                f.write(f"Total Time: {stats['total_duration']/60:.1f} minutes\n")
                f.write(f"Average: {stats['avg_time_per_video']:.2f} seconds per video\n")
            f.write("=" * 70 + "\n\n")
            for result in stats['results']:
                f.write(f"Video ID: {result['video_id']}\n")
                f.write(f"Title: {result['video_title']}\n")
                f.write(f"NFT Token ID: {result['nft_token_id']}\n")
                f.write(f"Status: {result['status']}\n")
                f.write(f"Needs Update: {result['needs_update']}\n")
                f.write(f"Action: {result['action_taken']}\n")
                f.write("-" * 70 + "\n")

        logger.info(f"Detailed results saved to: {results_file}")

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
