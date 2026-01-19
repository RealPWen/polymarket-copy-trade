# Source: https://docs.polymarket.com/api-reference/core/get-trader-leaderboard-rankings

Get trader leaderboard rankings

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/v1/leaderboard
```

200

400

500

Copy

Ask AI

```
[
  {
    "rank": "<string>",
    "proxyWallet": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
    "userName": "<string>",
    "vol": 123,
    "pnl": 123,
    "profileImage": "<string>",
    "xUsername": "<string>",
    "verifiedBadge": true
  }
]
```

GET

/

v1

/

leaderboard

Try it

Get trader leaderboard rankings

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/v1/leaderboard
```

200

400

500

Copy

Ask AI

```
[
  {
    "rank": "<string>",
    "proxyWallet": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
    "userName": "<string>",
    "vol": 123,
    "pnl": 123,
    "profileImage": "<string>",
    "xUsername": "<string>",
    "verifiedBadge": true
  }
]
```

#### Query Parameters

[​](#parameter-category)

category

enum<string>

default:OVERALL

Market category for the leaderboard

Available options:

`OVERALL`,

`POLITICS`,

`SPORTS`,

`CRYPTO`,

`CULTURE`,

`MENTIONS`,

`WEATHER`,

`ECONOMICS`,

`TECH`,

`FINANCE`

[​](#parameter-time-period)

timePeriod

enum<string>

default:DAY

Time period for leaderboard results

Available options:

`DAY`,

`WEEK`,

`MONTH`,

`ALL`

[​](#parameter-order-by)

orderBy

enum<string>

default:PNL

Leaderboard ordering criteria

Available options:

`PNL`,

`VOL`

[​](#parameter-limit)

limit

integer

default:25

Max number of leaderboard traders to return

Required range: `1 <= x <= 50`

[​](#parameter-offset)

offset

integer

default:0

Starting index for pagination

Required range: `0 <= x <= 1000`

[​](#parameter-user)

user

string

Limit leaderboard to a single user by address
User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

[​](#parameter-user-name)

userName

string

Limit leaderboard to a single username

#### Response

200

application/json

Success

[​](#response-items-rank)

rank

string

The rank position of the trader

[​](#response-items-proxy-wallet)

proxyWallet

string

User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

[​](#response-items-user-name)

userName

string

The trader's username

[​](#response-items-vol)

vol

number

Trading volume for this trader

[​](#response-items-pnl)

pnl

number

Profit and loss for this trader

[​](#response-items-profile-image)

profileImage

string

URL to the trader's profile image

[​](#response-items-x-username)

xUsername

string

The trader's X (Twitter) username

[​](#response-items-verified-badge)

verifiedBadge

boolean

Whether the trader has a verified badge

[Get closed positions for a user](/api-reference/core/get-closed-positions-for-a-user)[Get total markets a user has traded](/api-reference/misc/get-total-markets-a-user-has-traded)

⌘I