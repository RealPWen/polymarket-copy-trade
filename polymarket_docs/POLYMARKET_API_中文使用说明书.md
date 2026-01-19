# Polymarket API 中文使用说明书

> 本文档基于 Polymarket 官方文档编写，涵盖所有核心 API 功能的中文说明。

---

## 目录

1. [概述](#1-概述)
2. [API 体系架构](#2-api-体系架构)
3. [快速开始](#3-快速开始)
4. [认证机制](#4-认证机制)
5. [CLOB API（订单簿）](#5-clob-api订单簿)
6. [Gamma API（市场数据）](#6-gamma-api市场数据)
7. [Data API（用户数据）](#7-data-api用户数据)
8. [Subgraph（链上数据）](#8-subgraph链上数据)
9. [WebSocket 实时数据](#9-websocket-实时数据)
10. [常见问题与故障排除](#10-常见问题与故障排除)

---

## 1. 概述

### 1.1 什么是 Polymarket？

Polymarket 是一个基于 Polygon 区块链的去中心化预测市场平台，用户可以在各种事件上进行交易，如政治选举、体育赛事、加密货币价格等。

### 1.2 核心概念

| 术语 | 说明 |
|------|------|
| **Market（市场）** | 一个可交易的预测问题，如 "Will X happen?" |
| **Condition ID** | 市场的唯一标识符（64位十六进制字符串，0x前缀） |
| **Token ID** | 结果代币的唯一标识符，每个市场有多个结果代币 |
| **Outcome Token（结果代币）** | 代表某个结果的 ERC1155 代币，如 YES/NO |
| **USDC** | 抵押资产，用于购买结果代币 |
| **Price（价格）** | 代币价格，范围 0-1，代表市场预期概率 |

### 1.3 费用结构

| 交易量级别 | Maker 费率 (bps) | Taker 费率 (bps) |
|-----------|-----------------|-----------------|
| > 0 USDC | 0 | 0 |

> 注意：费用结构可能会更新，请关注官方公告。

---

## 2. API 体系架构

Polymarket 提供多个 API 服务，各有不同用途：

```
┌─────────────────────────────────────────────────────────────────┐
│                      Polymarket API 体系                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐│
│  │   CLOB API    │  │  Gamma API    │  │      Data API         ││
│  │ (订单簿交易)   │  │  (市场元数据)  │  │ (用户持仓/交易历史)    ││
│  │               │  │               │  │                       ││
│  │ clob.poly     │  │ gamma-api.    │  │ data-api.             ││
│  │ market.com    │  │ polymarket.com│  │ polymarket.com        ││
│  └───────────────┘  └───────────────┘  └───────────────────────┘│
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Subgraph (GraphQL)                      │  │
│  │              链上数据查询（订单、持仓、PNL）                │  │
│  │                   api.goldsky.com                          │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    WebSocket (实时数据)                     │  │
│  │           wss://ws-subscriptions-clob.polymarket.com       │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### API 端点汇总

| API | 基础 URL | 用途 |
|-----|---------|------|
| **CLOB API** | `https://clob.polymarket.com` | 订单管理、交易执行 |
| **Gamma API** | `https://gamma-api.polymarket.com` | 市场元数据、分类信息 |
| **Data API** | `https://data-api.polymarket.com` | 用户持仓、交易历史 |
| **WebSocket** | `wss://ws-subscriptions-clob.polymarket.com` | 实时市场更新 |

---

## 3. 快速开始

### 3.1 安装客户端

**TypeScript:**
```bash
npm install @polymarket/clob-client ethers
```

**Python:**
```bash
pip install py-clob-client
```

### 3.2 初始化客户端

**TypeScript:**
```typescript
import { ClobClient } from "@polymarket/clob-client";
import { Wallet } from "ethers"; // v5.8.0

const HOST = "https://clob.polymarket.com";
const CHAIN_ID = 137; // Polygon 主网
const signer = new Wallet(process.env.PRIVATE_KEY);

// 创建或获取 API 凭证
const tempClient = new ClobClient(HOST, CHAIN_ID, signer);
const apiCreds = await tempClient.createOrDeriveApiKey();

// 签名类型说明：
// 0 = EOA (标准以太坊钱包)
// 1 = POLY_PROXY (Magic Link 用户专用)
// 2 = GNOSIS_SAFE (推荐用于大多数场景)
const signatureType = 0;

// 初始化完整客户端
const client = new ClobClient(
  HOST, 
  CHAIN_ID, 
  signer, 
  apiCreds, 
  signatureType
);
```

**Python:**
```python
from py_clob_client.client import ClobClient
import os

host = "https://clob.polymarket.com"
chain_id = 137  # Polygon 主网
private_key = os.getenv("PRIVATE_KEY")

# 创建 L1 客户端获取 API 凭证
client = ClobClient(
    host=host,
    chain_id=chain_id,
    key=private_key
)

api_creds = client.create_or_derive_api_key()
# 返回: {"apiKey": "...", "secret": "...", "passphrase": "..."}
```

### 3.3 下单示例

**TypeScript:**
```typescript
import { Side } from "@polymarket/clob-client";

// 下限价单
const response = await client.createAndPostOrder({
  tokenID: "YOUR_TOKEN_ID",  // 从 Gamma API 获取
  price: 0.65,               // 每份价格
  size: 10,                  // 份数
  side: Side.BUY,            // BUY 或 SELL
});

console.log(`订单已提交! ID: ${response.orderID}`);
```

**Python:**
```python
# 下限价单
response = client.create_and_post_order({
    "token_id": "YOUR_TOKEN_ID",
    "price": 0.65,
    "size": 10,
    "side": "BUY"
})
```

### 3.4 查询订单

```typescript
// 查看所有未成交订单
const openOrders = await client.getOpenOrders();
console.log(`您有 ${openOrders.length} 个未成交订单`);

// 查看交易历史
const trades = await client.getTrades();
console.log(`您已完成 ${trades.length} 笔交易`);
```

---

## 4. 认证机制

Polymarket 使用两级认证系统：**L1（私钥签名）** 和 **L2（API 密钥）**。

### 4.1 L1 认证（私钥签名）

L1 认证使用钱包私钥签署 EIP-712 消息，用于：
- 创建/获取 API 凭证
- 本地签署订单

**HTTP 请求头:**

| 请求头 | 必需 | 说明 |
|--------|------|------|
| `POLY_ADDRESS` | ✅ | Polygon 签名者地址 |
| `POLY_SIGNATURE` | ✅ | EIP-712 签名 |
| `POLY_TIMESTAMP` | ✅ | 当前 UNIX 时间戳 |
| `POLY_NONCE` | ✅ | 随机数，默认 0 |

**EIP-712 签名结构:**
```typescript
const domain = {
  name: "ClobAuthDomain",
  version: "1",
  chainId: 137, // Polygon Chain ID
};

const types = {
  ClobAuth: [
    { name: "address", type: "address" },
    { name: "timestamp", type: "string" },
    { name: "nonce", type: "uint256" },
    { name: "message", type: "string" },
  ],
};

const value = {
  address: signingAddress,
  timestamp: ts,
  nonce: nonce,
  message: "This message attests that I control the given wallet",
};

const sig = await signer._signTypedData(domain, types, value);
```

### 4.2 L2 认证（API 密钥）

L2 认证使用从 L1 获取的 API 凭证，采用 HMAC-SHA256 签名，用于：
- 提交订单
- 取消订单
- 查询余额和授权

**HTTP 请求头:**

| 请求头 | 必需 | 说明 |
|--------|------|------|
| `POLY_ADDRESS` | ✅ | Polygon 签名者地址 |
| `POLY_SIGNATURE` | ✅ | HMAC-SHA256 签名 |
| `POLY_TIMESTAMP` | ✅ | 当前 UNIX 时间戳 |
| `POLY_API_KEY` | ✅ | API 密钥 |
| `POLY_PASSPHRASE` | ✅ | API 密码短语 |

### 4.3 签名类型与 Funder 地址

| 签名类型 | ID | 说明 |
|---------|----|----|
| **EOA** | 0 | 标准以太坊钱包 (MetaMask)，需要 POL 支付 Gas |
| **POLY_PROXY** | 1 | Magic Link 登录用户专用 |
| **GNOSIS_SAFE** | 2 | Gnosis Safe 多签代理钱包（最常用） |

> **Funder 地址**: 在 Polymarket.com 显示的钱包地址，是代理钱包地址，应用作 funder 参数。

---

## 5. CLOB API（订单簿）

CLOB (Central Limit Order Book) 是 Polymarket 的核心交易 API。

### 5.1 公共方法（无需认证）

#### 获取市场信息

```typescript
// 获取单个市场详情
const market = await client.getMarket(conditionId);

// 获取所有市场（分页）
const markets = await client.getMarkets();

// 获取简化市场数据（加载更快）
const simplifiedMarkets = await client.getSimplifiedMarkets();
```

**Market 响应结构:**
```typescript
interface Market {
  condition_id: string;        // 市场 ID
  question: string;            // 问题描述
  description: string;         // 详细描述
  active: boolean;             // 是否活跃
  closed: boolean;             // 是否已关闭
  neg_risk: boolean;           // 是否为负风险市场
  minimum_order_size: number;  // 最小订单大小
  minimum_tick_size: number;   // 最小价格精度
  tokens: MarketToken[];       // 结果代币列表
}

interface MarketToken {
  outcome: string;    // 结果名称 (如 "Yes", "No")
  price: number;      // 当前价格
  token_id: string;   // 代币 ID
  winner: boolean;    // 是否为获胜结果
}
```

#### 获取订单簿

```typescript
// 获取单个代币的订单簿
const orderBook = await client.getOrderBook(tokenId);

// 批量获取订单簿
const orderBooks = await client.getOrderBooks([
  { token_id: tokenId1, side: Side.BUY },
  { token_id: tokenId2, side: Side.SELL }
]);
```

**OrderBook 响应结构:**
```typescript
interface OrderBookSummary {
  market: string;           // 市场 ID
  asset_id: string;         // 代币 ID
  timestamp: string;        // 时间戳
  bids: OrderSummary[];     // 买单列表
  asks: OrderSummary[];     // 卖单列表
  min_order_size: string;   // 最小订单大小
  tick_size: string;        // 价格精度
  neg_risk: boolean;        // 是否负风险
}

interface OrderSummary {
  price: string;  // 价格
  size: string;   // 数量
}
```

#### 获取价格

```typescript
// 获取最佳买/卖价格
const price = await client.getPrice(tokenId, "BUY");

// 获取中间价（最佳买卖价的平均值）
const midpoint = await client.getMidpoint(tokenId);

// 获取买卖价差
const spread = await client.getSpread(tokenId);

// 获取历史价格
const priceHistory = await client.getPricesHistory({
  market: tokenId,
  interval: "1d",  // 可选: "max", "1w", "1d", "6h", "1h"
  startTs: 1704067200,
  endTs: 1706745600
});
```

#### 获取最近成交价

```typescript
// 获取单个代币最近成交价
const lastPrice = await client.getLastTradePrice(tokenId);

// 批量获取
const lastPrices = await client.getLastTradesPrices([tokenId1, tokenId2]);
```

### 5.2 L2 方法（需要认证）

#### 创建和提交订单

```typescript
// 一步完成创建和提交限价单
const response = await client.createAndPostOrder(
  {
    tokenID: "TOKEN_ID",
    price: 0.65,      // 价格 (0-1)
    size: 100,        // 数量
    side: Side.BUY,   // BUY 或 SELL
  },
  {
    tickSize: "0.01", // 价格精度
    negRisk: false    // 是否为负风险市场
  }
);

// 市价单
const marketOrder = await client.createAndPostMarketOrder(
  {
    tokenID: "TOKEN_ID",
    amount: 100,      // USDC 金额
    side: Side.BUY,
  },
  { tickSize: "0.01" }
);
```

**订单类型:**

| 类型 | 说明 |
|------|------|
| **GTC** | Good Till Cancelled - 直到取消前有效 |
| **GTD** | Good Till Date - 直到指定日期有效 |
| **FOK** | Fill or Kill - 全部成交或取消 |
| **FAK** | Fill and Kill - 部分成交后取消剩余 |

**OrderResponse 结构:**
```typescript
interface OrderResponse {
  success: boolean;
  errorMsg: string;
  orderID: string;
  transactionsHashes: string[];
  status: string;
  takingAmount: string;
  makingAmount: string;
}
```

#### 取消订单

```typescript
// 取消单个订单
await client.cancelOrder(orderId);

// 批量取消
await client.cancelOrders([orderId1, orderId2]);

// 取消所有订单
await client.cancelAll();

// 取消特定市场的所有订单
await client.cancelMarketOrders({ market: conditionId });
```

#### 查询订单和交易

```typescript
// 获取指定订单详情
const order = await client.getOrder(orderId);

// 获取所有未成交订单
const openOrders = await client.getOpenOrders();

// 按市场筛选
const marketOrders = await client.getOpenOrders({
  market: conditionId
});

// 获取交易历史
const trades = await client.getTrades();

// 分页获取交易
const tradesPaginated = await client.getTradesPaginated({
  before: "2024-01-01",
  after: "2023-01-01"
});
```

**OpenOrder 结构:**
```typescript
interface OpenOrder {
  id: string;
  status: string;
  owner: string;
  maker_address: string;
  market: string;
  asset_id: string;
  side: string;
  original_size: string;
  size_matched: string;
  price: string;
  outcome: string;
  created_at: number;
  expiration: string;
  order_type: string;
}
```

#### 余额和授权

```typescript
// 查询余额和授权
const balance = await client.getBalanceAllowance({
  asset_type: AssetType.COLLATERAL  // COLLATERAL(USDC) 或 CONDITIONAL(结果代币)
});

// 更新缓存的余额和授权
await client.updateBalanceAllowance({
  asset_type: AssetType.CONDITIONAL,
  token_id: tokenId
});
```

---

## 6. Gamma API（市场数据）

Gamma API 提供市场元数据，包括分类、描述、交易量等信息。

**基础 URL:** `https://gamma-api.polymarket.com`

### 6.1 获取市场列表

```bash
GET https://gamma-api.polymarket.com/markets
```

**查询参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `active` | boolean | 只返回活跃市场 |
| `closed` | boolean | 只返回已关闭市场 |
| `limit` | integer | 返回数量限制 |
| `offset` | integer | 分页偏移量 |

**响应示例:**
```json
[
  {
    "id": "123",
    "question": "Will Bitcoin reach $100k in 2024?",
    "conditionId": "0x...",
    "slug": "bitcoin-100k-2024",
    "category": "Crypto",
    "volume": "1500000",
    "liquidity": "500000",
    "outcomePrices": "[0.35, 0.65]",
    "outcomes": "[\"Yes\", \"No\"]",
    "clobTokenIds": "[\"tokenId1\", \"tokenId2\"]",
    "active": true,
    "closed": false,
    "volume24hr": 50000,
    "bestBid": 0.34,
    "bestAsk": 0.36
  }
]
```

### 6.2 获取单个市场

```bash
GET https://gamma-api.polymarket.com/markets/{id}
GET https://gamma-api.polymarket.com/markets?slug={slug}
```

### 6.3 获取事件

```bash
GET https://gamma-api.polymarket.com/events
GET https://gamma-api.polymarket.com/events/{id}
```

### 6.4 搜索

```bash
GET https://gamma-api.polymarket.com/search?query=bitcoin
```

---

## 7. Data API（用户数据）

Data API 提供用户相关的数据查询功能。

**基础 URL:** `https://data-api.polymarket.com`

### 7.1 获取用户持仓

```bash
GET https://data-api.polymarket.com/positions?user={address}
```

**查询参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `user` | string | 用户地址（必需） |
| `market` | string[] | 按市场 ID 筛选 |
| `sizeThreshold` | number | 最小持仓阈值 |
| `limit` | integer | 返回数量限制 (默认 100) |
| `offset` | integer | 分页偏移量 |
| `sortBy` | string | 排序字段 (TOKENS/CASHPNL/PERCENTPNL 等) |

**响应示例:**
```json
[
  {
    "proxyWallet": "0x...",
    "conditionId": "0x...",
    "asset": "tokenId",
    "size": 1000,
    "avgPrice": 0.55,
    "initialValue": 550,
    "currentValue": 650,
    "cashPnl": 100,
    "percentPnl": 18.18,
    "curPrice": 0.65,
    "outcome": "Yes",
    "title": "Market Question"
  }
]
```

### 7.2 获取交易历史

```bash
GET https://data-api.polymarket.com/trades?user={address}
```

**查询参数:**

| 参数 | 类型 | 说明 |
|------|------|------|
| `user` | string | 用户地址 |
| `market` | string[] | 按市场 ID 筛选 |
| `side` | string | BUY 或 SELL |
| `limit` | integer | 返回数量限制 (默认 100) |
| `offset` | integer | 分页偏移量 |
| `filterType` | string | CASH 或 TOKENS |
| `filterAmount` | number | 最小金额筛选 |

**响应示例:**
```json
[
  {
    "proxyWallet": "0x...",
    "conditionId": "0x...",
    "side": "BUY",
    "size": 100,
    "price": 0.55,
    "timestamp": 1704067200,
    "outcome": "Yes",
    "title": "Market Question",
    "transactionHash": "0x..."
  }
]
```

### 7.3 获取用户活动

```bash
GET https://data-api.polymarket.com/activity?user={address}
```

### 7.4 获取交易排行榜

```bash
GET https://data-api.polymarket.com/leaderboard
```

---

## 8. Subgraph（链上数据）

Polymarket 提供多个 Subgraph 用于查询链上数据，托管在 Goldsky 上。

### 8.1 可用 Subgraph

| Subgraph | URL | 用途 |
|----------|-----|------|
| **Orders** | `https://api.goldsky.com/.../orderbook-subgraph/0.0.1/gn` | 订单数据 |
| **Positions** | `https://api.goldsky.com/.../positions-subgraph/0.0.7/gn` | 持仓数据 |
| **Activity** | `https://api.goldsky.com/.../activity-subgraph/0.0.4/gn` | 交易活动 |
| **Open Interest** | `https://api.goldsky.com/.../oi-subgraph/0.0.6/gn` | 未平仓合约 |
| **PNL** | `https://api.goldsky.com/.../pnl-subgraph/0.0.14/gn` | 盈亏数据 |

### 8.2 查询示例

**获取用户所有持仓:**
```graphql
query GetUserPositions($address: String!) {
  userPositions(where: { user: $address }) {
    id
    conditionId
    collateralToken
    outcomeTokenAmounts
    position {
      id
      outcome
    }
  }
}
```

**获取市场交易历史:**
```graphql
query GetMarketTrades($conditionId: String!) {
  trades(
    where: { conditionId: $conditionId }
    orderBy: timestamp
    orderDirection: desc
    first: 100
  ) {
    id
    user
    side
    size
    price
    timestamp
    transactionHash
  }
}
```

---

## 9. WebSocket 实时数据

WebSocket 提供市场和用户的实时更新推送。

**WebSocket URL:** `wss://ws-subscriptions-clob.polymarket.com`

### 9.1 频道类型

| 频道 | 说明 |
|------|------|
| **market** | 市场价格、订单簿更新 |
| **user** | 用户订单、交易更新 |

### 9.2 订阅消息格式

```json
{
  "auth": {
    "apiKey": "your-api-key",
    "secret": "your-secret",
    "passphrase": "your-passphrase"
  },
  "type": "MARKET",
  "assets_ids": ["tokenId1", "tokenId2"],
  "custom_feature_enabled": true
}
```

### 9.3 动态订阅/取消订阅

```json
{
  "operation": "subscribe",
  "assets_ids": ["tokenId3", "tokenId4"]
}
```

```json
{
  "operation": "unsubscribe",
  "assets_ids": ["tokenId1"]
}
```

### 9.4 市场频道事件

| 事件类型 | 说明 |
|---------|------|
| `price_change` | 价格变动 |
| `book_change` | 订单簿变动 |
| `last_trade_price` | 最新成交价 |
| `new_market` | 新市场上线 |

### 9.5 Python 示例

```python
import asyncio
import websockets
import json

async def subscribe_market():
    uri = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
    
    async with websockets.connect(uri) as websocket:
        # 订阅消息
        subscribe_msg = {
            "assets_ids": ["tokenId1", "tokenId2"],
            "type": "MARKET"
        }
        await websocket.send(json.dumps(subscribe_msg))
        
        # 接收消息
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"收到更新: {data}")

asyncio.run(subscribe_market())
```

---

## 10. 常见问题与故障排除

### 10.1 认证错误

#### `L2_AUTH_NOT_AVAILABLE`
**原因:** 未调用 `createOrDeriveApiKey()` 获取 API 凭证。

**解决方案:**
```typescript
const creds = await clobClient.createOrDeriveApiKey();
const client = new ClobClient(host, chainId, wallet, creds);
```

#### `INVALID_SIGNATURE`
**原因:** 私钥不正确或格式错误。

**解决方案:**
- 验证私钥是有效的十六进制字符串（以 "0x" 开头）
- 确认使用的是正确地址对应的私钥

#### `NONCE_ALREADY_USED`
**原因:** 提供的 nonce 已被使用。

**解决方案:**
```typescript
// 使用相同 nonce 恢复凭证
const recovered = await client.deriveApiKey(originalNonce);
// 或使用新 nonce 创建新凭证
const newCreds = await client.createApiKey();
```

### 10.2 订单错误

#### `insufficient balance`
**原因:** 余额不足。

**解决方案:**
- BUY 订单: 确保有足够的 USDC
- SELL 订单: 确保有足够的结果代币
- 在 [polymarket.com/portfolio](https://polymarket.com/portfolio) 检查余额

#### `insufficient allowance`
**原因:** 未授权 Exchange 合约使用代币。

**解决方案:**
- 通过 Polymarket UI 完成首次交易授权
- 或调用 CTF 合约的 `setApprovalForAll()` 方法

#### `Invalid Funder Address`
**原因:** Funder 地址不正确或不存在。

**解决方案:**
- 在 [polymarket.com/settings](https://polymarket.com/settings) 查看你的钱包地址
- 如果从未登录过 Polymarket，需要先部署代理钱包

### 10.3 Funder 地址说明

**什么是 Funder 地址?**
- Funder 地址是你在 Polymarket 上存入资金的代理钱包
- 可以在 [polymarket.com/settings](https://polymarket.com/settings) 找到
- 显示为 "Wallet Address" 或 "Profile Address"

### 10.4 地理限制

Polymarket 对某些地区有访问限制。如果遇到地理限制错误：
- 确认你所在地区是否被支持
- 检查 VPN 设置

---

## 附录

### A. 官方资源链接

| 资源 | 链接 |
|------|------|
| 官方文档 | https://docs.polymarket.com |
| TypeScript 客户端 | https://github.com/Polymarket/clob-client |
| Python 客户端 | https://github.com/Polymarket/py-clob-client |
| Subgraph 源码 | https://github.com/Polymarket/polymarket-subgraph |
| Exchange 合约 | https://github.com/Polymarket/ctf-exchange |
| 安全审计报告 | [ChainSecurity Audit](https://github.com/Polymarket/ctf-exchange/blob/main/audit/ChainSecurity_Polymarket_Exchange_audit.pdf) |

### B. 环境变量配置示例

```env
# .env 文件示例
PRIVATE_KEY=0x...              # 钱包私钥
FUNDER_ADDRESS=0x...           # Polymarket 代理钱包地址
API_KEY=...                    # API 密钥
SECRET=...                     # API 密钥密文
PASSPHRASE=...                 # API 密钥口令
```

### C. 完整交易流程示例

```typescript
import { ClobClient, Side } from "@polymarket/clob-client";
import { Wallet } from "ethers";

async function trade() {
  // 1. 初始化
  const HOST = "https://clob.polymarket.com";
  const CHAIN_ID = 137;
  const signer = new Wallet(process.env.PRIVATE_KEY);
  
  // 2. 获取 API 凭证
  const tempClient = new ClobClient(HOST, CHAIN_ID, signer);
  const apiCreds = await tempClient.createOrDeriveApiKey();
  
  // 3. 创建完整客户端
  const client = new ClobClient(
    HOST,
    CHAIN_ID,
    signer,
    apiCreds,
    2,  // GNOSIS_SAFE
    process.env.FUNDER_ADDRESS
  );
  
  // 4. 获取市场信息
  const markets = await client.getMarkets();
  const market = markets.data[0];
  const tokenId = market.tokens[0].token_id;
  
  // 5. 查看订单簿
  const orderBook = await client.getOrderBook(tokenId);
  console.log("订单簿:", orderBook);
  
  // 6. 下单
  const order = await client.createAndPostOrder({
    tokenID: tokenId,
    price: 0.50,
    size: 10,
    side: Side.BUY
  });
  console.log("订单提交成功:", order);
  
  // 7. 查看未成交订单
  const openOrders = await client.getOpenOrders();
  console.log("未成交订单:", openOrders);
  
  // 8. 取消订单（如需要）
  if (openOrders.length > 0) {
    await client.cancelOrder(openOrders[0].id);
    console.log("订单已取消");
  }
}

trade().catch(console.error);
```

---

> **文档版本:** 1.0  
> **更新日期:** 2026-01-16  
> **基于:** Polymarket 官方文档
