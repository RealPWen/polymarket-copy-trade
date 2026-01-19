# Source: https://docs.polymarket.com/developers/builders/order-attribution

On this page

* [Overview](#overview)
* [Builder API Credentials](#builder-api-credentials)
* [Signing Methods](#signing-methods)
* [Authentication Headers](#authentication-headers)
* [Next Steps](#next-steps)

## [​](#overview) Overview

The [CLOB (Central Limit Order Book)](/developers/CLOB/introduction) is Polymarket’s order matching system. Order attribution adds builder authentication headers when placing orders through the CLOB Client, enabling Polymarket to credit trades to your builder account. This allows you to:

* Track volume on the [Builder Leaderboard](https://builders.polymarket.com/)
* Compete for grants based on trading activity
* Monitor performance via the Data API

---

## [​](#builder-api-credentials) Builder API Credentials

Each builder receives API credentials from their [Builder Profile](/developers/builders/builder-profile):

| Credential | Description |
| --- | --- |
| `key` | Your builder API key identifier |
| `secret` | Secret key for signing requests |
| `passphrase` | Additional authentication passphrase |

**Security Notice**: Your Builder API keys must be kept secure. Never expose them in client-side code.

---

## [​](#signing-methods) Signing Methods

* Remote Signing (Recommended)
* Local Signing

Remote signing keeps your credentials secure on a server you control.**How it works:**

1. User signs an order payload
2. Payload is sent to your builder signing server
3. Your server adds builder authentication headers
4. Complete order is sent to the CLOB

### [​](#server-implementation) Server Implementation

Your signing server receives request details and returns the authentication headers. Use the `buildHmacSignature` function from the SDK:

TypeScript

Python

Copy

Ask AI

```
import { 
  buildHmacSignature, 
  BuilderApiKeyCreds 
} from "@polymarket/builder-signing-sdk";

const BUILDER_CREDENTIALS: BuilderApiKeyCreds = {
  key: process.env.POLY_BUILDER_API_KEY!,
  secret: process.env.POLY_BUILDER_SECRET!,
  passphrase: process.env.POLY_BUILDER_PASSPHRASE!,
};

// POST /sign - receives { method, path, body } from the client SDK
export async function handleSignRequest(request) {
  const { method, path, body } = await request.json();
  
  const timestamp = Date.now().toString();
  
  const signature = buildHmacSignature(
    BUILDER_CREDENTIALS.secret,
    parseInt(timestamp),
    method,
    path,
    body
  );

  return {
    POLY_BUILDER_SIGNATURE: signature,
    POLY_BUILDER_TIMESTAMP: timestamp,
    POLY_BUILDER_API_KEY: BUILDER_CREDENTIALS.key,
    POLY_BUILDER_PASSPHRASE: BUILDER_CREDENTIALS.passphrase,
  };
}
```

Never commit credentials to version control. Use environment variables or a secrets manager.

### [​](#client-configuration) Client Configuration

Point your client to your signing server:

TypeScript

Python

Copy

Ask AI

```
import { ClobClient } from "@polymarket/clob-client";
import { BuilderConfig } from "@polymarket/builder-signing-sdk";

// Point to your signing server
const builderConfig = new BuilderConfig({
  remoteBuilderConfig: { 
    url: "https://your-server.com/sign"
  }
});

// Or with optional authorization token
const builderConfigWithAuth = new BuilderConfig({
  remoteBuilderConfig: { 
    url: "https://your-server.com/sign", 
    token: "your-auth-token" 
  }
});

const client = new ClobClient(
  "https://clob.polymarket.com",
  137,
  signer, // ethers v5.x EOA signer
  creds, // User's API Credentials
  2, // signatureType for the Safe proxy wallet
  funderAddress, // Safe proxy wallet address
  undefined, 
  false,
  builderConfig
);

// Orders automatically use the signing server
const order = await client.createOrder({
  price: 0.40,
  side: Side.BUY,
  size: 5,
  tokenID: "YOUR_TOKEN_ID"
});

const response = await client.postOrder(order);
```

### [​](#troubleshooting) Troubleshooting

Invalid Signature Errors

**Error:** Client receives invalid signature errors**Solution:**

1. Verify the request body is passed correctly as JSON
2. Check that `path`, `body`, and `method` match what the client sends
3. Ensure your server and client use the same Builder API credentials

Missing Credentials

**Error:** `Builder credentials not configured` or undefined values**Solution:** Ensure your environment variables are set:

* `POLY_BUILDER_API_KEY`
* `POLY_BUILDER_SECRET`
* `POLY_BUILDER_PASSPHRASE`

Sign orders locally when you control the entire order placement flow.**How it works:**

1. Your system creates and signs orders on behalf of users
2. Your system uses Builder API credentials locally to add headers
3. Complete signed order is sent directly to the CLOB

TypeScript

Python

Copy

Ask AI

```
import { ClobClient } from "@polymarket/clob-client";
import { BuilderConfig, BuilderApiKeyCreds } from "@polymarket/builder-signing-sdk";

// Configure with local builder credentials
const builderCreds: BuilderApiKeyCreds = {
  key: process.env.POLY_BUILDER_API_KEY!,
  secret: process.env.POLY_BUILDER_SECRET!,
  passphrase: process.env.POLY_BUILDER_PASSPHRASE!
};

const builderConfig = new BuilderConfig({
  localBuilderCreds: builderCreds
});

const client = new ClobClient(
  "https://clob.polymarket.com",
  137,
  signer, // ethers v5.x EOA signer
  creds, // User's API Credentials
  2, // signatureType for the Safe proxy wallet
  funderAddress, // Safe proxy wallet address
  undefined, 
  false,
  builderConfig
);

// Orders automatically include builder headers
const order = await client.createOrder({
  price: 0.40,
  side: Side.BUY,
  size: 5,
  tokenID: "YOUR_TOKEN_ID"
});

const response = await client.postOrder(order);
```

Never commit credentials to version control. Use environment variables or a secrets manager.

---

## [​](#authentication-headers) Authentication Headers

The SDK automatically generates and attaches these headers to each request:

| Header | Description |
| --- | --- |
| `POLY_BUILDER_API_KEY` | Your builder API key |
| `POLY_BUILDER_TIMESTAMP` | Unix timestamp of signature creation |
| `POLY_BUILDER_PASSPHRASE` | Your builder passphrase |
| `POLY_BUILDER_SIGNATURE` | HMAC signature of the request |

With **local signing**, the SDK constructs and attaches these headers automatically. With **remote signing**, your server must return these headers (see Server Implementation above), and the SDK attaches them to the request.

---

## [​](#next-steps) Next Steps

[## Relayer Client

Learn how to configure and use the Relay Client too!](/developers/builders/relayer-client)[## CLOB Client Methods

Explore the complete CLOB client reference](/developers/CLOB/clients/methods-overview)

[Builder Profile & Keys](/developers/builders/builder-profile)[Relayer Client](/developers/builders/relayer-client)

⌘I