import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import DuplicateKeyError


class MongoDBService:
    """Service for managing NFT and video data in MongoDB"""

    def __init__(self, mongodb_uri: str, database_name: str = "youtube_nft_db"):
        """
        Initialize MongoDB service

        Args:
            mongodb_uri: MongoDB connection URI
            database_name: Database name (default: youtube_nft_db)
        """
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[database_name]

        # Collections
        self.videos = self.db['videos']
        self.nfts = self.db['nfts']
        self.minting_log = self.db['minting_log']

        # Create indexes for efficient querying
        self._create_indexes()

        print(f"MongoDB Service Initialized")
        print(f"  Database: {database_name}")
        print(f"  Collections: videos, nfts, minting_log")

    def _create_indexes(self):
        """Create database indexes for efficient queries"""
        # Video indexes
        self.videos.create_index([("video_id", ASCENDING)], unique=True)
        self.videos.create_index([("published_at", DESCENDING)])
        self.videos.create_index([("category", ASCENDING)])

        # NFT indexes
        self.nfts.create_index([("nft_id", ASCENDING)], unique=True)
        self.nfts.create_index([("video_id", ASCENDING)], unique=True)
        self.nfts.create_index([("tx_hash", ASCENDING)])
        self.nfts.create_index([("minted_at", DESCENDING)])

        # Minting log indexes
        self.minting_log.create_index([("timestamp", DESCENDING)])
        self.minting_log.create_index([("video_id", ASCENDING)])

    def save_video(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save or update video data

        Args:
            video_data: Video information dict with video_id, title, etc.

        Returns:
            Dict with operation result
        """
        try:
            video_id = video_data.get('video_id')
            if not video_id:
                raise ValueError("video_id is required")

            # Add metadata
            video_data['updated_at'] = datetime.now(timezone.utc)

            # Upsert video data
            result = self.videos.update_one(
                {"video_id": video_id},
                {
                    "$set": video_data,
                    "$setOnInsert": {"created_at": datetime.now(timezone.utc)}
                },
                upsert=True
            )

            return {
                'success': True,
                'video_id': video_id,
                'matched': result.matched_count,
                'modified': result.modified_count,
                'upserted': result.upserted_id is not None
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def save_nft(self, nft_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save NFT data to database

        Args:
            nft_data: NFT information including nft_id, video_id, ipfs hashes, etc.

        Returns:
            Dict with operation result
        """
        try:
            nft_id = nft_data.get('nft_id')
            video_id = nft_data.get('video_id')

            if not nft_id:
                raise ValueError("nft_id is required")
            if not video_id:
                raise ValueError("video_id is required")

            # Add timestamp
            nft_data['created_at'] = datetime.now(timezone.utc)

            # Insert NFT data
            result = self.nfts.insert_one(nft_data)

            return {
                'success': True,
                'nft_id': nft_id,
                'video_id': video_id,
                'inserted_id': str(result.inserted_id)
            }

        except DuplicateKeyError:
            return {
                'success': False,
                'error': f"NFT already exists for video_id: {video_id}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get video data by video_id

        Args:
            video_id: YouTube video ID

        Returns:
            Video data dict or None
        """
        video = self.videos.find_one({"video_id": video_id}, {"_id": 0})
        return video

    def get_nft_by_video_id(self, video_id: str) -> Optional[Dict[str, Any]]:
        """
        Get NFT data by video_id

        Args:
            video_id: YouTube video ID

        Returns:
            NFT data dict or None
        """
        nft = self.nfts.find_one({"video_id": video_id}, {"_id": 0})
        return nft

    def get_nft_by_nft_id(self, nft_id: str) -> Optional[Dict[str, Any]]:
        """
        Get NFT data by nft_id

        Args:
            nft_id: XRPL NFT ID

        Returns:
            NFT data dict or None
        """
        nft = self.nfts.find_one({"nft_id": nft_id}, {"_id": 0})
        return nft

    def get_all_videos(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get all videos

        Args:
            limit: Maximum number of videos to return
            skip: Number of videos to skip

        Returns:
            List of video data dicts
        """
        videos = list(
            self.videos.find({}, {"_id": 0})
            .sort("published_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return videos

    def get_all_nfts(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get all NFTs

        Args:
            limit: Maximum number of NFTs to return
            skip: Number of NFTs to skip

        Returns:
            List of NFT data dicts
        """
        nfts = list(
            self.nfts.find({}, {"_id": 0})
            .sort("minted_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        return nfts

    def get_unminted_videos(self, limit: int = 100, include_skipped: bool = False) -> List[Dict[str, Any]]:
        """
        Get videos that haven't been minted as NFTs

        Args:
            limit: Maximum number of videos to return
            include_skipped: If True, include videos marked as skipped

        Returns:
            List of unminted video data dicts
        """
        # Get all video_ids that have been minted
        minted_video_ids = set(
            nft['video_id'] for nft in self.nfts.find({}, {"video_id": 1, "_id": 0})
        )

        # Build query filter
        query_filter = {"video_id": {"$nin": list(minted_video_ids)}}

        # Exclude skipped videos unless explicitly included
        if not include_skipped:
            query_filter["skip_minting"] = {"$ne": True}

        # Get videos not in minted list
        unminted_videos = list(
            self.videos.find(query_filter, {"_id": 0})
            .sort("published_at", ASCENDING)
            .limit(limit)
        )

        return unminted_videos

    def mark_video_skipped(self, video_id: str, reason: str = "Duplicate CID detected") -> Dict[str, Any]:
        """
        Mark a video as skipped for minting

        Args:
            video_id: YouTube video ID
            reason: Reason for skipping

        Returns:
            Dict with update result
        """
        try:
            result = self.videos.update_one(
                {"video_id": video_id},
                {
                    "$set": {
                        "skip_minting": True,
                        "skip_reason": reason,
                        "skipped_at": datetime.now(timezone.utc)
                    }
                }
            )

            return {
                'success': True,
                'modified_count': result.modified_count
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def unmark_video_skipped(self, video_id: str) -> Dict[str, Any]:
        """
        Remove skip flag from a video

        Args:
            video_id: YouTube video ID

        Returns:
            Dict with update result
        """
        try:
            result = self.videos.update_one(
                {"video_id": video_id},
                {
                    "$unset": {
                        "skip_minting": "",
                        "skip_reason": "",
                        "skipped_at": ""
                    }
                }
            )

            return {
                'success': True,
                'modified_count': result.modified_count
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_videos_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get videos by category

        Args:
            category: Video category
            limit: Maximum number of videos to return

        Returns:
            List of video data dicts
        """
        videos = list(
            self.videos.find({"category": category}, {"_id": 0})
            .sort("published_at", DESCENDING)
            .limit(limit)
        )
        return videos

    def log_minting_operation(
        self,
        video_id: str,
        success: bool,
        nft_id: Optional[str] = None,
        tx_hash: Optional[str] = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Log a minting operation for tracking and debugging

        Args:
            video_id: YouTube video ID
            success: Whether minting was successful
            nft_id: NFT ID if successful
            tx_hash: Transaction hash if successful
            error: Error message if failed

        Returns:
            Dict with log result
        """
        try:
            log_entry = {
                "video_id": video_id,
                "success": success,
                "timestamp": datetime.now(timezone.utc),
                "nft_id": nft_id,
                "tx_hash": tx_hash,
                "error": error
            }

            result = self.minting_log.insert_one(log_entry)

            return {
                'success': True,
                'log_id': str(result.inserted_id)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_minting_stats(self) -> Dict[str, Any]:
        """
        Get statistics about minting operations

        Returns:
            Dict with minting statistics
        """
        total_videos = self.videos.count_documents({})
        total_nfts = self.nfts.count_documents({})

        # Get category breakdown
        category_pipeline = [
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        category_stats = list(self.videos.aggregate(category_pipeline))

        return {
            'total_videos': total_videos,
            'total_nfts': total_nfts,
            'unminted_count': total_videos - total_nfts,
            'category_breakdown': category_stats
        }

    def close(self):
        """Close MongoDB connection"""
        self.client.close()


def create_mongodb_service() -> MongoDBService:
    """
    Factory function to create MongoDBService instance from environment variables

    Returns:
        MongoDBService instance
    """
    mongodb_uri = os.getenv("MONGODB_URI")

    if not mongodb_uri:
        raise ValueError("MONGODB_URI environment variable is required")

    database_name = os.getenv("MONGODB_DATABASE")
    if not database_name:
        raise ValueError("MONGODB_DATABASE environment variable is required")

    return MongoDBService(mongodb_uri, database_name)
