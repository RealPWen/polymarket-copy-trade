# Source: https://docs.polymarket.com/developers/CLOB/clients/methods-l2

On this page

* [Client Initialization](#client-initialization)
* [Order Creation and Management](#order-creation-and-management)
* [createAndPostOrder()](#createandpostorder)
* [createAndPostMarketOrder()](#createandpostmarketorder)
* [postOrder()](#postorder)
* [postOrders()](#postorders)
* [cancelOrder()](#cancelorder)
* [cancelOrders()](#cancelorders)
* [cancelAll()](#cancelall)
* [cancelMarketOrders()](#cancelmarketorders)
* [Order and Trade Queries](#order-and-trade-queries)
* [getOrder()](#getorder)
* [getOpenOrders()](#getopenorders)
* [getTrades()](#gettrades)
* [getTradesPaginated()](#gettradespaginated)
* [Balance and Allowances](#balance-and-allowances)
* [getBalanceAllowance()](#getbalanceallowance)
* [updateBalanceAllowance()](#updatebalanceallowance)
* [API Key Management (L2)](#api-key-management-l2)
* [getApiKeys()](#getapikeys)
* [deleteApiKey()](#deleteapikey)
* [Notifications](#notifications)
* [getNotifications()](#getnotifications)
* [dropNotifications()](#dropnotifications)
* [See Also](#see-also)

---

## [​](#client-initialization) Client Initialization

L2 methods require the client to initialize with the signer, signatureType, user API credentials, and funder.

* TypeScript
* Python

Copy

Ask AI

```
import { ClobClient } from "@polymarket/clob-client";
import { Wallet } from "ethers";

const signer = new Wallet(process.env.PRIVATE_KEY)

const apiCreds = {
  apiKey: process.env.API_KEY,
  secret: process.env.SECRET,
  passphrase: process.env.PASSPHRASE,
};

const client = new ClobClient(
  "https://clob.polymarket.com",
  137,
  signer,
  apiCreds,
  2, // Deployed Safe proxy wallet
  process.env.FUNDER_ADDRESS // Address of deployed Safe proxy wallet
);

// Ready to send authenticated requests to the CLOB API!
const order = await client.postOrder(signedOrder);
```

Copy

Ask AI

```
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import ApiCreds
import os

api_creds = ApiCreds(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("SECRET"),
    api_passphrase=os.getenv("PASSPHRASE")
)

client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137,
    key=os.getenv("PRIVATE_KEY"),
    creds=api_creds,
    signature_type=2, # Deployed Safe proxy wallet
    funder=os.getenv("FUNDER_ADDRESS") # Address of deployed Safe proxy wallet
)

# Ready to send authenticated requests to the CLOB API!
order = await client.post_order(signed_order)
```

---

## [​](#order-creation-and-management) Order Creation and Management

---

### [​](#createandpostorder) createAndPostOrder()

A convenience method that creates, prompts signature, and posts an order in a single call.
Use when you want to buy/sell at a specific price and can wait.

Signature

Copy

Ask AI

```
async createAndPostOrder(
  userOrder: UserOrder,
  options?: Partial<CreateOrderOptions>,
  orderType?: OrderType.GTC | OrderType.GTD, // Defaults to GTC
): Promise<OrderResponse>
```

Params

Copy

Ask AI

```
interface UserOrder {
  tokenID: string;
  price: number;
  size: number;
  side: Side;
  feeRateBps?: number;
  nonce?: number;
  expiration?: number;
  taker?: string;
}

type CreateOrderOptions = {
  tickSize: TickSize;
  negRisk?: boolean;
}

type TickSize = "0.1" | "0.01" | "0.001" | "0.0001";
```

Response

Copy

Ask AI

```
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

---

### [​](#createandpostmarketorder) createAndPostMarketOrder()

A convenience method that creates, prompts signature, and posts an order in a single call.
Use when you want to buy/sell right now at whatever the market price is.

Signature

Copy

Ask AI

```
async createAndPostMarketOrder(
  userMarketOrder: UserMarketOrder,
  options?: Partial<CreateOrderOptions>,
  orderType?: OrderType.FOK | OrderType.FAK, // Defaults to FOK
): Promise<OrderResponse>
```

Params

Copy

Ask AI

```
interface UserMarketOrder {
  tokenID: string;
  amount: number;
  side: Side;
  price?: number;
  feeRateBps?: number;
  nonce?: number;
  taker?: string;
  orderType?: OrderType.FOK | OrderType.FAK;
}

type CreateOrderOptions = {
  tickSize: TickSize;
  negRisk?: boolean;
}

type TickSize = "0.1" | "0.01" | "0.001" | "0.0001";
```

Response

Copy

Ask AI

```
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

---

### [​](#postorder) postOrder()

Posts a pre-signed and created order to the CLOB.

Signature

Copy

Ask AI

```
async postOrder(
  order: SignedOrder,
  orderType?: OrderType, // Defaults to GTC
  postOnly?: boolean, // Defaults to false
): Promise<OrderResponse>
```

Params

Copy

Ask AI

```
order: SignedOrder  // Pre-signed order from createOrder() or createMarketOrder()
orderType?: OrderType  // Optional, defaults to GTC
postOnly?: boolean  // Optional, defaults to false
```

Response

Copy

Ask AI

```
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

---

### [​](#postorders) postOrders()

Posts up to 15 pre-signed and created orders in a single batch.

Copy

Ask AI

```
async postOrders(
  args: PostOrdersArgs[],
): Promise<OrderResponse[]>
```

Params

Copy

Ask AI

```
interface PostOrdersArgs {
  order: SignedOrder;
  orderType: OrderType;
  postOnly?: boolean; // Defaults to false
}
```

Response

Copy

Ask AI

```
OrderResponse[]  // Array of OrderResponse objects

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

---

### [​](#cancelorder) cancelOrder()

Cancels a single open order.

Signature

Copy

Ask AI

```
async cancelOrder(orderID: string): Promise<CancelOrdersResponse>
```

Response

Copy

Ask AI

```
interface CancelOrdersResponse {
  canceled: string[];
  not_canceled: Record<string, any>;
}
```

---

### [​](#cancelorders) cancelOrders()

Cancels multiple orders in a single batch.

Signature

Copy

Ask AI

```
async cancelOrders(orderIDs: string[]): Promise<CancelOrdersResponse>
```

Params

Copy

Ask AI

```
orderIDs: string[];
```

Response

Copy

Ask AI

```
interface CancelOrdersResponse {
  canceled: string[];
  not_canceled: Record<string, any>;
}
```

---

### [​](#cancelall) cancelAll()

Cancels all open orders.

Signature

Copy

Ask AI

```
async cancelAll(): Promise<CancelResponse>
```

Response

Copy

Ask AI

```
interface CancelOrdersResponse {
  canceled: string[];
  not_canceled: Record<string, any>;
}
```

---

### [​](#cancelmarketorders) cancelMarketOrders()

Cancels all open orders for a specific market.

Signature

Copy

Ask AI

```
async cancelMarketOrders(
  payload: OrderMarketCancelParams
): Promise<CancelOrdersResponse>
```

Parameters

Copy

Ask AI

```
interface OrderMarketCancelParams {
  market?: string;
  asset_id?: string;
}
```

Response

Copy

Ask AI

```
interface CancelOrdersResponse {
  canceled: string[];
  not_canceled: Record<string, any>;
}
```

---

## [​](#order-and-trade-queries) Order and Trade Queries

---

### [​](#getorder) getOrder()

Get details for a specific order.

Signature

Copy

Ask AI

```
async getOrder(orderID: string): Promise<OpenOrder>
```

Response

Copy

Ask AI

```
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
  associate_trades: string[];
  outcome: string;
  created_at: number;
  expiration: string;
  order_type: string;
}
```

---

### [​](#getopenorders) getOpenOrders()

Get all your open orders.

Signature

Copy

Ask AI

```
async getOpenOrders(
  params?: OpenOrderParams,
  only_first_page?: boolean,
): Promise<OpenOrdersResponse>
```

Params

Copy

Ask AI

```
interface OpenOrderParams {
  id?: string; // Order ID
  market?: string; // Market condition ID
  asset_id?: string; // Token ID
}

only_first_page?: boolean  // Defaults to false
```

Response

Copy

Ask AI

```
type OpenOrdersResponse = OpenOrder[];

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
  associate_trades: string[];
  outcome: string;
  created_at: number;
  expiration: string;
  order_type: string;
}
```

---

### [​](#gettrades) getTrades()

Get your trade history (filled orders).

Signature

Copy

Ask AI

```
async getTrades(
  params?: TradeParams,
  only_first_page?: boolean,
): Promise<Trade[]>
```

Params

Copy

Ask AI

```
interface TradeParams {
  id?: string;
  maker_address?: string;
  market?: string;
  asset_id?: string;
  before?: string;
  after?: string;
}

only_first_page?: boolean  // Defaults to false
```

Response

Copy

Ask AI

```
interface Trade {
  id: string;
  taker_order_id: string;
  market: string;
  asset_id: string;
  side: Side;
  size: string;
  fee_rate_bps: string;
  price: string;
  status: string;
  match_time: string;
  last_update: string;
  outcome: string;
  bucket_index: number;
  owner: string;
  maker_address: string;
  maker_orders: MakerOrder[];
  transaction_hash: string;
  trader_side: "TAKER" | "MAKER";
}

interface MakerOrder {
  order_id: string;
  owner: string;
  maker_address: string;
  matched_amount: string;
  price: string;
  fee_rate_bps: string;
  asset_id: string;
  outcome: string;
  side: Side;
}
```

---

### [​](#gettradespaginated) getTradesPaginated()

Get trade history with pagination for large result sets.

Signature

Copy

Ask AI

```
async getTradesPaginated(
  params?: TradeParams,
): Promise<TradesPaginatedResponse>
```

Params

Copy

Ask AI

```
interface TradeParams {
  id?: string;
  maker_address?: string;
  market?: string;
  asset_id?: string;
  before?: string;
  after?: string;
}
```

Response

Copy

Ask AI

```
interface TradesPaginatedResponse {
  trades: Trade[];
  limit: number;
  count: number;
}
```

---

## [​](#balance-and-allowances) Balance and Allowances

---

### [​](#getbalanceallowance) getBalanceAllowance()

Get your balance and allowance for specific tokens.

Signature

Copy

Ask AI

```
async getBalanceAllowance(
  params?: BalanceAllowanceParams
): Promise<BalanceAllowanceResponse>
```

Params

Copy

Ask AI

```
interface BalanceAllowanceParams {
  asset_type: AssetType;
  token_id?: string;
}

enum AssetType {
  COLLATERAL = "COLLATERAL",
  CONDITIONAL = "CONDITIONAL",
}
```

Response

Copy

Ask AI

```
interface BalanceAllowanceResponse {
  balance: string;
  allowance: string;
}
```

---

### [​](#updatebalanceallowance) updateBalanceAllowance()

Updates the cached balance and allowance for specific tokens.

Signature

Copy

Ask AI

```
async updateBalanceAllowance(
  params?: BalanceAllowanceParams
): Promise<void>
```

Params

Copy

Ask AI

```
interface BalanceAllowanceParams {
  asset_type: AssetType;
  token_id?: string;
}

enum AssetType {
  COLLATERAL = "COLLATERAL",
  CONDITIONAL = "CONDITIONAL",
}
```

---

## [​](#api-key-management-l2) API Key Management (L2)

### [​](#getapikeys) getApiKeys()

Get all API keys associated with your account.

Signature

Copy

Ask AI

```
async getApiKeys(): Promise<ApiKeysResponse>
```

Response

Copy

Ask AI

```
interface ApiKeysResponse {
  apiKeys: ApiKeyCreds[];
}

interface ApiKeyCreds {
  key: string;
  secret: string;
  passphrase: string;
}
```

---

### [​](#deleteapikey) deleteApiKey()

Deletes (revokes) the currently authenticated API key.
**TypeScript Signature:**

Copy

Ask AI

```
async deleteApiKey(): Promise<any>
```

---

## [​](#notifications) Notifications

---

### [​](#getnotifications) getNotifications()

Retrieves all event notifications for the L2 authenticated user.
Records are removed automatically after 48 hours or if manually removed via dropNotifications().

Signature

Copy

Ask AI

```
public async getNotifications(): Promise<Notification[]>
```

Response

Copy

Ask AI

```
interface Notification {
    id: number;           // Unique notification ID
    owner: string;        // User's L2 credential apiKey or empty string for global notifications
    payload: any;         // Type-specific payload data
    timestamp?: number;   // Unix timestamp
    type: number;         // Notification type (see type mapping below)
}
```

**Notification Type Mapping**

| Name | Value | Description |
| --- | --- | --- |
| Order Cancellation | 1 | User’s order was canceled |
| Order Fill | 2 | User’s order was filled (maker or taker) |
| Market Resolved | 4 | Market was resolved |

---

### [​](#dropnotifications) dropNotifications()

Mark notifications as read/dismissed.

Signature

Copy

Ask AI

```
public async dropNotifications(params?: DropNotificationParams): Promise<void>
```

Params

Copy

Ask AI

```
interface DropNotificationParams {
    ids: string[];  // Array of notification IDs to mark as read
}
```

---

## [​](#see-also) See Also

[## Understand CLOB Authentication

Deep dive into L1 and L2 authentication](/developers/CLOB/authentication)[## Public Methods

Access market data, orderbooks, and prices.](/developers/CLOB/clients/methods-l2)[## L1 Methods

Private key authentication to create or derive API keys (L2 headers)](/developers/CLOB/clients/methods-l2)[## Web Socket API

Real-time market data streaming](/developers/CLOB/websocket/wss-overview)

[L1 Methods](/developers/CLOB/clients/methods-l1)[Builder Methods](/developers/CLOB/clients/methods-builder)

⌘I