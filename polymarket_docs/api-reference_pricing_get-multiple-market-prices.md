# Source: https://docs.polymarket.com/api-reference/pricing/get-multiple-market-prices

Get multiple market prices

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/prices
```

200

400

500

Copy

Ask AI

```
{
  "1234567890": {
    "BUY": "1800.50",
    "SELL": "1801.00"
  },
  "0987654321": {
    "BUY": "50.25",
    "SELL": "50.30"
  }
}
```

GET

/

prices

Try it

Get multiple market prices

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/prices
```

200

400

500

Copy

Ask AI

```
{
  "1234567890": {
    "BUY": "1800.50",
    "SELL": "1801.00"
  },
  "0987654321": {
    "BUY": "50.25",
    "SELL": "50.30"
  }
}
```

#### Response

200

application/json

Successful response

Map of token\_id to side to price

[​](#response-additional-properties)

{key}

object

Show child attributes

[Get market price](/api-reference/pricing/get-market-price)[Get multiple market prices by request](/api-reference/pricing/get-multiple-market-prices-by-request)

⌘I