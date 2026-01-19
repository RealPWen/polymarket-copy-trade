# Source: https://docs.polymarket.com/developers/market-makers/inventory

On this page

* [Overview](#overview)
* [Splitting USDCe into Tokens](#splitting-usdce-into-tokens)
* [Via Relayer Client (Recommended)](#via-relayer-client-recommended)
* [Result](#result)
* [Merging Tokens to USDCe](#merging-tokens-to-usdce)
* [Via Relayer Client](#via-relayer-client)
* [Result](#result-2)
* [Redeeming After Resolution](#redeeming-after-resolution)
* [Check Resolution Status](#check-resolution-status)
* [Redeem Winning Tokens](#redeem-winning-tokens)
* [Payout](#payout)
* [Negative Risk Markets](#negative-risk-markets)
* [Inventory Strategies](#inventory-strategies)
* [Pre-market Preparation](#pre-market-preparation)
* [During Trading](#during-trading)
* [Post-Resolution](#post-resolution)
* [Batch Operations](#batch-operations)
* [Related Documentation](#related-documentation)

## [​](#overview) Overview

Market makers need to manage their inventory of outcome tokens. This involves:

1. **Splitting** USDCe into YES/NO tokens to have inventory to quote
2. **Merging** tokens back to USDCe to reduce exposure
3. **Redeeming** winning tokens after market resolution

All these operations use the Conditional Token Framework (CTF) contract, typically via the Relayer Client for gasless execution.

These examples assume you have initialized a RelayClient. See [Setup](/developers/market-makers/setup) for client initialization.

## [​](#splitting-usdce-into-tokens) Splitting USDCe into Tokens

Split 1 USDCe into 1 YES + 1 NO token. This creates inventory for quoting both sides.

### [​](#via-relayer-client-recommended) Via Relayer Client (Recommended)

Copy

Ask AI

```
import { ethers } from "ethers";
import { Interface } from "ethers/lib/utils";
import { RelayClient, Transaction } from "@polymarket/builder-relayer-client";

const CTF_ADDRESS = "0x4d97dcd97ec945f40cf65f87097ace5ea0476045";
const USDCe_ADDRESS = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174";

const ctfInterface = new Interface([
  "function splitPosition(address collateralToken, bytes32 parentCollectionId, bytes32 conditionId, uint[] partition, uint amount)"
]);

// Split $1000 USDCe into YES/NO tokens
const amount = ethers.utils.parseUnits("1000", 6); // USDCe has 6 decimals

const splitTx: Transaction = {
  to: CTF_ADDRESS,
  data: ctfInterface.encodeFunctionData("splitPosition", [
    USDCe_ADDRESS,                                    // collateralToken
    ethers.constants.HashZero,                       // parentCollectionId (null for Polymarket)
    conditionId,                                     // conditionId from market
    [1, 2],                                          // partition: [YES, NO]
    amount
  ]),
  value: "0"
};

const response = await client.execute([splitTx], "Split USDCe into tokens");
const result = await response.wait();
console.log("Split completed:", result?.transactionHash);
```

### [​](#result) Result

After splitting 1000 USDCe:

* Receive 1000 YES tokens
* Receive 1000 NO tokens
* USDCe balance decreases by 1000

## [​](#merging-tokens-to-usdce) Merging Tokens to USDCe

Merge equal amounts of YES + NO tokens back into USDCe. Useful for:

* Reducing inventory
* Exiting a market
* Converting profits to USDCe

### [​](#via-relayer-client) Via Relayer Client

Copy

Ask AI

```
const ctfInterface = new Interface([
  "function mergePositions(address collateralToken, bytes32 parentCollectionId, bytes32 conditionId, uint[] partition, uint amount)"
]);

// Merge 500 YES + 500 NO back to 500 USDCe
const amount = ethers.utils.parseUnits("500", 6);

const mergeTx: Transaction = {
  to: CTF_ADDRESS,
  data: ctfInterface.encodeFunctionData("mergePositions", [
    USDCe_ADDRESS,
    ethers.constants.HashZero,
    conditionId,
    [1, 2],
    amount
  ]),
  value: "0"
};

const response = await client.execute([mergeTx], "Merge tokens to USDCe");
await response.wait();
```

### [​](#result-2) Result

After merging 500 of each:

* YES tokens decrease by 500
* NO tokens decrease by 500
* USDCe balance increases by 500

## [​](#redeeming-after-resolution) Redeeming After Resolution

After a market resolves, redeem winning tokens for USDCe.

### [​](#check-resolution-status) Check Resolution Status

Copy

Ask AI

```
// Via CLOB API
const market = await clobClient.getMarket(conditionId);
if (market.closed) {
  // Market is resolved
  const winningToken = market.tokens.find(t => t.winner);
  console.log("Winning outcome:", winningToken?.outcome);
}
```

### [​](#redeem-winning-tokens) Redeem Winning Tokens

Copy

Ask AI

```
const ctfInterface = new Interface([
  "function redeemPositions(address collateralToken, bytes32 parentCollectionId, bytes32 conditionId, uint[] indexSets)"
]);

const redeemTx: Transaction = {
  to: CTF_ADDRESS,
  data: ctfInterface.encodeFunctionData("redeemPositions", [
    USDCe_ADDRESS,
    ethers.constants.HashZero,
    conditionId,
    [1, 2]  // Redeem both YES and NO (only winners pay out)
  ]),
  value: "0"
};

const response = await client.execute([redeemTx], "Redeem winning tokens");
await response.wait();
```

### [​](#payout) Payout

* If YES wins: Each YES token redeems for $1 USDCe
* If NO wins: Each NO token redeems for $1 USDCe
* Losing tokens are worthless (redeem for $0)

## [​](#negative-risk-markets) Negative Risk Markets

Multi-outcome markets use the Negative Risk CTF Exchange. The split/merge process is similar but uses different contract addresses.

Copy

Ask AI

```
const NEG_RISK_ADAPTER = "0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296";
const NEG_RISK_CTF_EXCHANGE = "0xC5d563A36AE78145C45a50134d48A1215220f80a";
```

See [Negative Risk Overview](/developers/neg-risk/overview) for details.

## [​](#inventory-strategies) Inventory Strategies

### [​](#pre-market-preparation) Pre-market Preparation

Before quoting a market:

1. Check market metadata via Gamma API
2. Split sufficient USDCe to cover expected quoting size
3. Set token approvals if not already done

### [​](#during-trading) During Trading

Monitor inventory and adjust:

* Skew quotes when inventory is imbalanced
* Merge excess tokens to free up capital
* Split more when inventory runs low

### [​](#post-resolution) Post-Resolution

After market closes:

1. Cancel all open orders
2. Wait for resolution
3. Redeem winning tokens
4. Merge any remaining pairs

## [​](#batch-operations) Batch Operations

For efficiency, batch multiple operations:

Copy

Ask AI

```
const transactions: Transaction[] = [
  // Split on Market A
  {
    to: CTF_ADDRESS,
    data: ctfInterface.encodeFunctionData("splitPosition", [
      USDCe_ADDRESS,
      ethers.constants.HashZero,
      conditionIdA,
      [1, 2],
      ethers.utils.parseUnits("1000", 6)
    ]),
    value: "0"
  },
  // Split on Market B
  {
    to: CTF_ADDRESS,
    data: ctfInterface.encodeFunctionData("splitPosition", [
      USDCe_ADDRESS,
      ethers.constants.HashZero,
      conditionIdB,
      [1, 2],
      ethers.utils.parseUnits("1000", 6)
    ]),
    value: "0"
  }
];

const response = await client.execute(transactions, "Batch inventory setup");
await response.wait();
```

## [​](#related-documentation) Related Documentation

[## CTF Overview

Conditional Token Framework basics](/developers/CTF/overview)[## Split Positions

Detailed split documentation](/developers/CTF/split)[## Merge Positions

Detailed merge documentation](/developers/CTF/merge)[## Relayer Client

Gasless transaction execution](/developers/builders/relayer-client)

[Data Feeds](/developers/market-makers/data-feeds)[Builder Program Introduction](/developers/builders/builder-intro)

⌘I