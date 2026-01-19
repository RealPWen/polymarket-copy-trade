# Source: https://docs.polymarket.com/api-reference/orderbook/get-order-book-summary

Get order book summary

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/book
```

200

400

404

500

Copy

Ask AI

```
{
  "market": "0x1b6f76e5b8587ee896c35847e12d11e75290a8c3934c5952e8a9d6e4c6f03cfa",
  "asset_id": "1234567890",
  "timestamp": "2023-10-01T12:00:00Z",
  "hash": "0xabc123def456...",
  "bids": [
    {
      "price": "1800.50",
      "size": "10.5"
    }
  ],
  "asks": [
    {
      "price": "1800.50",
      "size": "10.5"
    }
  ],
  "min_order_size": "0.001",
  "tick_size": "0.01",
  "neg_risk": false
}
```

GET

/

book

Try it

Get order book summary

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/book
```

200

400

404

500

Copy

Ask AI

```
{
  "market": "0x1b6f76e5b8587ee896c35847e12d11e75290a8c3934c5952e8a9d6e4c6f03cfa",
  "asset_id": "1234567890",
  "timestamp": "2023-10-01T12:00:00Z",
  "hash": "0xabc123def456...",
  "bids": [
    {
      "price": "1800.50",
      "size": "10.5"
    }
  ],
  "asks": [
    {
      "price": "1800.50",
      "size": "10.5"
    }
  ],
  "min_order_size": "0.001",
  "tick_size": "0.01",
  "neg_risk": false
}
```

#### Query Parameters

[​](#parameter-token-id)

token\_id

string

required

The unique identifier for the token

#### Response

200

application/json

Successful response

[​](#response-market)

market

string

required

Market identifier

Example:

`"0x1b6f76e5b8587ee896c35847e12d11e75290a8c3934c5952e8a9d6e4c6f03cfa"`

[​](#response-asset-id)

asset\_id

string

required

Asset identifier

Example:

`"1234567890"`

[​](#response-timestamp)

timestamp

string<date-time>

required

Timestamp of the order book snapshot

Example:

`"2023-10-01T12:00:00Z"`

[​](#response-hash)

hash

string

required

Hash of the order book state

Example:

`"0xabc123def456..."`

[​](#response-bids)

bids

object[]

required

Array of bid levels

Show child attributes

[​](#response-asks)

asks

object[]

required

Array of ask levels

Show child attributes

[​](#response-min-order-size)

min\_order\_size

string

required

Minimum order size for this market

Example:

`"0.001"`

[​](#response-tick-size)

tick\_size

string

required

Minimum price increment

Example:

`"0.01"`

[​](#response-neg-risk)

neg\_risk

boolean

required

Whether negative risk is enabled

Example:

`false`

[Builder Methods](/developers/CLOB/clients/methods-builder)[Get multiple order books summaries by request](/api-reference/orderbook/get-multiple-order-books-summaries-by-request)

⌘I