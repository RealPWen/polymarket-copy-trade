# Source: https://docs.polymarket.com/api-reference/builders/get-aggregated-builder-leaderboard

Get aggregated builder leaderboard

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/v1/builders/leaderboard
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
    "builder": "<string>",
    "volume": 123,
    "activeUsers": 123,
    "verified": true,
    "builderLogo": "<string>"
  }
]
```

GET

/

v1

/

builders

/

leaderboard

Try it

Get aggregated builder leaderboard

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/v1/builders/leaderboard
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
    "builder": "<string>",
    "volume": 123,
    "activeUsers": 123,
    "verified": true,
    "builderLogo": "<string>"
  }
]
```

#### Query Parameters

[​](#parameter-time-period)

timePeriod

enum<string>

default:DAY

The time period to aggregate results over.

Available options:

`DAY`,

`WEEK`,

`MONTH`,

`ALL`

[​](#parameter-limit)

limit

integer

default:25

Maximum number of builders to return

Required range: `0 <= x <= 50`

[​](#parameter-offset)

offset

integer

default:0

Starting index for pagination

Required range: `0 <= x <= 1000`

#### Response

200

application/json

Success

[​](#response-items-rank)

rank

string

The rank position of the builder

[​](#response-items-builder)

builder

string

The builder name or identifier

[​](#response-items-volume)

volume

number

Total trading volume attributed to this builder

[​](#response-items-active-users)

activeUsers

integer

Number of active users for this builder

[​](#response-items-verified)

verified

boolean

Whether the builder is verified

[​](#response-items-builder-logo)

builderLogo

string

URL to the builder's logo image

[Get live volume for an event](/api-reference/misc/get-live-volume-for-an-event)[Get daily builder volume time-series](/api-reference/builders/get-daily-builder-volume-time-series)

⌘I