# Source: https://docs.polymarket.com/api-reference/builders/get-daily-builder-volume-time-series

Get daily builder volume time-series

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/v1/builders/volume
```

200

400

500

Copy

Ask AI

```
[
  {
    "dt": "2025-11-15T00:00:00Z",
    "builder": "<string>",
    "builderLogo": "<string>",
    "verified": true,
    "volume": 123,
    "activeUsers": 123,
    "rank": "<string>"
  }
]
```

GET

/

v1

/

builders

/

volume

Try it

Get daily builder volume time-series

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/v1/builders/volume
```

200

400

500

Copy

Ask AI

```
[
  {
    "dt": "2025-11-15T00:00:00Z",
    "builder": "<string>",
    "builderLogo": "<string>",
    "verified": true,
    "volume": 123,
    "activeUsers": 123,
    "rank": "<string>"
  }
]
```

#### Query Parameters

[​](#parameter-time-period)

timePeriod

enum<string>

default:DAY

The time period to fetch daily records for.

Available options:

`DAY`,

`WEEK`,

`MONTH`,

`ALL`

#### Response

200

application/json

Success - Returns array of daily volume records

[​](#response-items-dt)

dt

string<date-time>

The timestamp for this volume entry in ISO 8601 format

Example:

`"2025-11-15T00:00:00Z"`

[​](#response-items-builder)

builder

string

The builder name or identifier

[​](#response-items-builder-logo)

builderLogo

string

URL to the builder's logo image

[​](#response-items-verified)

verified

boolean

Whether the builder is verified

[​](#response-items-volume)

volume

number

Trading volume for this builder on this date

[​](#response-items-active-users)

activeUsers

integer

Number of active users for this builder on this date

[​](#response-items-rank)

rank

string

The rank position of the builder on this date

[Get aggregated builder leaderboard](/api-reference/builders/get-aggregated-builder-leaderboard)[Overview](/developers/misc-endpoints/bridge-overview)

⌘I