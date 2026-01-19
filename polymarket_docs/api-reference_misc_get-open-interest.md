# Source: https://docs.polymarket.com/api-reference/misc/get-open-interest

Get open interest

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/oi
```

200

400

500

Copy

Ask AI

```
[
  {
    "market": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
    "value": 123
  }
]
```

GET

/

oi

Try it

Get open interest

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/oi
```

200

400

500

Copy

Ask AI

```
[
  {
    "market": "0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917",
    "value": 123
  }
]
```

#### Query Parameters

[​](#parameter-market)

market

string[]

0x-prefixed 64-hex string

#### Response

200

application/json

Success

[​](#response-items-market)

market

string

0x-prefixed 64-hex string

Example:

`"0xdd22472e552920b8438158ea7238bfadfa4f736aa4cee91a6b86c39ead110917"`

[​](#response-items-value)

value

number

[Get total markets a user has traded](/api-reference/misc/get-total-markets-a-user-has-traded)[Get live volume for an event](/api-reference/misc/get-live-volume-for-an-event)

⌘I