# Source: https://docs.polymarket.com/api-reference/core/get-closed-positions-for-a-user

Get closed positions for a user

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/v1/closed-positions
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
    "avgPrice": 123,
    "totalBought": 123,
    "realizedPnl": 123,
    "curPrice": 123,
    "timestamp": 123,
    "title": "<string>",
    "slug": "<string>",
    "icon": "<string>",
    "eventSlug": "<string>",
    "outcome": "<string>",
    "outcomeIndex": 123,
    "oppositeOutcome": "<string>",
    "oppositeAsset": "<string>",
    "endDate": "<string>"
  }
]
```

GET

/

v1

/

closed-positions

Try it

Get closed positions for a user

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/v1/closed-positions
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
    "avgPrice": 123,
    "totalBought": 123,
    "realizedPnl": 123,
    "curPrice": 123,
    "timestamp": 123,
    "title": "<string>",
    "slug": "<string>",
    "icon": "<string>",
    "eventSlug": "<string>",
    "outcome": "<string>",
    "outcomeIndex": 123,
    "oppositeOutcome": "<string>",
    "oppositeAsset": "<string>",
    "endDate": "<string>"
  }
]
```

#### Query Parameters

[​](#parameter-user)

user

string

required

The address of the user in question
User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

[​](#parameter-market)

market

string[]

The conditionId of the market in question. Supports multiple csv separated values. Cannot be used with the eventId param.

0x-prefixed 64-hex string

[​](#parameter-title)

title

string

Filter by market title

Maximum string length: `100`

[​](#parameter-event-id)

eventId

integer[]

The event id of the event in question. Supports multiple csv separated values. Returns positions for all markets for those event ids. Cannot be used with the market param.

Required range: `x >= 1`

[​](#parameter-limit)

limit

integer

default:10

The max number of positions to return

Required range: `0 <= x <= 50`

[​](#parameter-offset)

offset

integer

default:0

The starting index for pagination

Required range: `0 <= x <= 100000`

[​](#parameter-sort-by)

sortBy

enum<string>

default:REALIZEDPNL

The sort criteria

Available options:

`REALIZEDPNL`,

`TITLE`,

`PRICE`,

`AVGPRICE`,

`TIMESTAMP`

[​](#parameter-sort-direction)

sortDirection

enum<string>

default:DESC

The sort direction

Available options:

`ASC`,

`DESC`

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

[​](#response-items-avg-price)

avgPrice

number

[​](#response-items-total-bought)

totalBought

number

[​](#response-items-realized-pnl)

realizedPnl

number

[​](#response-items-cur-price)

curPrice

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

[​](#response-items-opposite-outcome)

oppositeOutcome

string

[​](#response-items-opposite-asset)

oppositeAsset

string

[​](#response-items-end-date)

endDate

string

[Get total value of a user's positions](/api-reference/core/get-total-value-of-a-users-positions)[Get trader leaderboard rankings](/api-reference/core/get-trader-leaderboard-rankings)

⌘I