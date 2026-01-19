# Source: https://docs.polymarket.com/developers/builders/relayer-client

On this page

* [Overview](#overview)
* [Builder API Credentials](#builder-api-credentials)
* [Installation](#installation)
* [Relayer Endpoint](#relayer-endpoint)
* [Signing Methods](#signing-methods)
* [Authentication Headers](#authentication-headers)
* [Wallet Types](#wallet-types)
* [Usage](#usage)
* [Deploy a Wallet](#deploy-a-wallet)
* [Execute Transactions](#execute-transactions)
* [Transaction Examples](#transaction-examples)
* [Reference](#reference)
* [Contracts & Approvals](#contracts-%26-approvals)
* [Transaction States](#transaction-states)
* [TypeScript Types](#typescript-types)
* [Next Steps](#next-steps)

## [​](#overview) Overview

The Relayer Client routes onchain transactions through Polymarket’s infrastructure, providing gasless transactions for your users. Builder authentication is required to access the relayer.

## Gasless Transactions

Polymarket pays all gas fees

## Wallet Deployment

Deploy Safe or Proxy wallets

## CTF Operations

Split, merge, and redeem positions

---

## [​](#builder-api-credentials) Builder API Credentials

Each builder receives API credentials from their [Builder Profile](/developers/builders/builder-profile):

| Credential | Description |
| --- | --- |
| `key` | Your builder API key identifier |
| `secret` | Secret key for signing requests |
| `passphrase` | Additional authentication passphrase |

**Security Notice**: Your Builder API keys must be kept secure. Never expose them in client-side code.

---

## [​](#installation) Installation

TypeScript

Python

Copy

Ask AI

```
npm install @polymarket/builder-relayer-client
```

---

## [​](#relayer-endpoint) Relayer Endpoint

All relayer requests are sent to Polymarket’s relayer service on Polygon:

Copy

Ask AI

```
https://relayer-v2.polymarket.com/
```

---

## [​](#signing-methods) Signing Methods

* Remote Signing (Recommended)
* Local Signing

Remote signing keeps your credentials secure on a server you control.**How it works:**

1. Client sends request details to your signing server
2. Your server generates the HMAC signature
3. Client attaches headers and sends to relayer

### [​](#server-implementation) Server Implementation

Your signing server receives request details and returns the authentication headers:

TypeScript

Python

Copy

Ask AI

```
import { 
  buildHmacSignature, 
  BuilderApiKeyCreds 
} from "@polymarket/builder-signing-sdk";

const BUILDER_CREDENTIALS: BuilderApiKeyCreds = {
  key: process.env.POLY_BUILDER_API_KEY!,
  secret: process.env.POLY_BUILDER_SECRET!,
  passphrase: process.env.POLY_BUILDER_PASSPHRASE!,
};

// POST /sign - receives { method, path, body } from the client SDK
export async function handleSignRequest(request) {
  const { method, path, body } = await request.json();
  
  const timestamp = Date.now().toString();
  
  const signature = buildHmacSignature(
    BUILDER_CREDENTIALS.secret,
    parseInt(timestamp),
    method,
    path,
    body
  );

  return {
    POLY_BUILDER_SIGNATURE: signature,
    POLY_BUILDER_TIMESTAMP: timestamp,
    POLY_BUILDER_API_KEY: BUILDER_CREDENTIALS.key,
    POLY_BUILDER_PASSPHRASE: BUILDER_CREDENTIALS.passphrase,
  };
}
```

Never commit credentials to version control. Use environment variables or a secrets manager.

### [​](#client-configuration) Client Configuration

Point your client to your signing server:

TypeScript

Python

Copy

Ask AI

```
import { createWalletClient, http, Hex } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { polygon } from "viem/chains";
import { RelayClient } from "@polymarket/builder-relayer-client";
import { BuilderConfig } from "@polymarket/builder-signing-sdk";

// Create wallet
const account = privateKeyToAccount(process.env.PRIVATE_KEY as Hex);
const wallet = createWalletClient({
  account,
  chain: polygon,
  transport: http(process.env.RPC_URL)
});

// Configure remote signing
const builderConfig = new BuilderConfig({
  remoteBuilderConfig: { 
    url: "https://your-server.com/sign" 
  }
});

const RELAYER_URL = "https://relayer-v2.polymarket.com/";
const CHAIN_ID = 137;

const client = new RelayClient(
  RELAYER_URL,
  CHAIN_ID,
  wallet,
  builderConfig
);
```

Sign locally when your backend handles all transactions.**How it works:**

1. Your system creates transactions on behalf of users
2. Your system uses Builder API credentials locally to add headers
3. Complete signed request is sent directly to the relayer

TypeScript

Python

Copy

Ask AI

```
import { createWalletClient, http, Hex } from "viem";
import { privateKeyToAccount } from "viem/accounts";
import { polygon } from "viem/chains";
import { RelayClient } from "@polymarket/builder-relayer-client";
import { BuilderConfig } from "@polymarket/builder-signing-sdk";

// Create wallet
const account = privateKeyToAccount(process.env.PRIVATE_KEY as Hex);
const wallet = createWalletClient({
  account,
  chain: polygon,
  transport: http(process.env.RPC_URL)
});

// Configure local signing
const builderConfig = new BuilderConfig({
  localBuilderCreds: {
    key: process.env.POLY_BUILDER_API_KEY!,
    secret: process.env.POLY_BUILDER_SECRET!,
    passphrase: process.env.POLY_BUILDER_PASSPHRASE!
  }
});

const RELAYER_URL = "https://relayer-v2.polymarket.com/";
const CHAIN_ID = 137;

const client = new RelayClient(
  RELAYER_URL,
  CHAIN_ID,
  wallet,
  builderConfig
);
```

Never commit credentials to version control. Use environment variables or a secrets manager.

---

## [​](#authentication-headers) Authentication Headers

The SDK automatically generates and attaches these headers to each request:

| Header | Description |
| --- | --- |
| `POLY_BUILDER_API_KEY` | Your builder API key |
| `POLY_BUILDER_TIMESTAMP` | Unix timestamp of signature creation |
| `POLY_BUILDER_PASSPHRASE` | Your builder passphrase |
| `POLY_BUILDER_SIGNATURE` | HMAC signature of the request |

With **local signing**, the SDK constructs and attaches these headers automatically. With **remote signing**, your server must return these headers (see Server Implementation above), and the SDK attaches them to the request.

---

## [​](#wallet-types) Wallet Types

Choose your wallet type before using the relayer:

* Safe Wallets
* Proxy Wallets

Gnosis Safe-based proxy wallets that require explicit deployment before use.

* **Best for:** Most builder integrations
* **Deployment:** Call `client.deploy()` before first transaction
* **Gas fees:** Paid by Polymarket

TypeScript

Python

Copy

Ask AI

```
const client = new RelayClient(
  "https://relayer-v2.polymarket.com", 
  137,
  eoaSigner, 
  builderConfig, 
  RelayerTxType.SAFE  // Default
);

// Deploy before first use
const response = await client.deploy();
const result = await response.wait();
console.log("Safe Address:", result?.proxyAddress);
```

Custom Polymarket proxy wallets that auto-deploy on first transaction.

* **Used for:** Magic Link users from Polymarket.com
* **Deployment:** Automatic on first transaction
* **Gas fees:** Paid by Polymarket

TypeScript

Python

Copy

Ask AI

```
const client = new RelayClient(
  "https://relayer-v2.polymarket.com", 
  137,
  eoaSigner, 
  builderConfig, 
  RelayerTxType.PROXY
);

// No deploy() needed - auto-deploys on first tx
await client.execute([transaction], "First transaction");
```

Wallet Comparison Table

| Feature | Safe Wallets | Proxy Wallets |
| --- | --- | --- |
| Deployment | Explicit `deploy()` | Auto-deploy on first tx |
| Gas Fees | Polymarket pays | Polymarket pays |
| ERC20 Approvals | ✅ | ✅ |
| CTF Operations | ✅ | ✅ |
| Send Transactions | ✅ | ✅ |



---

## [​](#usage) Usage

### [​](#deploy-a-wallet) Deploy a Wallet

For Safe wallets, deploy before executing transactions:

TypeScript

Python

Copy

Ask AI

```
const response = await client.deploy();
const result = await response.wait();

if (result) {
  console.log("Safe deployed successfully!");
  console.log("Transaction Hash:", result.transactionHash);
  console.log("Safe Address:", result.proxyAddress);
}
```

### [​](#execute-transactions) Execute Transactions

The `execute` method sends transactions through the relayer. Pass an array of transactions to batch multiple operations in a single call.

TypeScript

Python

Copy

Ask AI

```
interface Transaction {
  to: string;    // Target contract or wallet address
  data: string;  // Encoded function call (use "0x" for simple transfers)
  value: string; // Amount of MATIC to send (usually "0")
}

const response = await client.execute(transactions, "Description");
const result = await response.wait();

if (result) {
  console.log("Transaction confirmed:", result.transactionHash);
}
```

### [​](#transaction-examples) Transaction Examples

* Transfer
* Approve
* Redeem Positions
* Split Positions
* Merge Positions
* Batch Transactions

Transfer tokens to any address (e.g., withdrawals):

TypeScript

Python

Copy

Ask AI

```
import { encodeFunctionData, parseUnits } from "viem";

const transferTx = {
  to: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", // USDCe
  data: encodeFunctionData({
    abi: [{
      name: "transfer",
      type: "function",
      inputs: [
        { name: "to", type: "address" },
        { name: "amount", type: "uint256" }
      ],
      outputs: [{ type: "bool" }]
    }],
    functionName: "transfer",
    args: [
      "0xRecipientAddressHere",
      parseUnits("100", 6) // 100 USDCe (6 decimals)
    ]
  }),
  value: "0"
};

const response = await client.execute([transferTx], "Transfer USDCe");
await response.wait();
```

Set token allowances to enable trading:

TypeScript

Python

Copy

Ask AI

```
import { encodeFunctionData, maxUint256 } from "viem";

const approveTx = {
  to: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", // USDCe
  data: encodeFunctionData({
    abi: [{
      name: "approve",
      type: "function",
      inputs: [
        { name: "spender", type: "address" },
        { name: "amount", type: "uint256" }
      ],
      outputs: [{ type: "bool" }]
    }],
    functionName: "approve",
    args: [
      "0x4d97dcd97ec945f40cf65f87097ace5ea0476045", // CTF
      maxUint256
    ]
  }),
  value: "0"
};

const response = await client.execute([approveTx], "Approve USDCe for CTF");
await response.wait();
```

Redeem winning conditional tokens after market resolution:

TypeScript

Python

Copy

Ask AI

```
import { encodeFunctionData } from "viem";

const redeemTx = {
  to: ctfAddress,
  data: encodeFunctionData({
    abi: [{
      name: "redeemPositions",
      type: "function",
      inputs: [
        { name: "collateralToken", type: "address" },
        { name: "parentCollectionId", type: "bytes32" },
        { name: "conditionId", type: "bytes32" },
        { name: "indexSets", type: "uint256[]" }
      ],
      outputs: []
    }],
    functionName: "redeemPositions",
    args: [collateralToken, parentCollectionId, conditionId, indexSets]
  }),
  value: "0"
};

const response = await client.execute([redeemTx], "Redeem positions");
await response.wait();
```

Split collateral tokens into conditional outcome tokens:

TypeScript

Python

Copy

Ask AI

```
import { encodeFunctionData } from "viem";

const splitTx = {
  to: ctfAddress,
  data: encodeFunctionData({
    abi: [{
      name: "splitPosition",
      type: "function",
      inputs: [
        { name: "collateralToken", type: "address" },
        { name: "parentCollectionId", type: "bytes32" },
        { name: "conditionId", type: "bytes32" },
        { name: "partition", type: "uint256[]" },
        { name: "amount", type: "uint256" }
      ],
      outputs: []
    }],
    functionName: "splitPosition",
    args: [collateralToken, parentCollectionId, conditionId, partition, amount]
  }),
  value: "0"
};

const response = await client.execute([splitTx], "Split positions");
await response.wait();
```

Merge conditional tokens back into collateral:

TypeScript

Python

Copy

Ask AI

```
import { encodeFunctionData } from "viem";

const mergeTx = {
  to: ctfAddress,
  data: encodeFunctionData({
    abi: [{
      name: "mergePositions",
      type: "function",
      inputs: [
        { name: "collateralToken", type: "address" },
        { name: "parentCollectionId", type: "bytes32" },
        { name: "conditionId", type: "bytes32" },
        { name: "partition", type: "uint256[]" },
        { name: "amount", type: "uint256" }
      ],
      outputs: []
    }],
    functionName: "mergePositions",
    args: [collateralToken, parentCollectionId, conditionId, partition, amount]
  }),
  value: "0"
};

const response = await client.execute([mergeTx], "Merge positions");
await response.wait();
```

Execute multiple transactions atomically in a single call:

TypeScript

Python

Copy

Ask AI

```
import { encodeFunctionData, parseUnits, maxUint256 } from "viem";

const erc20Abi = [
  {
    name: "approve",
    type: "function",
    inputs: [
      { name: "spender", type: "address" },
      { name: "amount", type: "uint256" }
    ],
    outputs: [{ type: "bool" }]
  },
  {
    name: "transfer",
    type: "function",
    inputs: [
      { name: "to", type: "address" },
      { name: "amount", type: "uint256" }
    ],
    outputs: [{ type: "bool" }]
  }
] as const;

// Approve CTF to spend USDCe
const approveTx = {
  to: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
  data: encodeFunctionData({
    abi: erc20Abi,
    functionName: "approve",
    args: ["0x4d97dcd97ec945f40cf65f87097ace5ea0476045", maxUint256]
  }),
  value: "0"
};

// Transfer some USDCe to another wallet
const transferTx = {
  to: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
  data: encodeFunctionData({
    abi: erc20Abi,
    functionName: "transfer",
    args: ["0xRecipientAddressHere", parseUnits("50", 6)]
  }),
  value: "0"
};

// Both transactions execute in one call
const response = await client.execute(
  [approveTx, transferTx], 
  "Approve and transfer"
);
await response.wait();
```

Batching reduces latency and ensures all transactions succeed or fail together.

---

## [​](#reference) Reference

### [​](#contracts-&-approvals) Contracts & Approvals

| Contract | Address | USDCe | Outcome Tokens |
| --- | --- | --- | --- |
| USDCe | `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174` | — | — |
| CTF | `0x4d97dcd97ec945f40cf65f87097ace5ea0476045` | ✅ | — |
| CTF Exchange | `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E` | ✅ | ✅ |
| Neg Risk CTF Exchange | `0xC5d563A36AE78145C45a50134d48A1215220f80a` | ✅ | ✅ |
| Neg Risk Adapter | `0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296` | — | ✅ |

### [​](#transaction-states) Transaction States

| State | Description |
| --- | --- |
| `STATE_NEW` | Transaction received by relayer |
| `STATE_EXECUTED` | Transaction executed onchain |
| `STATE_MINED` | Transaction included in a block |
| `STATE_CONFIRMED` | Transaction confirmed (final ✅) |
| `STATE_FAILED` | Transaction failed (terminal ❌) |
| `STATE_INVALID` | Transaction rejected as invalid (terminal ❌) |

### [​](#typescript-types) TypeScript Types

View Type Definitions

Copy

Ask AI

```
// Transaction type used in all examples
interface Transaction {
  to: string;
  data: string;
  value: string;
}

// Wallet type selector
enum RelayerTxType {
  SAFE = "SAFE",
  PROXY = "PROXY"
}

// Transaction states
enum RelayerTransactionState {
  STATE_NEW = "STATE_NEW",
  STATE_EXECUTED = "STATE_EXECUTED",
  STATE_MINED = "STATE_MINED",
  STATE_CONFIRMED = "STATE_CONFIRMED",
  STATE_FAILED = "STATE_FAILED",
  STATE_INVALID = "STATE_INVALID"
}

// Response from relayer
interface RelayerTransaction {
  transactionID: string;
  transactionHash: string;
  from: string;
  to: string;
  proxyAddress: string;
  data: string;
  state: string;
  type: string;
  metadata: string;
  createdAt: Date;
  updatedAt: Date;
}
```



---

## [​](#next-steps) Next Steps

[## Order Attribution

Attribute orders to your builder account](/developers/builders/order-attribution)[## Example Apps

Complete integration examples](/developers/builders/examples)

[Order Attribution](/developers/builders/order-attribution)[Examples](/developers/builders/examples)

⌘I