# Source: https://docs.polymarket.com/api-reference/pricing/get-market-price

Get market price

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/price
```

200

Example

Copy

Ask AI

```
{  
  "price": "1800.50"  
}
```

GET

/

price

Try it

Get market price

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://clob.polymarket.com/price
```

200

Example

Copy

Ask AI

```
{  
  "price": "1800.50"  
}
```

#### Query Parameters

[​](#parameter-token-id)

token\_id

string

required

The unique identifier for the token

[​](#parameter-side)

side

enum<string>

required

The side of the market (BUY or SELL)

Available options:

`BUY`,

`SELL`

#### Response

200

application/json

Successful response

[​](#response-price)

price

string

required

The market price (as string to maintain precision)

Example:

`"1800.50"`

[Get multiple order books summaries by request](/api-reference/orderbook/get-multiple-order-books-summaries-by-request)[Get multiple market prices](/api-reference/pricing/get-multiple-market-prices)

⌘I