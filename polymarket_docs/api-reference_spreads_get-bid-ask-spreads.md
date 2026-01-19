# Source: https://docs.polymarket.com/api-reference/spreads/get-bid-ask-spreads

Get bid-ask spreads

cURL

Copy

Ask AI

```
curl --request POST \
  --url https://clob.polymarket.com/spreads \
  --header 'Content-Type: application/json' \
  --data '
[
  {
    "token_id": "1234567890"
  },
  {
    "token_id": "0987654321"
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
  "1234567890": "0.50",  
  "0987654321": "0.05"  
}
```

POST

/

spreads

Try it

Get bid-ask spreads

cURL

Copy

Ask AI

```
curl --request POST \
  --url https://clob.polymarket.com/spreads \
  --header 'Content-Type: application/json' \
  --data '
[
  {
    "token_id": "1234567890"
  },
  {
    "token_id": "0987654321"
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
  "1234567890": "0.50",  
  "0987654321": "0.05"  
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

Optional side parameter for certain operations

Available options:

`BUY`,

`SELL`

Example:

`"BUY"`

#### Response

200

application/json

Successful response

Map of token\_id to spread value

[​](#response-additional-properties)

{key}

string

[Get price history for a traded token](/api-reference/pricing/get-price-history-for-a-traded-token)[Historical Timeseries Data](/developers/CLOB/timeseries)

⌘I