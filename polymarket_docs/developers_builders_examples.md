# Source: https://docs.polymarket.com/developers/builders/examples

On this page

* [Overview](#overview)
* [Safe Wallet Examples](#safe-wallet-examples)
* [Proxy Wallet Examples](#proxy-wallet-examples)
* [What Each Demo Covers](#what-each-demo-covers)

## [​](#overview) Overview

These open-source demo applications show how to integrate Polymarket’s CLOB Client and Builder Relayer Client for gasless trading with builder order attribution.

## Authentication

Multiple wallet providers

## Gasless Trading

Safe & Proxy wallet support

## Full Integration

Orders, positions, CTF ops

---

## [​](#safe-wallet-examples) Safe Wallet Examples

Deploy Gnosis Safe wallets for your users:

[## wagmi + Safe

MetaMask, Phantom, Rabby, and other browser wallets](https://github.com/Polymarket/wagmi-safe-builder-example)[## Privy + Safe

Privy embedded wallets](https://github.com/Polymarket/privy-safe-builder-example)[## Magic Link + Safe

Magic Link email/social authentication](https://github.com/Polymarket/magic-safe-builder-example)[## Turnkey + Safe

Turnkey embedded wallets](https://github.com/Polymarket/turnkey-safe-builder-example)

## [​](#proxy-wallet-examples) Proxy Wallet Examples

For existing Magic Link users from Polymarket.com:

[## Magic Link + Proxy

Auto-deploying proxy wallets for Polymarket.com Magic users](https://github.com/Polymarket/magic-proxy-builder-example)

---

## [​](#what-each-demo-covers) What Each Demo Covers

* Authentication
* Wallet Operations
* Trading

* User sign-in via wallet provider
* User API credential derivation (L2 auth)
* Builder config with remote signing
* Signature types for Safe vs Proxy wallets

* Safe wallet deployment via Relayer
* Batch token approvals (USDC.e + outcome tokens)
* CTF operations (split, merge, redeem)
* Transaction monitoring

* CLOB client initialization
* Order placement with builder attribution
* Position and order management
* Market discovery via Gamma API

[Relayer Client](/developers/builders/relayer-client)[CLOB Introduction](/developers/CLOB/introduction)

⌘I