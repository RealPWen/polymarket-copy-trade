# Source: https://docs.polymarket.com/api-reference/pricing/get-midpoint-price

Get midpoint price

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/midpoint
```

200

400

404

500

Copy

Ask AI

```
{
  "mid": "1800.75"
}
```

GET

/

midpoint

Try it

Get midpoint price

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/midpoint
```

200

400

404

500

Copy

Ask AI

```
{
  "mid": "1800.75"
}
```

#### Query Parameters

[​](#parameter-token-id)

token\_id

string

required

The unique identifier for the token

#### Response

200

application/json

Successful response

[​](#response-mid)

mid

string

required

The midpoint price (as string to maintain precision)

Example:

`"1800.75"`

[Get multiple market prices by request](/api-reference/pricing/get-multiple-market-prices-by-request)[Get price history for a traded token](/api-reference/pricing/get-price-history-for-a-traded-token)

⌘I