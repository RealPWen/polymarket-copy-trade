# Source: https://docs.polymarket.com/developers/misc-endpoints/bridge-overview

On this page

* [Overview](#overview)
* [USDC.e on Polygon](#usdc-e-on-polygon)
* [Base URL](#base-url)
* [Key Features](#key-features)
* [Endpoints](#endpoints)

## [​](#overview) Overview

The Polymarket Bridge API enables seamless deposits between multiple blockchains and Polymarket.

### [​](#usdc-e-on-polygon) USDC.e on Polygon

**Polymarket uses USDC.e (Bridged USDC) on Polygon as collateral** for all trading activities. USDC.e is the bridged version of USDC from Ethereum, and it serves as the native currency for placing orders and settling trades on Polymarket.
When you deposit assets to Polymarket:

1. You can deposit from various supported chains (Ethereum, Solana, Arbitrum, Base, etc.)
2. Your assets are automatically bridged/swapped to USDC.e on Polygon
3. USDC.e is credited to your Polymarket wallet
4. You can now trade on any Polymarket market

## [​](#base-url) Base URL

Copy

Ask AI

```
https://bridge.polymarket.com
```

## [​](#key-features) Key Features

* **Multi-chain deposits**: Bridge assets from EVM chains (Ethereum, Arbitrum, Base, etc.), Solana, and Bitcoin
* **Automatic conversion**: Assets are automatically bridged/swapped to USDC.e on Polygon
* **Simple addressing**: One deposit address per blockchain type (EVM, SVM, BTC)

## [​](#endpoints) Endpoints

* `POST /deposit` - Create unique deposit addresses for bridging assets
* `GET /supported-assets` - Get all supported chains and tokens

[Get daily builder volume time-series](/api-reference/builders/get-daily-builder-volume-time-series)[Create deposit addresses](/api-reference/bridge/create-deposit-addresses)

⌘I