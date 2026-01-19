# Source: https://docs.polymarket.com/developers/CLOB/clients/methods-public

On this page

* [Client Initialization](#client-initialization)
* [Health Check](#health-check)
* [getOk()](#getok)
* [Markets](#markets)
* [getMarket()](#getmarket)
* [getMarkets()](#getmarkets)
* [getSimplifiedMarkets()](#getsimplifiedmarkets)
* [getSamplingMarkets()](#getsamplingmarkets)
* [getSamplingSimplifiedMarkets()](#getsamplingsimplifiedmarkets)
* [Order Books and Prices](#order-books-and-prices)
* [calculateMarketPrice()](#calculatemarketprice)
* [getOrderBook()](#getorderbook)
* [getOrderBooks()](#getorderbooks)
* [getPrice()](#getprice)
* [getPrices()](#getprices)
* [getMidpoint()](#getmidpoint)
* [getMidpoints()](#getmidpoints)
* [getSpread()](#getspread)
* [getSpreads()](#getspreads)
* [getPricesHistory()](#getpriceshistory)
* [Trades](#trades)
* [getLastTradePrice()](#getlasttradeprice)
* [getLastTradesPrices()](#getlasttradesprices)
* [getMarketTradesEvents](#getmarkettradesevents)
* [Market Parameters](#market-parameters)
* [getFeeRateBps()](#getfeeratebps)
* [getTickSize()](#getticksize)
* [getNegRisk()](#getnegrisk)
* [Time & Server Info](#time-%26-server-info)
* [getServerTime()](#getservertime)
* [See Also](#see-also)

## [​](#client-initialization) Client Initialization

Public methods require the client to initialize with the host URL and Polygon chain ID.

* TypeScript
* Python

Copy

Ask AI

```
import { ClobClient } from "@polymarket/clob-client";

const client = new ClobClient(
  "https://clob.polymarket.com",
  137
);

// Ready to call public methods
const markets = await client.getMarkets();
```

Copy

Ask AI

```
from py_clob_client.client import ClobClient

client = ClobClient(
    host="https://clob.polymarket.com",
    chain_id=137
)

# Ready to call public methods
markets = await client.get_markets()
```

---

## [​](#health-check) Health Check

---

### [​](#getok) getOk()

Health check endpoint to verify the CLOB service is operational.

Signature

Copy

Ask AI

```
async getOk(): Promise<any>
```

---

## [​](#markets) Markets

---

### [​](#getmarket) getMarket()

Get details for a single market by condition ID.

Signature

Copy

Ask AI

```
async getMarket(conditionId: string): Promise<Market>
```

Response

Copy

Ask AI

```
interface MarketToken {
  outcome: string;
  price: number;
  token_id: string;
  winner: boolean;
}

interface Market {
  accepting_order_timestamp: string | null;
  accepting_orders: boolean;
  active: boolean;
  archived: boolean;
  closed: boolean;
  condition_id: string;
  description: string;
  enable_order_book: boolean;
  end_date_iso: string;
  fpmm: string;
  game_start_time: string;
  icon: string;
  image: string;
  is_50_50_outcome: boolean;
  maker_base_fee: number;
  market_slug: string;
  minimum_order_size: number;
  minimum_tick_size: number;
  neg_risk: boolean;
  neg_risk_market_id: string;
  neg_risk_request_id: string;
  notifications_enabled: boolean;
  question: string;
  question_id: string;
  rewards: {
    max_spread: number;
    min_size: number;
    rates: any | null;
  };
  seconds_delay: number;
  tags: string[];
  taker_base_fee: number;
  tokens: MarketToken[];
}
```

---

### [​](#getmarkets) getMarkets()

Get details for multiple markets paginated.

Signature

Copy

Ask AI

```
async getMarkets(): Promise<PaginationPayload>
```

Response

Copy

Ask AI

```
interface PaginationPayload {
  limit: number;
  count: number;
  data: Market[];
}

interface Market {
  accepting_order_timestamp: string | null;
  accepting_orders: boolean;
  active: boolean;
  archived: boolean;
  closed: boolean;
  condition_id: string;
  description: string;
  enable_order_book: boolean;
  end_date_iso: string;
  fpmm: string;
  game_start_time: string;
  icon: string;
  image: string;
  is_50_50_outcome: boolean;
  maker_base_fee: number;
  market_slug: string;
  minimum_order_size: number;
  minimum_tick_size: number;
  neg_risk: boolean;
  neg_risk_market_id: string;
  neg_risk_request_id: string;
  notifications_enabled: boolean;
  question: string;
  question_id: string;
  rewards: {
    max_spread: number;
    min_size: number;
    rates: any | null;
  };
  seconds_delay: number;
  tags: string[];
  taker_base_fee: number;
  tokens: MarketToken[];
}

interface MarketToken {
  outcome: string;
  price: number;
  token_id: string;
  winner: boolean;
}
```

---

### [​](#getsimplifiedmarkets) getSimplifiedMarkets()

Get simplified market data paginated for faster loading.

Signature

Copy

Ask AI

```
async getSimplifiedMarkets(): Promise<PaginationPayload>
```

Response

Copy

Ask AI

```
interface PaginationPayload {
  limit: number;
  count: number;
  data: SimplifiedMarket[];
}

interface SimplifiedMarket {
  accepting_orders: boolean;
  active: boolean;
  archived: boolean;
  closed: boolean;
  condition_id: string;
  rewards: {
    rates: any | null;
    min_size: number;
    max_spread: number;
  };
    tokens: SimplifiedToken[];
}

interface SimplifiedToken {
  outcome: string;
  price: number;
  token_id: string;
}
```

---

### [​](#getsamplingmarkets) getSamplingMarkets()

Signature

Copy

Ask AI

```
async getSamplingMarkets(): Promise<PaginationPayload>
```

Response

Copy

Ask AI

```
interface PaginationPayload {
  limit: number;
  count: number;
  data: Market[];
}

interface Market {
  accepting_order_timestamp: string | null;
  accepting_orders: boolean;
  active: boolean;
  archived: boolean;
  closed: boolean;
  condition_id: string;
  description: string;
  enable_order_book: boolean;
  end_date_iso: string;
  fpmm: string;
  game_start_time: string;
  icon: string;
  image: string;
  is_50_50_outcome: boolean;
  maker_base_fee: number;
  market_slug: string;
  minimum_order_size: number;
  minimum_tick_size: number;
  neg_risk: boolean;
  neg_risk_market_id: string;
  neg_risk_request_id: string;
  notifications_enabled: boolean;
  question: string;
  question_id: string;
  rewards: {
    max_spread: number;
    min_size: number;
    rates: any | null;
  };
  seconds_delay: number;
  tags: string[];
  taker_base_fee: number;
  tokens: MarketToken[];
}

interface MarketToken {
  outcome: string;
  price: number;
  token_id: string;
  winner: boolean;
}
```

---

### [​](#getsamplingsimplifiedmarkets) getSamplingSimplifiedMarkets()

Signature

Copy

Ask AI

```
async getSamplingSimplifiedMarkets(): Promise<PaginationPayload>
```

Response

Copy

Ask AI

```
interface PaginationPayload {
  limit: number;
  count: number;
  data: SimplifiedMarket[];
}

interface SimplifiedMarket {
  accepting_orders: boolean;
  active: boolean;
  archived: boolean;
  closed: boolean;
  condition_id: string;
  rewards: {
    rates: any | null;
    min_size: number;
    max_spread: number;
  };
    tokens: SimplifiedToken[];
}

interface SimplifiedToken {
  outcome: string;
  price: number;
  token_id: string;
}
```

---

## [​](#order-books-and-prices) Order Books and Prices

---

### [​](#calculatemarketprice) calculateMarketPrice()

Signature

Copy

Ask AI

```
async calculateMarketPrice(
  tokenID: string,
  side: Side,
  amount: number,
  orderType: OrderType = OrderType.FOK
): Promise<number>
```

Params

Copy

Ask AI

```
enum OrderType {
  GTC = "GTC",  // Good Till Cancelled
  FOK = "FOK",  // Fill or Kill
  GTD = "GTD",  // Good Till Date
  FAK = "FAK",  // Fill and Kill
}

enum Side {
  BUY = "BUY",
  SELL = "SELL",
}
```

Response

Copy

Ask AI

```
number // calculated market price
```

---

### [​](#getorderbook) getOrderBook()

Get the order book for a specific token ID.

Signature

Copy

Ask AI

```
async getOrderBook(tokenID: string): Promise<OrderBookSummary>
```

Response

Copy

Ask AI

```
interface OrderBookSummary {
  market: string;
  asset_id: string;
  timestamp: string;
  bids: OrderSummary[];
  asks: OrderSummary[];
  min_order_size: string;
  tick_size: string;
  neg_risk: boolean;
  hash: string;
}

interface OrderSummary {
  price: string;
  size: string;
}
```

---

### [​](#getorderbooks) getOrderBooks()

Get order books for multiple token IDs.

Signature

Copy

Ask AI

```
async getOrderBooks(params: BookParams[]): Promise<OrderBookSummary[]>
```

Params

Copy

Ask AI

```
interface BookParams {
  token_id: string;
  side: Side;  // Side.BUY or Side.SELL
}
```

Response

Copy

Ask AI

```
OrderBookSummary[]
```

---

### [​](#getprice) getPrice()

Get the current best price for buying or selling a token ID.

Signature

Copy

Ask AI

```
async getPrice(
  tokenID: string,
  side: "BUY" | "SELL"
): Promise<any>
```

Response

Copy

Ask AI

```
{
  price: string;
}
```

---

### [​](#getprices) getPrices()

Get the current best prices for multiple token IDs.

Signature

Copy

Ask AI

```
async getPrices(params: BookParams[]): Promise<PricesResponse>
```

Params

Copy

Ask AI

```
interface BookParams {
  token_id: string;
  side: Side;  // Side.BUY or Side.SELL
}
```

Response

Copy

Ask AI

```
interface TokenPrices {
  BUY?: string;
  SELL?: string;
}

type PricesResponse = {
  [tokenId: string]: TokenPrices;
}
```

---

### [​](#getmidpoint) getMidpoint()

Get the midpoint price (average of best bid and best ask) for a token ID.

Signature

Copy

Ask AI

```
async getMidpoint(tokenID: string): Promise<any>
```

Response

Copy

Ask AI

```
{
  mid: string;
}
```

---

### [​](#getmidpoints) getMidpoints()

Get the midpoint prices (average of best bid and best ask) for multiple token IDs.

Signature

Copy

Ask AI

```
async getMidpoints(params: BookParams[]): Promise<any>
```

Params

Copy

Ask AI

```
interface BookParams {
  token_id: string;
  side: Side;  // Side is ignored
}
```

Response

Copy

Ask AI

```
{
  [tokenId: string]: string;
}
```

---

### [​](#getspread) getSpread()

Get the spread (difference between best ask and best bid) for a token ID.

Signature

Copy

Ask AI

```
async getSpread(tokenID: string): Promise<SpreadResponse>
```

Response

Copy

Ask AI

```
interface SpreadResponse {
  spread: string;
}
```

---

### [​](#getspreads) getSpreads()

Get the spreads (difference between best ask and best bid) for multiple token IDs.

Signature

Copy

Ask AI

```
async getSpreads(params: BookParams[]): Promise<SpreadsResponse>
```

Params

Copy

Ask AI

```
interface BookParams {
  token_id: string;
  side: Side;
}
```

Response

Copy

Ask AI

```
type SpreadsResponse = {
  [tokenId: string]: string;
}
```

---

### [​](#getpriceshistory) getPricesHistory()

Get historical price data for a token.

Signature

Copy

Ask AI

```
async getPricesHistory(params: PriceHistoryFilterParams): Promise<MarketPrice[]>
```

Params

Copy

Ask AI

```
interface PriceHistoryFilterParams {
  market: string; // tokenID
  startTs?: number;
  endTs?: number;
  fidelity?: number;
  interval: PriceHistoryInterval;
}

enum PriceHistoryInterval {
  MAX = "max",
  ONE_WEEK = "1w",
  ONE_DAY = "1d",
  SIX_HOURS = "6h",
  ONE_HOUR = "1h",
}
```

Response

Copy

Ask AI

```
interface MarketPrice {
  t: number;  // timestamp
  p: number;  // price
}
```

---

## [​](#trades) Trades

---

### [​](#getlasttradeprice) getLastTradePrice()

Get the price of the most recent trade for a token.

Signature

Copy

Ask AI

```
async getLastTradePrice(tokenID: string): Promise<LastTradePrice>
```

Response

Copy

Ask AI

```
interface LastTradePrice {
  price: string;
  side: string;
}
```

---

### [​](#getlasttradesprices) getLastTradesPrices()

Get the price of the most recent trade for a token.

Signature

Copy

Ask AI

```
async getLastTradesPrices(params: BookParams[]): Promise<LastTradePriceWithToken[]>
```

Params

Copy

Ask AI

```
interface BookParams {
  token_id: string;
  side: Side;
}
```

Response

Copy

Ask AI

```
interface LastTradePriceWithToken {
  price: string;
  side: string;
  token_id: string;
}
```

---

### [​](#getmarkettradesevents) getMarketTradesEvents

Signature

Copy

Ask AI

```
async getMarketTradesEvents(conditionID: string): Promise<MarketTradeEvent[]>
```

Response

Copy

Ask AI

```
interface MarketTradeEvent {
  event_type: string;
  market: {
    condition_id: string;
    asset_id: string;
    question: string;
    icon: string;
    slug: string;
  };
  user: {
    address: string;
    username: string;
    profile_picture: string;
    optimized_profile_picture: string;
    pseudonym: string;
  };
  side: Side;
  size: string;
  fee_rate_bps: string;
  price: string;
  outcome: string;
  outcome_index: number;
  transaction_hash: string;
  timestamp: string;
}
```

## [​](#market-parameters) Market Parameters

---

### [​](#getfeeratebps) getFeeRateBps()

Get the fee rate in basis points for a token.

Signature

Copy

Ask AI

```
async getFeeRateBps(tokenID: string): Promise<number>
```

Response

Copy

Ask AI

```
number
```

---

### [​](#getticksize) getTickSize()

Get the tick size (minimum price increment) for a market.

Signature

Copy

Ask AI

```
async getTickSize(tokenID: string): Promise<TickSize>
```

Response

Copy

Ask AI

```
type TickSize = "0.1" | "0.01" | "0.001" | "0.0001";
```

---

### [​](#getnegrisk) getNegRisk()

Check if a market uses negative risk (binary complementary tokens).

Signature

Copy

Ask AI

```
async getNegRisk(tokenID: string): Promise<boolean>
```

Response

Copy

Ask AI

```
boolean
```

---

## [​](#time-&-server-info) Time & Server Info

### [​](#getservertime) getServerTime()

Get the current server timestamp.

Signature

Copy

Ask AI

```
async getServerTime(): Promise<number>
```

Response

Copy

Ask AI

```
number // Unix timestamp in seconds
```

---

## [​](#see-also) See Also

[## L1 Methods

Private key authentication to create or derive API keys (L2 headers).](/developers/CLOB/clients/methods-l1)[## L2 Methods

Manage and close orders. Creating orders requires signer.](/developers/CLOB/clients/methods-l2)[## CLOB Rest API Reference

Complete REST endpoint documentation](/api-reference/orderbook/get-order-book-summary)[## Web Socket API

Real-time market data streaming](/developers/CLOB/websocket/wss-overview)

[Methods Overview](/developers/CLOB/clients/methods-overview)[L1 Methods](/developers/CLOB/clients/methods-l1)

⌘I