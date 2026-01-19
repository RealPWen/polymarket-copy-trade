# Source: https://docs.polymarket.com/api-reference/core/get-total-value-of-a-users-positions

Get total value of a user's positions

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/value
```

200

400

500

Copy

Ask AI

```
[
  {
    "user": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
    "value": 123
  }
]
```

GET

/

value

Try it

Get total value of a user's positions

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/value
```

200

400

500

Copy

Ask AI

```
[
  {
    "user": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
    "value": 123
  }
]
```

#### Query Parameters

[​](#parameter-user)

user

string

required

User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

[​](#parameter-market)

market

string[]

0x-prefixed 64-hex string

#### Response

200

application/json

Success

[​](#response-items-user)

user

string

User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

[​](#response-items-value)

value

number

[Get top holders for markets](/api-reference/core/get-top-holders-for-markets)[Get closed positions for a user](/api-reference/core/get-closed-positions-for-a-user)

⌘I