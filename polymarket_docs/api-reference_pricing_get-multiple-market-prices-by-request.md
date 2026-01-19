# Source: https://docs.polymarket.com/api-reference/pricing/get-multiple-market-prices-by-request

Get multiple market prices by request

cURL

Copy

Ask AI

```
curl --request POST \
  --url https://clob.polymarket.com/prices \
  --header 'Content-Type: application/json' \
  --data '
[
  {
    "token_id": "1234567890",
    "side": "BUY"
  },
  {
    "token_id": "0987654321",
    "side": "SELL"
  }
]
'
```

200

Example

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

POST

/

prices

Try it

Get multiple market prices by request

cURL

Copy

Ask AI

```
curl --request POST \
  --url https://clob.polymarket.com/prices \
  --header 'Content-Type: application/json' \
  --data '
[
  {
    "token_id": "1234567890",
    "side": "BUY"
  },
  {
    "token_id": "0987654321",
    "side": "SELL"
  }
]
'
```

200

Example

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

#### Body

application/json

Maximum array length: `500`

[​](#body-items-token-id)

token\_id

string

required

The unique identifier for the token

Example:

`"1234567890"`

[​](#body-items-side)

side

enum<string>

required

The side of the market (BUY or SELL)

Available options:

`BUY`,

`SELL`

Example:

`"BUY"`

#### Response

200

application/json

Successful response

Map of token\_id to side to price

[​](#response-additional-properties)

{key}

object

Show child attributes

[Get multiple market prices](/api-reference/pricing/get-multiple-market-prices)[Get midpoint price](/api-reference/pricing/get-midpoint-price)

⌘I