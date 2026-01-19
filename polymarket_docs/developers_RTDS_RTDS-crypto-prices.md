# Source: https://docs.polymarket.com/developers/RTDS/RTDS-crypto-prices

On this page

* [Overview](#overview)
* [Binance Source (crypto\_prices)](#binance-source-crypto-prices)
* [Subscription Details](#subscription-details)
* [Subscription Message](#subscription-message)
* [With Symbol Filter](#with-symbol-filter)
* [Chainlink Source (crypto\_prices\_chainlink)](#chainlink-source-crypto-prices-chainlink)
* [Subscription Details](#subscription-details-2)
* [Subscription Message](#subscription-message-2)
* [With Symbol Filter](#with-symbol-filter-2)
* [Message Format](#message-format)
* [Binance Source Message Format](#binance-source-message-format)
* [Chainlink Source Message Format](#chainlink-source-message-format)
* [Payload Fields](#payload-fields)
* [Example Messages](#example-messages)
* [Binance Source Examples](#binance-source-examples)
* [Solana Price Update (Binance)](#solana-price-update-binance)
* [Bitcoin Price Update (Binance)](#bitcoin-price-update-binance)
* [Chainlink Source Examples](#chainlink-source-examples)
* [Ethereum Price Update (Chainlink)](#ethereum-price-update-chainlink)
* [Bitcoin Price Update (Chainlink)](#bitcoin-price-update-chainlink)
* [Supported Symbols](#supported-symbols)
* [Binance Source Symbols](#binance-source-symbols)
* [Chainlink Source Symbols](#chainlink-source-symbols)
* [Notes](#notes)
* [General](#general)

Polymarket provides a Typescript client for interacting with this streaming service. [Download and view it’s documentation here](https://github.com/Polymarket/real-time-data-client)

## [​](#overview) Overview

The crypto prices subscription provides real-time updates for cryptocurrency price data from two different sources:

* **Binance Source** (`crypto_prices`): Real-time price data from Binance exchange
* **Chainlink Source** (`crypto_prices_chainlink`): Price data from Chainlink oracle networks

Both streams deliver current market prices for various cryptocurrency trading pairs, but use different symbol formats and subscription structures.

## [​](#binance-source-crypto-prices) Binance Source (`crypto_prices`)

### [​](#subscription-details) Subscription Details

* **Topic**: `crypto_prices`
* **Type**: `update`
* **Authentication**: Not required
* **Filters**: Optional (specific symbols can be filtered)
* **Symbol Format**: Lowercase concatenated pairs (e.g., `solusdt`, `btcusdt`)

### [​](#subscription-message) Subscription Message

Copy

Ask AI

```
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "crypto_prices",
      "type": "update"
    }
  ]
}
```

### [​](#with-symbol-filter) With Symbol Filter

To subscribe to specific cryptocurrency symbols, include a filters parameter:

Copy

Ask AI

```
{
  "action": "subscribe", 
  "subscriptions": [
    {
      "topic": "crypto_prices",
      "type": "update",
      "filters": "solusdt,btcusdt,ethusdt"
    }
  ]
}
```

## [​](#chainlink-source-crypto-prices-chainlink) Chainlink Source (`crypto_prices_chainlink`)

### [​](#subscription-details-2) Subscription Details

* **Topic**: `crypto_prices_chainlink`
* **Type**: `*` (all types)
* **Authentication**: Not required
* **Filters**: Optional (JSON object with symbol specification)
* **Symbol Format**: Slash-separated pairs (e.g., `eth/usd`, `btc/usd`)

### [​](#subscription-message-2) Subscription Message

Copy

Ask AI

```
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "crypto_prices_chainlink",
      "type": "*",
      "filters": ""
    }
  ]
}
```

### [​](#with-symbol-filter-2) With Symbol Filter

To subscribe to specific cryptocurrency symbols, include a JSON filters parameter:

Copy

Ask AI

```
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "crypto_prices_chainlink",
      "type": "*",
      "filters": "{\"symbol\":\"eth/usd\"}"
    }
  ]
}
```

## [​](#message-format) Message Format

### [​](#binance-source-message-format) Binance Source Message Format

When subscribed to Binance crypto prices (`crypto_prices`), you’ll receive messages with the following structure:

Copy

Ask AI

```
{
  "topic": "crypto_prices",
  "type": "update", 
  "timestamp": 1753314064237,
  "payload": {
    "symbol": "solusdt",
    "timestamp": 1753314064213,
    "value": 189.55
  }
}
```

### [​](#chainlink-source-message-format) Chainlink Source Message Format

When subscribed to Chainlink crypto prices (`crypto_prices_chainlink`), you’ll receive messages with the following structure:

Copy

Ask AI

```
{
  "topic": "crypto_prices_chainlink",
  "type": "update", 
  "timestamp": 1753314064237,
  "payload": {
    "symbol": "eth/usd",
    "timestamp": 1753314064213,
    "value": 3456.78
  }
}
```

## [​](#payload-fields) Payload Fields

| Field | Type | Description |
| --- | --- | --- |
| `symbol` | string | Trading pair symbol **Binance**: lowercase concatenated (e.g., “solusdt”, “btcusdt”) **Chainlink**: slash-separated (e.g., “eth/usd”, “btc/usd”) |
| `timestamp` | number | Price timestamp in Unix milliseconds |
| `value` | number | Current price value in the quote currency |

## [​](#example-messages) Example Messages

### [​](#binance-source-examples) Binance Source Examples

#### [​](#solana-price-update-binance) Solana Price Update (Binance)

Copy

Ask AI

```
{
  "topic": "crypto_prices",
  "type": "update",
  "timestamp": 1753314064237,
  "payload": {
    "symbol": "solusdt", 
    "timestamp": 1753314064213,
    "value": 189.55
  }
}
```

#### [​](#bitcoin-price-update-binance) Bitcoin Price Update (Binance)

Copy

Ask AI

```
{
  "topic": "crypto_prices",
  "type": "update", 
  "timestamp": 1753314088421,
  "payload": {
    "symbol": "btcusdt",
    "timestamp": 1753314088395,
    "value": 67234.50
  }
}
```

### [​](#chainlink-source-examples) Chainlink Source Examples

#### [​](#ethereum-price-update-chainlink) Ethereum Price Update (Chainlink)

Copy

Ask AI

```
{
  "topic": "crypto_prices_chainlink",
  "type": "update",
  "timestamp": 1753314064237,
  "payload": {
    "symbol": "eth/usd", 
    "timestamp": 1753314064213,
    "value": 3456.78
  }
}
```

#### [​](#bitcoin-price-update-chainlink) Bitcoin Price Update (Chainlink)

Copy

Ask AI

```
{
  "topic": "crypto_prices_chainlink",
  "type": "update", 
  "timestamp": 1753314088421,
  "payload": {
    "symbol": "btc/usd",
    "timestamp": 1753314088395,
    "value": 67234.50
  }
}
```

## [​](#supported-symbols) Supported Symbols

### [​](#binance-source-symbols) Binance Source Symbols

The Binance source supports various cryptocurrency trading pairs using lowercase concatenated format:

* `btcusdt` - Bitcoin to USDT
* `ethusdt` - Ethereum to USDT
* `solusdt` - Solana to USDT
* `xrpusdt` - XRP to USDT

### [​](#chainlink-source-symbols) Chainlink Source Symbols

The Chainlink source supports cryptocurrency trading pairs using slash-separated format:

* `btc/usd` - Bitcoin to USD
* `eth/usd` - Ethereum to USD
* `sol/usd` - Solana to USD
* `xrp/usd` - XRP to USD

## [​](#notes) Notes

### [​](#general) General

* Price updates are sent as market prices change
* The timestamp in the payload represents when the price was recorded
* The outer timestamp represents when the message was sent via WebSocket
* No authentication is required for crypto price data

[RTDS Overview](/developers/RTDS/RTDS-overview)[RTDS Comments](/developers/RTDS/RTDS-comments)

⌘I