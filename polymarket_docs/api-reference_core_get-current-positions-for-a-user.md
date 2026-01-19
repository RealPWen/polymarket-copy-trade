# Source: https://docs.polymarket.com/api-reference/core/get-current-positions-for-a-user

Get current positions for a user

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/positions
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
    "asset": "<string>",
    "conditionId": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
    "size": 123,
    "avgPrice": 123,
    "initialValue": 123,
    "currentValue": 123,
    "cashPnl": 123,
    "percentPnl": 123,
    "totalBought": 123,
    "realizedPnl": 123,
    "percentRealizedPnl": 123,
    "curPrice": 123,
    "redeemable": true,
    "mergeable": true,
    "title": "<string>",
    "slug": "<string>",
    "icon": "<string>",
    "eventSlug": "<string>",
    "outcome": "<string>",
    "outcomeIndex": 123,
    "oppositeOutcome": "<string>",
    "oppositeAsset": "<string>",
    "endDate": "<string>",
    "negativeRisk": true
  }
]
```

GET

/

positions

Try it

Get current positions for a user

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/positions
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
    "asset": "<string>",
    "conditionId": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
    "size": 123,
    "avgPrice": 123,
    "initialValue": 123,
    "currentValue": 123,
    "cashPnl": 123,
    "percentPnl": 123,
    "totalBought": 123,
    "realizedPnl": 123,
    "percentRealizedPnl": 123,
    "curPrice": 123,
    "redeemable": true,
    "mergeable": true,
    "title": "<string>",
    "slug": "<string>",
    "icon": "<string>",
    "eventSlug": "<string>",
    "outcome": "<string>",
    "outcomeIndex": 123,
    "oppositeOutcome": "<string>",
    "oppositeAsset": "<string>",
    "endDate": "<string>",
    "negativeRisk": true
  }
]
```

#### Query Parameters

[​](#parameter-user)

user

string

required

User address (required)
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

[​](#parameter-size-threshold)

sizeThreshold

number

default:1

Required range: `x >= 0`

[​](#parameter-redeemable)

redeemable

boolean

default:false

[​](#parameter-mergeable)

mergeable

boolean

default:false

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

[​](#parameter-sort-by)

sortBy

enum<string>

default:TOKENS

Available options:

`CURRENT`,

`INITIAL`,

`TOKENS`,

`CASHPNL`,

`PERCENTPNL`,

`TITLE`,

`RESOLVING`,

`PRICE`,

`AVGPRICE`

[​](#parameter-sort-direction)

sortDirection

enum<string>

default:DESC

Available options:

`ASC`,

`DESC`

[​](#parameter-title)

title

string

Maximum string length: `100`

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

[​](#response-items-avg-price)

avgPrice

number

[​](#response-items-initial-value)

initialValue

number

[​](#response-items-current-value)

currentValue

number

[​](#response-items-cash-pnl)

cashPnl

number

[​](#response-items-percent-pnl)

percentPnl

number

[​](#response-items-total-bought)

totalBought

number

[​](#response-items-realized-pnl)

realizedPnl

number

[​](#response-items-percent-realized-pnl)

percentRealizedPnl

number

[​](#response-items-cur-price)

curPrice

number

[​](#response-items-redeemable)

redeemable

boolean

[​](#response-items-mergeable)

mergeable

boolean

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

[​](#response-items-opposite-outcome)

oppositeOutcome

string

[​](#response-items-opposite-asset)

oppositeAsset

string

[​](#response-items-end-date)

endDate

string

[​](#response-items-negative-risk)

negativeRisk

boolean

[Data API Health check](/api-reference/data-api-status/data-api-health-check)[Get trades for a user or markets](/api-reference/core/get-trades-for-a-user-or-markets)

⌘I