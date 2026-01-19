# Source: https://docs.polymarket.com/developers/builders/builder-intro

On this page

* [What is a Builder?](#what-is-a-builder)
* [Program Benefits](#program-benefits)
* [Relayer Access](#relayer-access)
* [Trading Attribution](#trading-attribution)
* [Getting Started](#getting-started)
* [SDKs & Libraries](#sdks-%26-libraries)

## [​](#what-is-a-builder) What is a Builder?

A “builder” is a person, group, or organization that routes orders from their users to Polymarket.
If you’ve created a platform that allows users to trade on Polymarket via your system, this program is for you.


---

## [​](#program-benefits) Program Benefits

## Relayer Access

All onchain operations are gasless through our relayer

## Order Attribution

Get credited for orders and compete for grants on the Builder Leaderboard

## Fee Share

Earn a share of fees on routed orders

### [​](#relayer-access) Relayer Access

We expose our relayer to builders, providing gasless transactions for users with
Polymarket’s Proxy Wallets deployed via [Relayer Client](/developers/builders/relayer-client).
When transactions are routed through proxy wallets, Polymarket pays all gas fees for:

* Deploying Gnosis Safe Wallets or Custom Proxy (Magic Link users) Wallets
* Token approvals (USDC, outcome tokens)
* CTF operations (split, merge, redeem)
* Order execution (via [CLOB API](/developers/CLOB/introduction))

EOA wallets do not have relayer access. Users trading directly from an EOA pay their own gas fees.

### [​](#trading-attribution) Trading Attribution

Attach custom headers to orders to identify your builder account:

* Orders attributed to your builder account
* Compete on the [Builder Leaderboard](https://builders.polymarket.com/) for grants
* Track performance via the Data API
  + [Leaderboard API](/api-reference/builders/get-aggregated-builder-leaderboard): Get aggregated builder rankings for a time period
  + [Volume API](/api-reference/builders/get-daily-builder-volume-time-series): Get daily time-series volume data for trend analysis

---

## [​](#getting-started) Getting Started

1. **Get Builder Credentials**: Generate API keys from your [Builder Profile](/developers/builders/builder-profile)
2. **Configure Order Attribution**: Set up CLOB client to credit trades to your account ([guide](/developers/builders/order-attribution))
3. **Enable Gasless Transactions**: Use the Relayer for gas-free wallet deployment and trading ([guide](/developers/builders/relayer-client))

See [Example Apps](/developers/builders/examples) for complete Next.js reference implementations.

---

## [​](#sdks-&-libraries) SDKs & Libraries

[## CLOB Client (TypeScript)

Place orders with builder attribution](https://github.com/Polymarket/clob-client)[## CLOB Client (Python)

Place orders with builder attribution](https://github.com/Polymarket/py-clob-client)[## Relayer Client (TypeScript)

Gasless onchain transactions for your users](https://github.com/Polymarket/builder-relayer-client)[## Relayer Client (Python)

Gasless onchain transactions for your users](https://github.com/Polymarket/py-builder-relayer-client)[## Signing SDK (TypeScript)

Sign builder authentication headers](https://github.com/Polymarket/builder-signing-sdk)[## Signing SDK (Python)

Sign builder authentication headers](https://github.com/Polymarket/py-builder-signing-sdk)

[Inventory Management](/developers/market-makers/inventory)[Builder Tiers](/developers/builders/builder-tiers)

⌘I