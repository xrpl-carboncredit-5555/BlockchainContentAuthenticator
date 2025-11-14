import os
import io
import json as json_lib
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PinataService:
    """Service for interacting with Pinata IPFS API"""

    def __init__(self, api_key: str, api_secret: str, jwt_token: str, group_id: str):
        """
        Initialize Pinata service

        Args:
            api_key: Pinata API key
            api_secret: Pinata API secret
            jwt_token: Pinata JWT token
            group_id: Default group ID for organizing uploads
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.jwt_token = jwt_token
        self.group_id = group_id
        self.base_url = "https://api.pinata.cloud"
        self.upload_url = "https://uploads.pinata.cloud/v3/files"
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }

    def upload_json(
        self,
        json_data: Dict[str, Any],
        name: Optional[str] = None,
        keyvalues: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload JSON metadata to Pinata IPFS (API v3)

        Args:
            json_data: The JSON object to upload
            name: Name for the pinned content
            keyvalues: Key-value pairs for tags/categories
            group_id: Group ID to organize the upload (uses default if not provided)

        Returns:
            Dict with upload response including IPFS hash
        """
        if name is None:
            name = f"metadata-{int(datetime.now().timestamp())}.json"

        if keyvalues is None:
            keyvalues = {}

        # Add upload timestamp
        keyvalues["uploadedAt"] = datetime.now().isoformat()

        target_group_id = group_id or self.group_id

        try:
            # Convert JSON to string and then to bytes
            json_string = json_lib.dumps(json_data, indent=2)
            json_bytes = json_string.encode('utf-8')

            # Prepare multipart form data
            files = {
                'file': (name, json_bytes, 'application/json')
            }

            # Form data fields
            data = {
                'name': name,
                'network': 'public',
            }

            # Add group_id if provided
            if target_group_id:
                data['group_id'] = target_group_id

            # Add keyvalues as JSON string
            if keyvalues:
                data['keyvalues'] = json_lib.dumps(keyvalues)

            # Headers for v3 API
            headers = {
                "Authorization": f"Bearer {self.jwt_token}"
            }

            response = requests.post(
                self.upload_url,
                files=files,
                data=data,
                headers=headers,
                timeout=60
            )
            response.raise_for_status()

            result = response.json()

            # Transform v3 response to match old API format for backwards compatibility
            return {
                'IpfsHash': result.get('data', {}).get('cid', ''),
                'PinSize': result.get('data', {}).get('size', 0),
                'Timestamp': result.get('data', {}).get('created_at', ''),
                'isDuplicate': result.get('data', {}).get('is_duplicate', False)
            }

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg} - {error_detail}"
                except:
                    error_msg = f"{error_msg} - {e.response.text}"
            raise Exception(f"Failed to upload JSON to Pinata: {error_msg}")

    def upload_json_with_category(
        self,
        json_data: Dict[str, Any],
        category: str,
        additional_tags: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload JSON with specific category tag

        Args:
            json_data: The JSON object to upload
            category: Category tag for organization
            additional_tags: Additional key-value tags

        Returns:
            Dict with upload response
        """
        if additional_tags is None:
            additional_tags = {}

        keyvalues = {
            "category": category,
            **additional_tags
        }

        name = f"{category}-{int(datetime.now().timestamp())}"

        return self.upload_json(json_data, name=name, keyvalues=keyvalues)

    def update_metadata(
        self,
        ipfs_hash: str,
        keyvalues: Dict[str, Any]
    ) -> None:
        """
        Update metadata (keyvalues) of an existing pinned file

        Args:
            ipfs_hash: The IPFS hash of the pinned content
            keyvalues: New key-value pairs to update
        """
        payload = {
            "ipfsHash": ipfs_hash,
            "keyvalues": keyvalues
        }

        try:
            response = requests.put(
                f"{self.base_url}/pinning/hashMetadata",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to update metadata: {str(e)}")

    def list_by_keyvalues(
        self,
        filters: Dict[str, Any],
        status: str = "pinned"
    ) -> Dict[str, Any]:
        """
        List pinned files filtered by keyvalues (tags/categories)

        Args:
            filters: Key-value filters to search by
            status: Pin status (pinned, unpinned, all)

        Returns:
            Dict with list of pinned files
        """
        params = {"status": status}

        for key, value in filters.items():
            params[f"metadata[keyvalues][{key}]"] = str(value)

        try:
            response = requests.get(
                f"{self.base_url}/data/pinList",
                params=params,
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list files: {str(e)}")

    def add_files_to_group(
        self,
        file_ids: List[str],
        group_id: Optional[str] = None
    ) -> None:
        """
        Add files to a specific group

        Args:
            file_ids: List of file IDs to add to group
            group_id: Group ID (uses default if not provided)
        """
        target_group_id = group_id or self.group_id

        payload = {
            "hashesToAdd": file_ids,
            "groupId": target_group_id
        }

        try:
            response = requests.put(
                f"{self.base_url}/pinning/addHashToGroup",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to add files to group: {str(e)}")

    def upload_image_from_url(
        self,
        image_url: str,
        name: Optional[str] = None,
        keyvalues: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download image from URL and upload to Pinata IPFS (API v3)

        Args:
            image_url: URL of the image to download and upload
            name: Name for the pinned content
            keyvalues: Key-value pairs for tags/categories
            group_id: Group ID to organize the upload

        Returns:
            Dict with upload response including CID (as IpfsHash for backwards compatibility)
        """
        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                # Download image with longer timeout and retry logic
                print(f"      Downloading image from URL (attempt {attempt + 1}/{max_retries})...")
                image_response = requests.get(image_url, timeout=30, stream=True)
                image_response.raise_for_status()

                # Read content
                image_content = image_response.content
                print(f"      Downloaded {len(image_content)} bytes")

                # Prepare metadata
                if name is None:
                    name = f"image-{int(datetime.now().timestamp())}.jpg"

                if keyvalues is None:
                    keyvalues = {}

                keyvalues["uploadedAt"] = datetime.now().isoformat()
                keyvalues["source_url"] = image_url

                target_group_id = group_id or self.group_id

                # Prepare multipart form data for API v3
                files = {
                    'file': (name, image_content, 'image/jpeg')
                }

                # Form data fields (not JSON!)
                data = {
                    'name': name,
                    'network': 'public',  # or 'private'
                }

                # Add group_id if provided
                if target_group_id:
                    data['group_id'] = target_group_id

                # Add keyvalues as JSON string
                if keyvalues:
                    data['keyvalues'] = json_lib.dumps(keyvalues)

                # Headers for v3 API (Authorization only, let requests handle Content-Type)
                headers = {
                    "Authorization": f"Bearer {self.jwt_token}"
                }

                print(f"      Uploading to Pinata IPFS (v3 API)...")
                response = requests.post(
                    self.upload_url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )
                response.raise_for_status()

                result = response.json()
                print(f"      Upload successful: {result.get('data', {}).get('cid', 'unknown')}")

                # Transform v3 response to match old API format for backwards compatibility
                return {
                    'IpfsHash': result.get('data', {}).get('cid', ''),
                    'PinSize': result.get('data', {}).get('size', 0),
                    'Timestamp': result.get('data', {}).get('created_at', ''),
                    'isDuplicate': result.get('data', {}).get('is_duplicate', False)
                }

            except requests.exceptions.Timeout as e:
                print(f"      Timeout on attempt {attempt + 1}/{max_retries}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise Exception(f"Failed to upload image after {max_retries} attempts (timeout): {str(e)}")

            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if hasattr(e, 'response') and e.response is not None:
                    try:
                        error_detail = e.response.json()
                        error_msg = f"{error_msg} - {error_detail}"
                    except:
                        error_msg = f"{error_msg} - {e.response.text}"

                print(f"      Request error on attempt {attempt + 1}/{max_retries}: {error_msg}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                else:
                    raise Exception(f"Failed to upload image to Pinata after {max_retries} attempts: {error_msg}")

            except Exception as e:
                print(f"      Unexpected error: {str(e)}")
                raise Exception(f"Failed to upload image to Pinata: {str(e)}")

    def upload_file(
        self,
        file_path: str,
        name: Optional[str] = None,
        keyvalues: Optional[Dict[str, Any]] = None,
        group_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a local file to Pinata IPFS (API v3)

        Args:
            file_path: Path to the file to upload
            name: Name for the pinned content
            keyvalues: Key-value pairs for tags/categories
            group_id: Group ID to organize the upload

        Returns:
            Dict with upload response including IPFS hash
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Prepare metadata
            if name is None:
                name = os.path.basename(file_path)

            if keyvalues is None:
                keyvalues = {}

            keyvalues["uploadedAt"] = datetime.now().isoformat()

            target_group_id = group_id or self.group_id

            # Form data fields
            data = {
                'name': name,
                'network': 'public',
            }

            # Add group_id if provided
            if target_group_id:
                data['group_id'] = target_group_id

            # Add keyvalues as JSON string
            if keyvalues:
                data['keyvalues'] = json_lib.dumps(keyvalues)

            # Headers for v3 API
            headers = {
                "Authorization": f"Bearer {self.jwt_token}"
            }

            # Read and upload file
            with open(file_path, 'rb') as f:
                files = {
                    'file': (name, f, 'application/octet-stream')
                }

                response = requests.post(
                    self.upload_url,
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=120
                )
                response.raise_for_status()

                result = response.json()

                # Transform v3 response to match old API format for backwards compatibility
                return {
                    'IpfsHash': result.get('data', {}).get('cid', ''),
                    'PinSize': result.get('data', {}).get('size', 0),
                    'Timestamp': result.get('data', {}).get('created_at', ''),
                    'isDuplicate': result.get('data', {}).get('is_duplicate', False)
                }

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    error_msg = f"{error_msg} - {error_detail}"
                except:
                    error_msg = f"{error_msg} - {e.response.text}"
            raise Exception(f"Failed to upload file to Pinata: {error_msg}")
        except Exception as e:
            raise Exception(f"Failed to upload file to Pinata: {str(e)}")


def create_pinata_service() -> PinataService:
    """
    Factory function to create PinataService instance from environment variables

    Returns:
        PinataService instance
    """
    api_key = os.getenv("PINATA_API_KEY")
    api_secret = os.getenv("PINATA_API_SECRET")
    jwt_token = os.getenv("PINATA_JWT_SECRET")
    group_id = os.getenv("PINATA_GROUP_ID")

    if not jwt_token:
        raise ValueError("PINATA_JWT_SECRET environment variable is required")

    if not group_id:
        raise ValueError("PINATA_GROUP_ID environment variable is required")

    return PinataService(api_key, api_secret, jwt_token, group_id)
