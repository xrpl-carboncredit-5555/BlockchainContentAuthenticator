// Simple test script to verify XRPL connection
const { Client } = require('xrpl');

async function testConnection() {
  const testnetClient = new Client('wss://s.altnet.rippletest.net:51233');
  const mainnetClient = new Client('wss://xrplcluster.com');

  const address = 'rrn5TTseRjmcV3Da3Z4ituzKsoXWVqYpbg';

  console.log(`Testing XRPL connection for address: ${address}`);

  // Test testnet
  try {
    console.log('\n--- Testing Testnet ---');
    await testnetClient.connect();
    console.log('Connected to testnet');

    const testnetRequest = {
      command: 'account_nfts',
      account: address
    };

    const testnetResponse = await testnetClient.request(testnetRequest);
    console.log('Testnet response:', testnetResponse);

    await testnetClient.disconnect();
  } catch (error) {
    console.log('Testnet error:', error.message);
  }

  // Test mainnet
  try {
    console.log('\n--- Testing Mainnet ---');
    await mainnetClient.connect();
    console.log('Connected to mainnet');

    const mainnetRequest = {
      command: 'account_nfts',
      account: address
    };

    const mainnetResponse = await mainnetClient.request(mainnetRequest);
    console.log('Mainnet response:', mainnetResponse);

    await mainnetClient.disconnect();
  } catch (error) {
    console.log('Mainnet error:', error.message);
  }
}

testConnection().catch(console.error);