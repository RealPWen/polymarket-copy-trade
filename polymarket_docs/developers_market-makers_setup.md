# Source: https://docs.polymarket.com/developers/market-makers/setup

On this page

* [Overview](#overview)
* [Deposit USDCe](#deposit-usdce)
* [Options](#options)
* [Using the Bridge API](#using-the-bridge-api)
* [Wallet Options](#wallet-options)
* [EOA (Externally Owned Account)](#eoa-externally-owned-account)
* [Safe Wallet (Recommended)](#safe-wallet-recommended)
* [Token Approvals](#token-approvals)
* [Required Approvals](#required-approvals)
* [Contract Addresses (Polygon Mainnet)](#contract-addresses-polygon-mainnet)
* [Approve via Relayer Client](#approve-via-relayer-client)
* [API Key Generation](#api-key-generation)
* [Generate API Key](#generate-api-key)
* [Using Credentials](#using-credentials)
* [Next Steps](#next-steps)

## [​](#overview) Overview

Before you can start market making on Polymarket, you need to complete these one-time setup steps:

1. Deposit bridged USDCe to Polygon
2. Deploy a wallet (EOA or Safe)
3. Approve tokens for trading
4. Generate API credentials

## [​](#deposit-usdce) Deposit USDCe

Market makers need USDCe on Polygon to fund their trading operations.

### [​](#options) Options

| Method | Best For | Documentation |
| --- | --- | --- |
| Bridge API | Automated deposits from other chains | [Bridge Overview](/developers/misc-endpoints/bridge-overview) |
| Direct Polygon transfer | Already have USDCe on Polygon | N/A |
| Cross-chain bridge | Large deposits from Ethereum | [Large Deposits](/polymarket-learn/deposits/large-cross-chain-deposits) |

### [​](#using-the-bridge-api) Using the Bridge API

Copy

Ask AI

```
// Deposit USDCe from Ethereum to Polygon
const deposit = await fetch("https://clob.polymarket.com/deposit", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    chainId: "1",
    fromChain: "ethereum",
    toChain: "polygon",
    asset: "USDCe",
    amount: "100000000000" // $100,000 in USDCe (6 decimals)
  })
});
```

See [Bridge Deposit](/developers/misc-endpoints/bridge-deposit) for full API details.

## [​](#wallet-options) Wallet Options

### [​](#eoa-externally-owned-account) EOA (Externally Owned Account)

Standard Ethereum wallet. You pay for all onchain transactions (approvals, splits, merges, trade exedcution).

### [​](#safe-wallet-recommended) Safe Wallet (Recommended)

Gnosis Safe-based wallet deployed via Polymarket’s relayer. Benefits:

* **Gasless transactions** - Polymarket pays gas fees for onchain operations
* **Contract wallet** - Enables advanced features like batched transactions.

Deploy a Safe wallet using the [Relayer Client](/developers/builders/relayer-client):

Copy

Ask AI

```
import { RelayClient, RelayerTxType } from "@polymarket/builder-relayer-client";

const client = new RelayClient(
  "https://relayer-v2.polymarket.com/",
  137, // Polygon mainnet
  signer,
  builderConfig,
  RelayerTxType.SAFE
);

// Deploy the Safe wallet
const response = await client.deploy();
const result = await response.wait();
console.log("Safe Address:", result?.proxyAddress);
```

## [​](#token-approvals) Token Approvals

Before trading, you must approve the exchange contracts to spend your tokens.

### [​](#required-approvals) Required Approvals

| Token | Spender | Purpose |
| --- | --- | --- |
| USDCe | CTF Contract | Split USDCe into outcome tokens |
| CTF (outcome tokens) | CTF Exchange | Trade outcome tokens |
| CTF (outcome tokens) | Neg Risk CTF Exchange | Trade neg-risk market tokens |

### [​](#contract-addresses-polygon-mainnet) Contract Addresses (Polygon Mainnet)

Copy

Ask AI

```
const ADDRESSES = {
  USDCe: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
  CTF: "0x4d97dcd97ec945f40cf65f87097ace5ea0476045",
  CTF_EXCHANGE: "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E",
  NEG_RISK_CTF_EXCHANGE: "0xC5d563A36AE78145C45a50134d48A1215220f80a",
  NEG_RISK_ADAPTER: "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296"
};
```

### [​](#approve-via-relayer-client) Approve via Relayer Client

Copy

Ask AI

```
import { ethers } from "ethers";
import { Interface } from "ethers/lib/utils";

const erc20Interface = new Interface([
  "function approve(address spender, uint256 amount) returns (bool)"
]);

// Approve USDCe for CTF contract
const approveTx = {
  to: ADDRESSES.USDCe,
  data: erc20Interface.encodeFunctionData("approve", [
    ADDRESSES.CTF,
    ethers.constants.MaxUint256
  ]),
  value: "0"
};

const response = await client.execute([approveTx], "Approve USDCe for CTF");
await response.wait();
```

See [Relayer Client](/developers/builders/relayer-client) for complete examples.

## [​](#api-key-generation) API Key Generation

To place orders and access authenticated endpoints, you need L2 API credentials.

### [​](#generate-api-key) Generate API Key

Copy

Ask AI

```
import { ClobClient } from "@polymarket/clob-client";

const client = new ClobClient(
  "https://clob.polymarket.com",
  137,
  signer
);

// Derive API credentials from your wallet
const credentials = await client.deriveApiKey();
console.log("API Key:", credentials.key);
console.log("Secret:", credentials.secret);
console.log("Passphrase:", credentials.passphrase);
```

### [​](#using-credentials) Using Credentials

Once you have credentials, initialize the client for authenticated operations:

Copy

Ask AI

```
const client = new ClobClient(
  "https://clob.polymarket.com",
  137,
  wallet,
  credentials
);
```

See [CLOB Authentication](/developers/CLOB/authentication) for full details.

## [​](#next-steps) Next Steps

Once setup is complete:

[## Start Trading

Post limit orders and manage quotes](/developers/market-makers/trading)[## Connect to RFQ

Respond to Request for Quote requests](/developers/market-makers/rfq/overview)

[Market Maker Introduction](/developers/market-makers/introduction)[Trading](/developers/market-makers/trading)

⌘I