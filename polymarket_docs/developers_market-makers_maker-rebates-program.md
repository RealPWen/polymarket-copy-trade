# Source: https://docs.polymarket.com/developers/market-makers/maker-rebates-program

On this page

* [Fee Handling by Implementation Type](#fee-handling-by-implementation-type)
* [Option 1: Official CLOB Clients (Recommended)](#option-1%3A-official-clob-clients-recommended)
* [Option 2: REST API / Custom Implementations](#option-2%3A-rest-api-%2F-custom-implementations)
* [Step 1: Fetch the Fee Rate](#step-1%3A-fetch-the-fee-rate)
* [Step 2: Include in Your Signed Order](#step-2%3A-include-in-your-signed-order)
* [Step 3: Sign and Submit](#step-3%3A-sign-and-submit)
* [Fee Behavior](#fee-behavior)
* [Fee Denomination](#fee-denomination)
* [Effective Rates: Buying (100 shares)](#effective-rates%3A-buying-100-shares)
* [Effective Rates: Selling (100 shares)](#effective-rates%3A-selling-100-shares)
* [Maker Rebates](#maker-rebates)
* [How Rebates Work](#how-rebates-work)
* [Rebate Pool](#rebate-pool)
* [Which Markets Have Fees?](#which-markets-have-fees)
* [Related Documentation](#related-documentation)

Polymarket has enabled **taker fees** on **15-minute crypto markets**. These fees fund a **Maker Rebates** program that pays daily USDC rebates to liquidity providers.

## [​](#fee-handling-by-implementation-type) Fee Handling by Implementation Type

### [​](#option-1:-official-clob-clients-recommended) Option 1: Official CLOB Clients (Recommended)

The official CLOB clients **automatically handle fees** for you. Update to the latest version:

[## TypeScript Client

npm install @polymarket/clob-client@latest](https://github.com/Polymarket/clob-client)[## Python Client

pip install —upgrade py-clob-client](https://github.com/Polymarket/py-clob-client)

**What the client does automatically:**

1. Fetches the fee rate for the market’s token ID
2. Includes `feeRateBps` in the order structure
3. Signs the order with the fee rate included

**You don’t need to do anything extra**. Just update your client and your orders will work on fee-enabled markets.


---

### [​](#option-2:-rest-api-/-custom-implementations) Option 2: REST API / Custom Implementations

If you’re calling the REST API directly or building your own order signing, you must manually include the fee rate in your **signed order payload**.

#### [​](#step-1:-fetch-the-fee-rate) Step 1: Fetch the Fee Rate

Query the fee rate for the token ID before creating your order:

Copy

Ask AI

```
GET https://clob.polymarket.com/fee-rate?token_id={token_id}
```

**Response:**

Copy

Ask AI

```
{
  "fee_rate_bps": 1000
}
```

* **Fee-enabled markets** return a value like `1000`
* **Fee-free markets** return `0`

#### [​](#step-2:-include-in-your-signed-order) Step 2: Include in Your Signed Order

Add the `feeRateBps` field to your order object. This value is **part of the signed payload**, the CLOB validates your signature against it.

Copy

Ask AI

```
{
  "salt": "12345",
  "maker": "0x...",
  "signer": "0x...",
  "taker": "0x...",
  "tokenId": "71321045679252212594626385532706912750332728571942532289631379312455583992563",
  "makerAmount": "50000000",
  "takerAmount": "100000000",
  "expiration": "0",
  "nonce": "0",
  "feeRateBps": "1000",
  "side": "0",
  "signatureType": 2,
  "signature": "0x..."
}
```

#### [​](#step-3:-sign-and-submit) Step 3: Sign and Submit

1. Include `feeRateBps` in the order object **before signing**
2. Sign the complete order
3. POST to `/order` endpoint

**Important:** Always fetch `fee_rate_bps` dynamically, do not hardcode. The fee rate may vary by market or change over time. You only need to pass `feeRateBps`

See the [Create Order documentation](/developers/CLOB/orders/create-order) for full signing details.


---

## [​](#fee-behavior) Fee Behavior

### [​](#fee-denomination) Fee Denomination

Fees are deducted from the **proceeds** of your trade:

| Order Type | You Receive | Fee Denomination |
| --- | --- | --- |
| **BUY** | Tokens | Fee in tokens |
| **SELL** | USDC | Fee in USDC |

Because fees are denominated differently, the **effective fee rate differs** between buying and selling.

### [​](#effective-rates:-buying-100-shares) Effective Rates: Buying (100 shares)

When buying, the fee is in tokens. Effective rate peaks at 50%.

| Price | Fee (tokens) | Fee ($) | Effective Rate |
| --- | --- | --- | --- |
| $0.10 | 0.20 | $0.02 | 0.2% |
| $0.30 | 1.10 | $0.33 | 1.1% |
| $0.50 | 1.56 | $0.78 | 1.6% |
| $0.70 | 1.10 | $0.77 | 1.1% |
| $0.90 | 0.20 | $0.18 | 0.2% |

### [​](#effective-rates:-selling-100-shares) Effective Rates: Selling (100 shares)

When selling, the fee is in USDC. Effective rate peaks around 30%.

| Price | Proceeds | Fee ($) | Effective Rate |
| --- | --- | --- | --- |
| $0.10 | $10 | $0.20 | 2.0% |
| $0.30 | $30 | $1.10 | 3.7% |
| $0.50 | $50 | $1.56 | 3.1% |
| $0.70 | $70 | $1.10 | 1.6% |
| $0.90 | $90 | $0.20 | 0.2% |

---

## [​](#maker-rebates) Maker Rebates

### [​](#how-rebates-work) How Rebates Work

* **Eligibility:** Your orders must add liquidity (maker orders) and get filled
* **Calculation:** Proportional to your share of executed maker volume in each eligible market
* **Payment:** Daily in USDC, paid directly to your wallet

### [​](#rebate-pool) Rebate Pool

The rebate pool for each market is funded by taker fees collected in that market. Currently, 100% of collected fees are redistributed as maker rebates.

Since taker fees are lower at price extremes, trades filled at those prices contribute less to the rebate pool.

---

## [​](#which-markets-have-fees) Which Markets Have Fees?

Currently, only **15-minute crypto markets** have fees enabled. Query the fee-rate endpoint to check:

Copy

Ask AI

```
GET https://clob.polymarket.com/fee-rate?token_id={token_id}

# Fee-enabled: { "fee_rate_bps": 1000 }
# Fee-free:    { "fee_rate_bps": 0 }
```

---

## [​](#related-documentation) Related Documentation

[## Maker Rebates Program

User-facing overview with full fee tables](/polymarket-learn/trading/maker-rebates-program)[## Create CLOB Order via REST API

Full order structure and signing documentation](/developers/CLOB/orders/create-order)

[Liquidity Rewards](/developers/market-makers/liquidity-rewards)[Data Feeds](/developers/market-makers/data-feeds)

⌘I