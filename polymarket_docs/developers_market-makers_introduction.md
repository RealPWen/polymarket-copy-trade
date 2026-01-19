# Source: https://docs.polymarket.com/developers/market-makers/introduction

On this page

* [What is a Market Maker?](#what-is-a-market-maker)
* [Getting Started](#getting-started)
* [Available Tools](#available-tools)
* [By Action Type](#by-action-type)
* [Quick Reference](#quick-reference)
* [Support](#support)

## [​](#what-is-a-market-maker) What is a Market Maker?

A Market Maker (MM) on Polymarket is a sophisticated trader who provides liquidity to prediction markets by continuously posting bid and ask orders. By “laying the spread,” market makers enable other users to trade efficiently while earning the spread as compensation for the risk they take.
Market makers are essential to Polymarket’s ecosystem:

* **Provide liquidity** across all markets
* **Tighten spreads** for better user experience
* **Enable price discovery** through continuous quoting
* **Absorb trading flow** from retail and institutional users

**Not a Market Maker?** If you’re building an application that routes orders for your
users, see the [Builders Program](/developers/builders/builder-intro) instead. Builders
get access to gasless transactions via the Relayer Client and can earn grants through order attribution.

## [​](#getting-started) Getting Started

To become a market maker on Polymarket:

1. **Contact Polymarket** - Email [[email protected]](/cdn-cgi/l/email-protection#fb888e8b8b94898fbb8b949782969a89909e8fd5989496) to request acces to RFQ API
2. **Complete setup** - Deploy wallets, fund with USDCe, set token approvals
3. **Connect to data feeds** - WebSocket for orderbook, RTDS for low-latency data
4. **Start quoting** - Post orders via CLOB REST API or respond to RFQ requests

## [​](#available-tools) Available Tools

### [​](#by-action-type) By Action Type

[## Setup

Deposits, token approvals, wallet deployment, API keys](/developers/market-makers/setup)[## Trading

CLOB order entry, order types, quoting best practices](/developers/market-makers/trading)[## RFQ API

Request for Quote system for responding to large orders](/developers/market-makers/rfq/overview)[## Data Feeds

WebSocket, RTDS, Gamma API, on-chain data](/developers/market-makers/data-feeds)[## Inventory Management

Split, merge, and redeem outcome tokens](/developers/market-makers/inventory)[## Liquidity Rewards

Earn rewards for providing liquidity](/developers/market-makers/liquidity-rewards)

## [​](#quick-reference) Quick Reference

| Action | Tool | Documentation |
| --- | --- | --- |
| Deposit USDCe | Bridge API | [Bridge Overview](/developers/misc-endpoints/bridge-overview) |
| Approve tokens | Relayer Client | [Setup Guide](/developers/market-makers/setup) |
| Post limit orders | CLOB REST API | [CLOB Client](/developers/CLOB/clients/methods-l2) |
| Respond to RFQ | RFQ API | [RFQ Overview](/developers/market-makers/rfq/overview) |
| Monitor orderbook | WebSocket | [WebSocket Overview](/developers/CLOB/websocket/wss-overview) |
| Low-latency data | RTDS | [Data Feeds](/developers/market-makers/data-feeds) |
| Split USDCe to tokens | CTF / Relayer | [Inventory](/developers/market-makers/inventory) |
| Merge tokens to USDCe | CTF / Relayer | [Inventory](/developers/market-makers/inventory) |

## [​](#support) Support

For market maker onboarding and support, contact [[email protected]](/cdn-cgi/l/email-protection#81f2f4f1f1eef3f5c1f1eeedf8ece0f3eae4f5afe2eeec).

[Endpoints](/quickstart/reference/endpoints)[Setup](/developers/market-makers/setup)

⌘I