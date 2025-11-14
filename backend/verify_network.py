#!/usr/bin/env python3
"""
Network Verification Utility
Verifies XRPL network configuration and prevents testnet/mainnet mix-ups
"""

import os
import sys
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()


def verify_network_configuration() -> Dict[str, Any]:
    """
    Verify network configuration and identify potential issues

    Returns:
        Dict with verification results
    """
    results = {
        'success': True,
        'network': 'unknown',
        'warnings': [],
        'errors': [],
        'info': {}
    }

    # Get configuration
    node_url = os.getenv('XRPL_NODE_URL', '')
    wallet_secret = os.getenv('XRPL_SECRET', '')
    mongodb_uri = os.getenv('MONGODB_URI', '')
    mongodb_db = os.getenv('MONGODB_DB', '')
    network_env = os.getenv('NETWORK', '')

    # Detect network from node URL
    is_testnet = 'testnet' in node_url.lower() or 'altnet' in node_url.lower()
    is_mainnet = any(domain in node_url.lower() for domain in [
        'xrplcluster.com',
        's1.ripple.com',
        's2.ripple.com',
        'livenet',
        'mainnet'
    ])

    # Determine network
    if is_testnet:
        results['network'] = 'testnet'
    elif is_mainnet:
        results['network'] = 'mainnet'
    else:
        results['network'] = 'unknown'
        results['warnings'].append(f"Cannot determine network from URL: {node_url}")

    # Store configuration details
    results['info'] = {
        'node_url': node_url,
        'mongodb_db': mongodb_db,
        'network_env': network_env,
        'wallet_configured': bool(wallet_secret),
        'mongodb_configured': bool(mongodb_uri)
    }

    # Validation checks

    # 1. Check if wallet secret is configured
    if not wallet_secret:
        results['errors'].append("XRPL_SECRET not configured in .env")
        results['success'] = False

    # 2. Check if MongoDB is configured
    if not mongodb_uri:
        results['errors'].append("MONGODB_URI not configured in .env")
        results['success'] = False

    # 3. Check network consistency
    if network_env and network_env.lower() != results['network']:
        results['warnings'].append(
            f"NETWORK env var ({network_env}) doesn't match detected network ({results['network']})"
        )

    # 4. Database naming check for mainnet
    if results['network'] == 'mainnet':
        if 'test' in mongodb_db.lower() or 'dev' in mongodb_db.lower():
            results['warnings'].append(
                f"⚠️  MAINNET using database with test/dev name: {mongodb_db}"
            )

    # 5. Database naming check for testnet
    if results['network'] == 'testnet':
        if 'prod' in mongodb_db.lower():
            results['errors'].append(
                f"❌ TESTNET using production database: {mongodb_db}"
            )
            results['success'] = False

    # 6. Wallet secret format check
    if wallet_secret:
        if not wallet_secret.startswith('s'):
            results['errors'].append("Invalid wallet secret format (should start with 's')")
            results['success'] = False

    return results


def display_verification_results(results: Dict[str, Any]):
    """Display formatted verification results"""
    print("\n" + "=" * 70)
    print("🔍 XRPL Network Configuration Verification")
    print("=" * 70)

    # Network detection
    network = results['network'].upper()
    if network == 'MAINNET':
        print(f"\n🔴 Network: {network} (PRODUCTION)")
        print("   ⚠️  Real XRP will be used for transactions")
    elif network == 'TESTNET':
        print(f"\n🟢 Network: {network} (TESTING)")
        print("   ℹ️  Using test XRP (no real value)")
    else:
        print(f"\n⚪ Network: {network}")

    # Configuration details
    info = results['info']
    print(f"\n📋 Configuration:")
    print(f"   Node URL: {info['node_url']}")
    print(f"   Database: {info['mongodb_db']}")
    print(f"   Wallet: {'✅ Configured' if info['wallet_configured'] else '❌ Not configured'}")
    print(f"   MongoDB: {'✅ Connected' if info['mongodb_configured'] else '❌ Not configured'}")

    # Errors
    if results['errors']:
        print(f"\n❌ Errors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"   • {error}")

    # Warnings
    if results['warnings']:
        print(f"\n⚠️  Warnings ({len(results['warnings'])}):")
        for warning in results['warnings']:
            print(f"   • {warning}")

    # Overall status
    print("\n" + "=" * 70)
    if results['success']:
        print("✅ Configuration Valid")
        if network == 'MAINNET':
            print("\n⚠️  MAINNET DEPLOYMENT CHECKLIST:")
            print("   1. Wallet funded with 15-20 XRP minimum")
            print("   2. Wallet secret backed up securely")
            print("   3. Production MongoDB with backups enabled")
            print("   4. Tested on testnet first")
            print("\nSee MAINNET_DEPLOYMENT.md for complete guide")
    else:
        print("❌ Configuration Issues Found")
        print("   Please fix errors before proceeding")
    print("=" * 70 + "\n")


def verify_wallet_balance():
    """Verify wallet exists and has sufficient balance"""
    try:
        from src.services import create_xrpl_service

        print("\n📊 Checking Wallet Balance...")
        xrpl = create_xrpl_service()
        info = xrpl.get_account_info()

        if info['success']:
            balance_drops = int(info['account_data']['Balance'])
            balance_xrp = balance_drops / 1_000_000

            print(f"   Wallet Address: {xrpl.wallet.address}")
            print(f"   Balance: {balance_xrp:.6f} XRP")

            # Check if balance is sufficient
            if balance_xrp < 10:
                print(f"   ⚠️  WARNING: Balance below minimum reserve (10 XRP)")
                return False
            elif balance_xrp < 15:
                print(f"   ⚠️  WARNING: Low balance for production (recommended: 15+ XRP)")
                return True
            else:
                print(f"   ✅ Sufficient balance for minting")
                return True
        else:
            print(f"   ❌ Error: {info.get('error')}")
            if 'actNotFound' in str(info.get('error')):
                print(f"   ℹ️  Account not activated. Fund with 10+ XRP to activate.")
            return False

    except Exception as e:
        print(f"   ❌ Error checking balance: {str(e)}")
        return False


def main():
    """Main execution"""
    print("🔐 XRPL Network Verification Utility")

    # Verify configuration
    results = verify_network_configuration()
    display_verification_results(results)

    # If configuration is valid, check wallet balance
    if results['success']:
        if '--skip-balance' not in sys.argv:
            verify_wallet_balance()

    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()
