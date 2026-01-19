# Source: https://docs.polymarket.com/api-reference/orderbook/get-multiple-order-books-summaries-by-request

Get multiple order books summaries by request

cURL

Copy

Ask AI

```
curl --request POST \
  --url https://clob.polymarket.com/books \
  --header 'Content-Type: application/json' \
  --data '
[
  {
    "token_id": "1234567890"
  },
  {
    "token_id": "0987654321"
  }
]
'
```

200

Example

Copy

Ask AI

```
[  
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
]
```

POST

/

books

Try it

Get multiple order books summaries by request

cURL

Copy

Ask AI

```
curl --request POST \
  --url https://clob.polymarket.com/books \
  --header 'Content-Type: application/json' \
  --data '
[
  {
    "token_id": "1234567890"
  },
  {
    "token_id": "0987654321"
  }
]
'
```

200

Example

Copy

Ask AI

```
[  
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
]
```

#### Body

application/json

Maximum array length: `500`

[​](#body-items-token-id)

token\_id

string

required

The unique identifier for the token

Example:

`"1234567890"`

[​](#body-items-side)

side

enum<string>

Optional side parameter for certain operations

Available options:

`BUY`,

`SELL`

Example:

`"BUY"`

#### Response

200

application/json

Successful response

[​](#response-items-market)

market

string

required

Market identifier

Example:

`"0x1b6f76e5b8587ee896c35847e12d11e75290a8c3934c5952e8a9d6e4c6f03cfa"`

[​](#response-items-asset-id)

asset\_id

string

required

Asset identifier

Example:

`"1234567890"`

[​](#response-items-timestamp)

timestamp

string<date-time>

required

Timestamp of the order book snapshot

Example:

`"2023-10-01T12:00:00Z"`

[​](#response-items-hash)

hash

string

required

Hash of the order book state

Example:

`"0xabc123def456..."`

[​](#response-items-bids)

bids

object[]

required

Array of bid levels

Show child attributes

[​](#response-items-asks)

asks

object[]

required

Array of ask levels

Show child attributes

[​](#response-items-min-order-size)

min\_order\_size

string

required

Minimum order size for this market

Example:

`"0.001"`

[​](#response-items-tick-size)

tick\_size

string

required

Minimum price increment

Example:

`"0.01"`

[​](#response-items-neg-risk)

neg\_risk

boolean

required

Whether negative risk is enabled

Example:

`false`

[Get order book summary](/api-reference/orderbook/get-order-book-summary)[Get market price](/api-reference/pricing/get-market-price)

⌘I