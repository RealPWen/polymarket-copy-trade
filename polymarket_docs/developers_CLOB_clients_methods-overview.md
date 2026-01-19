# Source: https://docs.polymarket.com/developers/CLOB/clients/methods-overview

On this page

* [Client Initialization by Use Case](#client-initialization-by-use-case)
* [Resources](#resources)

[## Public Methods

Access market data, orderbooks, and prices.](/developers/CLOB/clients/methods-public)[## L1 Methods

Private key authentication to create or derive API keys (L2 headers).](/developers/CLOB/clients/methods-l1)[## L2 Methods

Manage and close orders. Creating orders requires signer.](/developers/CLOB/clients/methods-l2)[## Builder Program Methods

Builder-specific operations for those in the Builders Program.](/developers/CLOB/clients/methods-builder)

---

## [​](#client-initialization-by-use-case) Client Initialization by Use Case

* Get Market Data
* Generate User API Credentials
* Create and Post Order
* Get Builders Orders

TypeScript

Python

Copy

Ask AI

```
// No signer or credentials needed
const client = new ClobClient(
  "https://clob.polymarket.com", 
  137
);

// All public methods available
const markets = await client.getMarkets();
const book = await client.getOrderBook(tokenId);
const price = await client.getPrice(tokenId, "BUY");
```

TypeScript

Python

Copy

Ask AI

```
// Create client with signer
const client = new ClobClient(
  "https://clob.polymarket.com", 
  137, 
  signer
);

// All public and L1 methods available
const newCreds = createApiKey();
const derivedCreds = deriveApiKey();
const creds = createOrDeriveApiKey();
```

TypeScript

Python

Copy

Ask AI

```
// Create client with signer and creds
const client = new ClobClient(
  "https://clob.polymarket.com", 
  137, 
  signer,
  creds,
  2, // Indicates Gnosis Safe proxy
  funder // Safe wallet address holding funds
);

// All public, L1, and L2 methods available
const order = await client.createOrder({ /* ... */ });
const result = await client.postOrder(order);
const trades = await client.getTrades();
```

TypeScript

Python

Copy

Ask AI

```
// Create client with builder's authentication headers
import { BuilderConfig, BuilderApiKeyCreds } from "@polymarket/builder-signing-sdk";

const builderCreds: BuilderApiKeyCreds = {
  key: process.env.POLY_BUILDER_API_KEY!,
  secret: process.env.POLY_BUILDER_SECRET!,
  passphrase: process.env.POLY_BUILDER_PASSPHRASE!
};

const builderConfig: BuilderConfig = {
  localBuilderCreds: builderCreds
};

const client = new ClobClient(
  "https://clob.polymarket.com", 
  137, 
  signer,
  creds, // User's API credentials
  2,
  funder,
  undefined,
  false,
  builderConfig // Builder's API credentials
);

// You can call all methods including builder methods
const builderTrades = await client.getBuilderTrades();
```

Learn more about the Builders Program and Relay Client here

---

## [​](#resources) Resources

[## TypeScript Client

Open source TypeScript client on GitHub](https://github.com/Polymarket/clob-client)[## Python Client

Open source Python client for GitHub](https://github.com/Polymarket/py-clob-client)[## TypeScript Examples

TypeScript client method examples](https://github.com/Polymarket/clob-client/tree/main/examples)[## Python Examples

Python client method examples](https://github.com/Polymarket/py-clob-client/tree/main/examples)[## CLOB Rest API Reference

Complete REST endpoint documentation](/api-reference/orderbook/get-order-book-summary)[## Web Socket API

Real-time market data streaming](/developers/CLOB/websocket/wss-overview)

[Geographic Restrictions](/developers/CLOB/geoblock)[Public Methods](/developers/CLOB/clients/methods-public)

⌘I