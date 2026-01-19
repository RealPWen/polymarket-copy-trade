# Source: https://docs.polymarket.com/api-reference/core/get-trades-for-a-user-or-markets

Get trades for a user or markets

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/trades
```

200

400

401

500

Copy

Ask AI

```
[
  {
    "proxyWallet": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
    "side": "BUY",
    "asset": "<string>",
    "conditionId": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
    "size": 123,
    "price": 123,
    "timestamp": 123,
    "title": "<string>",
    "slug": "<string>",
    "icon": "<string>",
    "eventSlug": "<string>",
    "outcome": "<string>",
    "outcomeIndex": 123,
    "name": "<string>",
    "pseudonym": "<string>",
    "bio": "<string>",
    "profileImage": "<string>",
    "profileImageOptimized": "<string>",
    "transactionHash": "<string>"
  }
]
```

GET

/

trades

Try it

Get trades for a user or markets

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/trades
```

200

400

401

500

Copy

Ask AI

```
[
  {
    "proxyWallet": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
    "side": "BUY",
    "asset": "<string>",
    "conditionId": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
    "size": 123,
    "price": 123,
    "timestamp": 123,
    "title": "<string>",
    "slug": "<string>",
    "icon": "<string>",
    "eventSlug": "<string>",
    "outcome": "<string>",
    "outcomeIndex": 123,
    "name": "<string>",
    "pseudonym": "<string>",
    "bio": "<string>",
    "profileImage": "<string>",
    "profileImageOptimized": "<string>",
    "transactionHash": "<string>"
  }
]
```

#### Query Parameters

[​](#parameter-limit)

limit

integer

default:100

Required range: `0 <= x <= 10000`

[​](#parameter-offset)

offset

integer

default:0

Required range: `0 <= x <= 10000`

[​](#parameter-taker-only)

takerOnly

boolean

default:true

[​](#parameter-filter-type)

filterType

enum<string>

Must be provided together with filterAmount.

Available options:

`CASH`,

`TOKENS`

[​](#parameter-filter-amount)

filterAmount

number

Must be provided together with filterType.

Required range: `x >= 0`

[​](#parameter-market)

market

string[]

Comma-separated list of condition IDs. Mutually exclusive with eventId.

0x-prefixed 64-hex string

[​](#parameter-event-id)

eventId

integer[]

Comma-separated list of event IDs. Mutually exclusive with market.

Required range: `x >= 1`

[​](#parameter-user)

user

string

User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

[​](#parameter-side)

side

enum<string>

Available options:

`BUY`,

`SELL`

#### Response

200

application/json

Success

[​](#response-items-proxy-wallet)

proxyWallet

string

User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

[​](#response-items-side)

side

enum<string>

Available options:

`BUY`,

`SELL`

[​](#response-items-asset)

asset

string

[​](#response-items-condition-id)

conditionId

string

0x-prefixed 64-hex string

Example:

`"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"`

[​](#response-items-size)

size

number

[​](#response-items-price)

price

number

[​](#response-items-timestamp)

timestamp

integer<int64>

[​](#response-items-title)

title

string

[​](#response-items-slug)

slug

string

[​](#response-items-icon)

icon

string

[​](#response-items-event-slug)

eventSlug

string

[​](#response-items-outcome)

outcome

string

[​](#response-items-outcome-index)

outcomeIndex

integer

[​](#response-items-name)

name

string

[​](#response-items-pseudonym)

pseudonym

string

[​](#response-items-bio)

bio

string

[​](#response-items-profile-image)

profileImage

string

[​](#response-items-profile-image-optimized)

profileImageOptimized

string

[​](#response-items-transaction-hash)

transactionHash

string

[Get current positions for a user](/api-reference/core/get-current-positions-for-a-user)[Get user activity](/api-reference/core/get-user-activity)

⌘I