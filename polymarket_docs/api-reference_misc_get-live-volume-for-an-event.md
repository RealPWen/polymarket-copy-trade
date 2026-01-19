# Source: https://docs.polymarket.com/api-reference/misc/get-live-volume-for-an-event

Get live volume for an event

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/live-volume
```

200

400

500

Copy

Ask AI

```
[
  {
    "total": 123,
    "markets": [
      {
        "market": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
        "value": 123
      }
    ]
  }
]
```

GET

/

live-volume

Try it

Get live volume for an event

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/live-volume
```

200

400

500

Copy

Ask AI

```
[
  {
    "total": 123,
    "markets": [
      {
        "market": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
        "value": 123
      }
    ]
  }
]
```

#### Query Parameters

[​](#parameter-id)

id

integer

required

Required range: `x >= 1`

#### Response

200

application/json

Success

[​](#response-items-total)

total

number

[​](#response-items-markets)

markets

object[]

Show child attributes

[Get open interest](/api-reference/misc/get-open-interest)[Get aggregated builder leaderboard](/api-reference/builders/get-aggregated-builder-leaderboard)

⌘I