# Source: https://docs.polymarket.com/api-reference/core/get-user-activity

Get user activity

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/activity
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
    "timestamp": 123,
    "conditionId": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
    "type": "TRADE",
    "size": 123,
    "usdcSize": 123,
    "transactionHash": "<string>",
    "price": 123,
    "asset": "<string>",
    "side": "BUY",
    "outcomeIndex": 123,
    "title": "<string>",
    "slug": "<string>",
    "icon": "<string>",
    "eventSlug": "<string>",
    "outcome": "<string>",
    "name": "<string>",
    "pseudonym": "<string>",
    "bio": "<string>",
    "profileImage": "<string>",
    "profileImageOptimized": "<string>"
  }
]
```

GET

/

activity

Try it

Get user activity

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/activity
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
    "timestamp": 123,
    "conditionId": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
    "type": "TRADE",
    "size": 123,
    "usdcSize": 123,
    "transactionHash": "<string>",
    "price": 123,
    "asset": "<string>",
    "side": "BUY",
    "outcomeIndex": 123,
    "title": "<string>",
    "slug": "<string>",
    "icon": "<string>",
    "eventSlug": "<string>",
    "outcome": "<string>",
    "name": "<string>",
    "pseudonym": "<string>",
    "bio": "<string>",
    "profileImage": "<string>",
    "profileImageOptimized": "<string>"
  }
]
```

#### Query Parameters

[​](#parameter-limit)

limit

integer

default:100

Required range: `0 <= x <= 500`

[​](#parameter-offset)

offset

integer

default:0

Required range: `0 <= x <= 10000`

[​](#parameter-user)

user

string

required

User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

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

[​](#parameter-type)

type

enum<string>[]

Available options:

`TRADE`,

`SPLIT`,

`MERGE`,

`REDEEM`,

`REWARD`,

`CONVERSION`

[​](#parameter-start)

start

integer

Required range: `x >= 0`

[​](#parameter-end)

end

integer

Required range: `x >= 0`

[​](#parameter-sort-by)

sortBy

enum<string>

default:TIMESTAMP

Available options:

`TIMESTAMP`,

`TOKENS`,

`CASH`

[​](#parameter-sort-direction)

sortDirection

enum<string>

default:DESC

Available options:

`ASC`,

`DESC`

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

[​](#response-items-timestamp)

timestamp

integer<int64>

[​](#response-items-condition-id)

conditionId

string

0x-prefixed 64-hex string

Example:

`"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"`

[​](#response-items-type)

type

enum<string>

Available options:

`TRADE`,

`SPLIT`,

`MERGE`,

`REDEEM`,

`REWARD`,

`CONVERSION`

[​](#response-items-size)

size

number

[​](#response-items-usdc-size)

usdcSize

number

[​](#response-items-transaction-hash)

transactionHash

string

[​](#response-items-price)

price

number

[​](#response-items-asset)

asset

string

[​](#response-items-side)

side

enum<string>

Available options:

`BUY`,

`SELL`

[​](#response-items-outcome-index)

outcomeIndex

integer

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

[Get trades for a user or markets](/api-reference/core/get-trades-for-a-user-or-markets)[Get top holders for markets](/api-reference/core/get-top-holders-for-markets)

⌘I