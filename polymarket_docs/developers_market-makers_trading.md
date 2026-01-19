# Source: https://docs.polymarket.com/developers/market-makers/trading

On this page

* [Overview](#overview)
* [Order Entry](#order-entry)
* [Posting Limit Orders](#posting-limit-orders)
* [Batch Orders](#batch-orders)
* [Order Types](#order-types)
* [When to Use Each](#when-to-use-each)
* [Order Management](#order-management)
* [Cancel Orders](#cancel-orders)
* [Get Active Orders](#get-active-orders)
* [Best Practices](#best-practices)
* [Quote Management](#quote-management)
* [Latency Optimization](#latency-optimization)
* [Risk Management](#risk-management)
* [Tick Sizes](#tick-sizes)
* [Fee Structure](#fee-structure)
* [Related Documentation](#related-documentation)

## [​](#overview) Overview

Market makers primarily interact with Polymarket through the CLOB (Central Limit Order Book) API to post and manage limit orders.

## [​](#order-entry) Order Entry

### [​](#posting-limit-orders) Posting Limit Orders

Use the CLOB client to create and post limit orders:

Copy

Ask AI

```
import { ClobClient, Side, OrderType } from "@polymarket/clob-client";

const client = new ClobClient(
  "https://clob.polymarket.com",
  137,
  wallet,
  credentials,
  signatureType,
  funder
);

// Post a bid (buy order)
const bidOrder = await client.createAndPostOrder({
  tokenID: "34097058504275310827233323421517291090691602969494795225921954353603704046623",
  side: Side.BUY,
  price: 0.48,
  size: 1000,
  orderType: OrderType.GTC
});

// Post an ask (sell order)
const askOrder = await client.createAndPostOrder({
  tokenID: "34097058504275310827233323421517291090691602969494795225921954353603704046623",
  side: Side.SELL,
  price: 0.52,
  size: 1000,
  orderType: OrderType.GTC
});
```

See [Create Order](/developers/CLOB/clients/methods-l1#createandpostorder) for full documentation.

### [​](#batch-orders) Batch Orders

For efficiency, post multiple orders in a single request:

Copy

Ask AI

```
const orders = await Promise.all([
  client.createOrder({ tokenID, side: Side.BUY, price: 0.48, size: 500 }),
  client.createOrder({ tokenID, side: Side.BUY, price: 0.47, size: 500 }),
  client.createOrder({ tokenID, side: Side.SELL, price: 0.52, size: 500 }),
  client.createOrder({ tokenID, side: Side.SELL, price: 0.53, size: 500 })
]);

const response = await client.postOrders(
  orders.map(order => ({ order, orderType: OrderType.GTC }))
);
```

See [Post Orders Batch](/developers/CLOB/clients/methods-l2#postorders) for details.

## [​](#order-types) Order Types

| Type | Behavior | MM Use Case |
| --- | --- | --- |
| **GTC** (Good Till Cancelled) | Rests on book until filled or cancelled | Default for passive quoting |
| **GTD** (Good Till Date) | Auto-expires at specified time | Auto-expire before events |
| **FOK** (Fill or Kill) | Fill entirely immediately or cancel | Aggressive rebalancing (all or nothing) |
| **FAK** (Fill and Kill) | Fill available immediately, cancel rest | Partial rebalancing acceptable |

### [​](#when-to-use-each) When to Use Each

**For passive market making (maker orders):**

* **GTC** - Standard quotes that sit on the book
* **GTD** - Time-limited quotes (e.g., expire before market close)

**For rebalancing (taker orders):**

* **FOK** - When you need exact size or nothing
* **FAK** - When partial fills are acceptable

Copy

Ask AI

```
// GTD example: expire in 1 hour
const expiringOrder = await client.createOrder({
  tokenID,
  side: Side.BUY,
  price: 0.50,
  size: 1000,
  orderType: OrderType.GTD,
  expiration: Math.floor(Date.now() / 1000) + 3600 // 1 hour from now
});
```

## [​](#order-management) Order Management

### [​](#cancel-orders) Cancel Orders

Cancel individual orders or all orders:

Copy

Ask AI

```
// Cancel single order
await client.cancelOrder(orderId);

// Cancel multiple orders in a single calls
await client.cancelOrders(orderIds: string[]);

// Cancel all orders for a market
await client.cancelMarketOrders(conditionId);

// Cancel all orders
await client.cancelAll();
```

See [Cancel Orders](/developers/CLOB/clients/methods-l2#cancelorder) for full documentation.

### [​](#get-active-orders) Get Active Orders

Monitor your open orders:

Copy

Ask AI

```
// Get active order
const order = await client.getOrder(orderId);

// Get active orders optionally filtered
const orders = await client.getOpenOrders({
  id?: string; // Order ID (hash)
  market?: string; // Market condition ID
  asset_id?: string; // Token ID
});
```

See [Get Active Orders](/developers/CLOB/clients/methods-l2#getorder) for details.

## [​](#best-practices) Best Practices

### [​](#quote-management) Quote Management

1. **Two-sided quoting** - Post both bids and asks to earn maximum [liquidity rewards](/developers/market-makers/liquidity-rewards)
2. **Monitor inventory** - Skew quotes based on your position
3. **Cancel stale quotes** - Remove orders when market conditions change
4. **Use GTD for events** - Auto-expire quotes before known events

### [​](#latency-optimization) Latency Optimization

1. **Batch orders** - Use `postOrders()` instead of multiple `createAndPostOrder()` calls
2. **WebSocket for data** - Use WebSocket feeds instead of polling REST endpoints

### [​](#risk-management) Risk Management

1. **Size limits** - Check token balances before quoting; don’t exceed inventory
2. **Price guards** - Validate against book midpoint; reject outlier prices
3. **Kill switch** - Use `cancelAll()` on error or position breach
4. **Monitor fills** - Subscribe to WebSocket user channel for real-time fill updates

## [​](#tick-sizes) Tick Sizes

Markets have different minimum price increments:

Copy

Ask AI

```
const tickSize = await client.getTickSize(tokenID);
// Returns: "0.1" | "0.01" | "0.001" | "0.0001"
```

Ensure your prices conform to the market’s tick size.

## [​](#fee-structure) Fee Structure

| Role | Fee |
| --- | --- |
| Maker | 0 bps |
| Taker | 0 bps |

Current fees are 0% for both makers and takers. See [CLOB Introduction](/developers/CLOB/introduction) for fee calculation details.

## [​](#related-documentation) Related Documentation

[## CLOB Client Overview

Complete client method reference](/developers/CLOB/clients/methods-overview)[## L2 Methods

Authenticated order management methods](/developers/CLOB/clients/methods-l2)[## WebSocket Feeds

Real-time order and market data](/developers/CLOB/websocket/wss-overview)[## Liquidity Rewards

Earn rewards for providing liquidity](/developers/market-makers/liquidity-rewards)

[Setup](/developers/market-makers/setup)[Liquidity Rewards](/developers/market-makers/liquidity-rewards)

⌘I