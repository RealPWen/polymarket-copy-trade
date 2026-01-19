# Source: https://docs.polymarket.com/developers/CLOB/quickstart

On this page

* [Installation](#installation)
* [Quick Start](#quick-start)
* [1. Setup Client](#1-setup-client)
* [2. Place an Order](#2-place-an-order)
* [3. Check Your Orders](#3-check-your-orders)
* [Complete Example](#complete-example)
* [Troubleshooting](#troubleshooting)
* [Next Steps](#next-steps)

## [​](#installation) Installation

TypeScript

Python

Copy

Ask AI

```
npm install @polymarket/clob-client ethers
```

---

## [​](#quick-start) Quick Start

### [​](#1-setup-client) 1. Setup Client

TypeScript

Python

Copy

Ask AI

```
import { ClobClient } from "@polymarket/clob-client";
import { Wallet } from "ethers"; // v5.8.0

const HOST = "https://clob.polymarket.com";
const CHAIN_ID = 137; // Polygon mainnet
const signer = new Wallet(process.env.PRIVATE_KEY);

// Create or derive user API credentials
const tempClient = new ClobClient(HOST, CHAIN_ID, signer);
const apiCreds = await tempClient.createOrDeriveApiKey();

// See 'Signature Types' note below
const signatureType = 0;

// Initialize trading client
const client = new ClobClient(
  HOST, 
  CHAIN_ID, 
  signer, 
  apiCreds, 
  signatureType
);
```

This quick start sets your EOA as the trading account. You’ll need to fund this
wallet to trade and pay for gas on transactions. Gas-less transactions are only
available by deploying a proxy wallet and using Polymarket’s Polygon relayer
infrastructure.

Signature Types

| Wallet Type | ID | When to Use |
| --- | --- | --- |
| EOA | `0` | Standard Ethereum wallet (MetaMask) |
| Custom Proxy | `1` | Specific to Magic Link users from Polymarket only |
| Gnosis Safe | `2` | Injected providers (Metamask, Rabby, embedded wallets) |



---

### [​](#2-place-an-order) 2. Place an Order

TypeScript

Python

Copy

Ask AI

```
import { Side } from "@polymarket/clob-client";

// Place a limit order in one step
const response = await client.createAndPostOrder({
  tokenID: "YOUR_TOKEN_ID", // Get from Gamma API
  price: 0.65, // Price per share
  size: 10, // Number of shares
  side: Side.BUY, // or SELL
});

console.log(`Order placed! ID: ${response.orderID}`);
```

---

### [​](#3-check-your-orders) 3. Check Your Orders

TypeScript

Python

Copy

Ask AI

```
// View all open orders
const openOrders = await client.getOpenOrders();
console.log(`You have ${openOrders.length} open orders`);

// View your trade history
const trades = await client.getTrades();
console.log(`You've made ${trades.length} trades`);
```

---

## [​](#complete-example) Complete Example

TypeScript

Python

Copy

Ask AI

```
import { ClobClient, Side } from "@polymarket/clob-client";
import { Wallet } from "ethers";

async function trade() {
  const HOST = "https://clob.polymarket.com";
  const CHAIN_ID = 137; // Polygon mainnet
  const signer = new Wallet(process.env.PRIVATE_KEY);

  const tempClient = new ClobClient(HOST, CHAIN_ID, signer);
  const apiCreds = await tempClient.createOrDeriveApiKey();

  const signatureType = 0;

  const client = new ClobClient(
    HOST,
    CHAIN_ID,
    signer,
    apiCreds,
    signatureType
  );

  const response = await client.createAndPostOrder({
    tokenID: "YOUR_TOKEN_ID",
    price: 0.65,
    size: 10,
    side: Side.BUY,
  });

  console.log(`Order placed! ID: ${response.orderID}`);
}

trade();
```

---

## [​](#troubleshooting) Troubleshooting

Error: L2\_AUTH\_NOT\_AVAILABLE

You forgot to call `createOrDeriveApiKey()`. Make sure you initialize the client with API credentials:

Copy

Ask AI

```
const creds = await clobClient.createOrDeriveApiKey();
const client = new ClobClient(host, chainId, wallet, creds);
```

Order rejected: insufficient balance

Ensure you have:

* **USDC** in your funder address for BUY orders
* **Outcome tokens** in your funder address for SELL orders

Check your balance at [polymarket.com/portfolio](https://polymarket.com/portfolio).

Order rejected: insufficient allowance

You need to approve the Exchange contract to spend your tokens. This is typically done through the Polymarket UI on your first trade. Or use the CTF contract’s `setApprovalForAll()` method.

What's my funder address?

Your funder address is the Polymarket proxy wallet where you deposit funds. Find it:

1. Go to [polymarket.com/settings](https://polymarket.com/settings)
2. Look for “Wallet Address” or “Profile Address”
3. This is your `FUNDER_ADDRESS`

---

## [​](#next-steps) Next Steps

[## Full Example Implementations

Complete Next.js examples demonstrating integration of embedded wallets
(Privy, Magic, Turnkey, wagmi) and the CLOB and Builder Relay clients](/developers/builders/examples)

[## Understand CLOB Authentication

Deep dive into L1 and L2 authentication](/developers/CLOB/authentication)[## Browse Client Methods

Explore the complete client reference](/developers/CLOB/clients/methods-overview)[## Find Markets to Trade

Use Gamma API to discover markets](/developers/gamma-markets-api/get-markets)[## Monitor with WebSocket

Get real-time order updates](/developers/CLOB/websocket/wss-overview)

[Status](/developers/CLOB/status)[Authentication](/developers/CLOB/authentication)

⌘I