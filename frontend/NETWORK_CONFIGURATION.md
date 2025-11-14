# XRPL Network Configuration

This application supports both XRPL testnet and mainnet configurations through environment variables.

## Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env.local
   ```

2. **Configure the network in `.env.local`:**

   For **Mainnet** (default):
   ```env
   NEXT_PUBLIC_XRPL_NETWORK=mainnet
   NEXT_PUBLIC_WALLET_ADDRESS=rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp
   ```

   For **Testnet**:
   ```env
   NEXT_PUBLIC_XRPL_NETWORK=testnet
   NEXT_PUBLIC_WALLET_ADDRESS=your-testnet-wallet-address
   ```

## Environment Variables

### `NEXT_PUBLIC_XRPL_NETWORK`
- **Required**: No
- **Values**: `testnet` | `mainnet`
- **Default**: `mainnet` (if not set or invalid value)
- **Description**: Determines which XRPL network the application connects to

### `NEXT_PUBLIC_WALLET_ADDRESS`
- **Required**: No
- **Default**: `rBCA9v3tQMLSnRdEFqN5eYvbwx34P9R9Qp`
- **Description**: The wallet address to query for NFTs

## Network Details

### Testnet
- **WebSocket URL**: `wss://s.altnet.rippletest.net:51233`
- **Explorer**: https://testnet.xrpl.org
- **Bithomp**: https://test.bithomp.com

### Mainnet
- **WebSocket URL**: `wss://xrplcluster.com`
- **Explorer**: https://livenet.xrpl.org
- **Bithomp**: https://bithomp.com

## Switching Networks

To switch from mainnet to testnet:

1. Open `.env.local`
2. Change `NEXT_PUBLIC_XRPL_NETWORK=mainnet` to `NEXT_PUBLIC_XRPL_NETWORK=testnet`
3. Update `NEXT_PUBLIC_WALLET_ADDRESS` to your testnet wallet address
4. Restart the development server:
   ```bash
   npm run dev
   ```

To switch from testnet to mainnet:

1. Open `.env.local`
2. Change `NEXT_PUBLIC_XRPL_NETWORK=testnet` to `NEXT_PUBLIC_XRPL_NETWORK=mainnet`
3. Update `NEXT_PUBLIC_WALLET_ADDRESS` to your mainnet wallet address
4. Restart the development server:
   ```bash
   npm run dev
   ```

## Important Notes

- **Default Network**: If `NEXT_PUBLIC_XRPL_NETWORK` is not set, the application defaults to **mainnet**
- Environment variables prefixed with `NEXT_PUBLIC_` are exposed to the browser
- Changes to `.env.local` require restarting the development server
- The `.env.local` file is gitignored and should never be committed
- Use `.env.example` as a template for required environment variables
- All explorer URLs and network connections automatically adjust based on the configured network
