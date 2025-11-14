import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from xrpl.clients import JsonRpcClient
from xrpl.wallet import Wallet
from xrpl.models.transactions import NFTokenMint, AccountSet, Memo
from xrpl.transaction import submit_and_wait
from xrpl.utils import str_to_hex

load_dotenv()


class XRPLService:
    """Service for interacting with XRPL - NFT minting and account management"""

    def __init__(self, node_url: str, wallet_secret: str):
        """
        Initialize XRPL service

        Args:
            node_url: XRPL node URL
            wallet_secret: XRPL wallet secret/seed
        """
        self.node_url = node_url
        self.client = JsonRpcClient(node_url)
        self.wallet = Wallet.from_seed(wallet_secret)

        print(f"XRPL Service Initialized")
        print(f"  Wallet Address: {self.wallet.address}")
        print(f"  Node: {node_url}")

    def mint_nft(
        self,
        uri: str,
        taxon: int = 0,
        transfer_fee: int = 0,
        flags: int = 8,
        memo_data: Optional[str] = None,
        memo_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mint an NFT on XRPL

        Args:
            uri: URI pointing to NFT metadata (will be converted to hex)
            taxon: NFToken taxon (default: 0)
            transfer_fee: Transfer fee in basis points (0-50000, representing 0-50%)
            flags: NFToken flags (default: 8 = tfTransferable)
            memo_data: Optional memo data
            memo_type: Optional memo type

        Returns:
            Dict with mint result including nft_id, tx_hash, and success status
        """
        try:
            print(f"\nMinting NFT...")
            print(f"  URI: {uri[:100]}..." if len(uri) > 100 else f"  URI: {uri}")
            print(f"  Taxon: {taxon}")
            print(f"  Transfer Fee: {transfer_fee}")

            # Convert URI to hex
            uri_hex = str_to_hex(uri)

            # Prepare memos if provided
            memos = []
            if memo_data and memo_type:
                memo = Memo(
                    # memo_type=str_to_hex(memo_type),
                    memo_data=str_to_hex(memo_data)
                )
                memos.append(memo)

            # Create mint transaction
            mint_tx = NFTokenMint(
                account=self.wallet.address,
                nftoken_taxon=taxon,
                transfer_fee=transfer_fee,
                # flags=flags,  # This is not needed for minting
                uri=uri_hex,
                memos=memos if memos else None
            )

            print(f"\nSubmitting transaction to XRPL...")

            # Submit and wait for validation
            response = submit_and_wait(mint_tx, self.client, self.wallet)

            if response.is_successful():
                tx_hash = response.result['hash']
                nft_id = self._extract_nft_id(response)

                result = {
                    'success': True,
                    'nft_id': nft_id,
                    'tx_hash': tx_hash,
                    'uri': uri,
                    'account': self.wallet.address,
                    'validated': True
                }

                print(f"\nNFT Minted Successfully!")
                print(f"  NFT ID: {nft_id}")
                print(f"  TX Hash: {tx_hash}")

                return result
            else:
                error_msg = str(response.result)
                print(f"\nTransaction Failed: {error_msg}")

                return {
                    'success': False,
                    'error': error_msg,
                    'uri': uri
                }

        except Exception as e:
            print(f"\nError minting NFT: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'uri': uri
            }

    def mint_nft_with_metadata(
        self,
        uri: str,
        validation_text: str,
        taxon: int = 0,
        transfer_fee: int = 0,
        flags: int = 8
    ) -> Dict[str, Any]:
        """
        Mint NFT with validation memo

        Args:
            uri: URI pointing to NFT metadata
            validation_text: Text for validation memo
            taxon: NFToken taxon
            transfer_fee: Transfer fee in basis points
            flags: NFToken flags

        Returns:
            Dict with mint result
        """
        return self.mint_nft(
            uri=uri,
            taxon=taxon,
            transfer_fee=transfer_fee,
            flags=flags,
            memo_data=validation_text,
            memo_type="validation"
        )

    def set_domain(self, domain: str) -> Dict[str, Any]:
        """
        Set account domain on XRPL

        Args:
            domain: Domain string to set (will be converted to hex)

        Returns:
            Dict with transaction result
        """
        try:
            print(f"\nSetting account domain...")
            print(f"  Domain: {domain}")
            print(f"  Account: {self.wallet.address}")

            # Convert domain to hex
            domain_hex = str_to_hex(domain)

            # Create AccountSet transaction
            account_set_tx = AccountSet(
                account=self.wallet.address,
                domain=domain_hex
            )

            print(f"\nSubmitting transaction to XRPL...")

            # Submit and wait for validation
            response = submit_and_wait(account_set_tx, self.client, self.wallet)

            if response.is_successful():
                tx_hash = response.result['hash']

                result = {
                    'success': True,
                    'tx_hash': tx_hash,
                    'domain': domain,
                    'domain_hex': domain_hex,
                    'account': self.wallet.address,
                    'validated': True
                }

                print(f"\nDomain Set Successfully!")
                print(f"  Domain: {domain}")
                print(f"  TX Hash: {tx_hash}")

                return result
            else:
                error_msg = str(response.result)
                print(f"\nTransaction Failed: {error_msg}")

                return {
                    'success': False,
                    'error': error_msg,
                    'domain': domain
                }

        except Exception as e:
            print(f"\nError setting domain: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'domain': domain
            }

    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information

        Returns:
            Dict with account details
        """
        try:
            from xrpl.models.requests import AccountInfo

            account_info_request = AccountInfo(
                account=self.wallet.address,
                ledger_index="validated"
            )

            response = self.client.request(account_info_request)

            if response.is_successful():
                return {
                    'success': True,
                    'account_data': response.result['account_data']
                }
            else:
                return {
                    'success': False,
                    'error': str(response.result)
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def get_nfts(self, account: Optional[str] = None) -> Dict[str, Any]:
        """
        Get NFTs owned by account

        Args:
            account: Account address (uses wallet address if not provided)

        Returns:
            Dict with list of NFTs
        """
        try:
            from xrpl.models.requests import AccountNFTs

            target_account = account or self.wallet.address

            nfts_request = AccountNFTs(
                account=target_account,
                ledger_index="validated"
            )

            response = self.client.request(nfts_request)

            if response.is_successful():
                return {
                    'success': True,
                    'nfts': response.result.get('account_nfts', []),
                    'account': target_account
                }
            else:
                return {
                    'success': False,
                    'error': str(response.result)
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def find_nft_by_uri(self, uri: str, account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Find NFT by URI in account's NFTs

        Args:
            uri: URI to search for (can be full URI or just CID)
            account: Account address (uses wallet address if not provided)

        Returns:
            NFT data if found, None otherwise
        """
        try:
            # Extract CID from URI if it's in ipfs:// format
            search_cid = uri.replace('ipfs://', '').strip()

            result = self.get_nfts(account)
            if not result['success']:
                return None

            nfts = result.get('nfts', [])
            for nft in nfts:
                nft_uri = nft.get('URI', '')
                # Decode hex URI to string
                try:
                    from xrpl.utils import hex_to_str
                    decoded_uri = hex_to_str(nft_uri) if nft_uri else ''
                    decoded_cid = decoded_uri.replace('ipfs://', '').strip()

                    # Match if CIDs match
                    if decoded_cid == search_cid or decoded_uri == uri:
                        return nft
                except Exception:
                    # If hex decode fails, try direct comparison
                    if nft_uri == uri:
                        return nft

            return None

        except Exception as e:
            print(f"  Error searching for NFT by URI: {str(e)}")
            return None

    def verify_transaction_success(self, tx_hash: str) -> Optional[str]:
        """
        Verify if a transaction succeeded and extract NFT ID

        Args:
            tx_hash: Transaction hash to verify

        Returns:
            NFT ID if transaction succeeded, None otherwise
        """
        try:
            from xrpl.models.requests import Tx

            print(f"  🔍 Verifying transaction {tx_hash[:16]}...")

            tx_request = Tx(transaction=tx_hash)
            response = self.client.request(tx_request)

            if response.is_successful():
                result = response.result
                meta = result.get('meta', {})

                # Check if transaction was successful
                if meta.get('TransactionResult') == 'tesSUCCESS':
                    print(f"  ✅ Transaction succeeded on-chain")
                    # Extract NFT ID
                    nft_id = self._extract_nft_id(response)
                    return nft_id
                else:
                    print(f"  ❌ Transaction failed: {meta.get('TransactionResult')}")
                    return None
            else:
                print(f"  ⚠️  Could not verify transaction")
                return None

        except Exception as e:
            print(f"  ⚠️  Error verifying transaction: {str(e)}")
            return None

    def _extract_nft_id(self, response) -> str:
        """
        Extract NFT ID from mint response

        Args:
            response: Transaction response

        Returns:
            NFT ID string
        """
        try:
            result = response.result
            meta = result.get('meta', {})

            # Primary location: result["meta"]["nftoken_id"]
            nft_id = meta.get('nftoken_id')
            if nft_id:
                return nft_id

            # Try alternative casings just in case
            nft_id = meta.get('NFTokenID') or meta.get('nftokenId')
            if nft_id:
                return nft_id

            # Fallback: Check AffectedNodes for NFTokenPage (older XRPL versions)
            affected_nodes = meta.get('AffectedNodes', [])
            for node in affected_nodes:
                # Check CreatedNode
                if 'CreatedNode' in node:
                    created = node['CreatedNode']
                    if created.get('LedgerEntryType') == 'NFTokenPage':
                        nftokens = created.get('NewFields', {}).get('NFTokens', [])
                        if nftokens:
                            nft_id = nftokens[0].get('NFToken', {}).get('NFTokenID')
                            if nft_id:
                                return nft_id

                # Check ModifiedNode
                if 'ModifiedNode' in node:
                    modified = node['ModifiedNode']
                    if modified.get('LedgerEntryType') == 'NFTokenPage':
                        nftokens = modified.get('FinalFields', {}).get('NFTokens', [])
                        if not nftokens:
                            nftokens = modified.get('NewFields', {}).get('NFTokens', [])

                        prev_nftokens = modified.get('PreviousFields', {}).get('NFTokens', [])

                        if nftokens:
                            if prev_nftokens:
                                prev_ids = {token.get('NFToken', {}).get('NFTokenID') for token in prev_nftokens}
                                for token in nftokens:
                                    nft_id = token.get('NFToken', {}).get('NFTokenID')
                                    if nft_id and nft_id not in prev_ids:
                                        return nft_id
                            else:
                                nft_id = nftokens[0].get('NFToken', {}).get('NFTokenID')
                                if nft_id:
                                    return nft_id

            # If still not found, print debug info
            print(f"  Warning: NFT ID not found in result.meta.nftoken_id")
            print(f"  Available keys in meta: {list(meta.keys())}")

            # Last resort: return transaction hash
            return response.result.get('hash', 'unknown')

        except Exception as e:
            print(f"  Error extracting NFT ID: {str(e)}")
            import traceback
            traceback.print_exc()
            return response.result.get('hash', 'unknown')


def create_xrpl_service() -> XRPLService:
    """
    Factory function to create XRPLService instance from environment variables

    Returns:
        XRPLService instance
    """
    node_url = os.getenv("XRPL_NODE_URL")
    wallet_secret = os.getenv("XRPL_SECRET")

    if not node_url:
        raise ValueError("XRPL_NODE_URL environment variable is required")

    if not wallet_secret:
        raise ValueError("XRPL_SECRET environment variable is required")

    return XRPLService(node_url, wallet_secret)
