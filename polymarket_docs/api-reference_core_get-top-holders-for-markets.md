# Source: https://docs.polymarket.com/api-reference/core/get-top-holders-for-markets

Get top holders for markets

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/holders
```

200

400

401

500

Copy

Ask AI

```
[
  {
    "token": "<string>",
    "holders": [
      {
        "proxyWallet": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
        "bio": "<string>",
        "asset": "<string>",
        "pseudonym": "<string>",
        "amount": 123,
        "displayUsernamePublic": true,
        "outcomeIndex": 123,
        "name": "<string>",
        "profileImage": "<string>",
        "profileImageOptimized": "<string>"
      }
    ]
  }
]
```

GET

/

holders

Try it

Get top holders for markets

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/holders
```

200

400

401

500

Copy

Ask AI

```
[
  {
    "token": "<string>",
    "holders": [
      {
        "proxyWallet": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
        "bio": "<string>",
        "asset": "<string>",
        "pseudonym": "<string>",
        "amount": 123,
        "displayUsernamePublic": true,
        "outcomeIndex": 123,
        "name": "<string>",
        "profileImage": "<string>",
        "profileImageOptimized": "<string>"
      }
    ]
  }
]
```

#### Query Parameters

[​](#parameter-limit)

limit

integer

default:20

Maximum number of holders to return per token. Capped at 20.

Required range: `0 <= x <= 20`

[​](#parameter-market)

market

string[]

required

Comma-separated list of condition IDs.

0x-prefixed 64-hex string

[​](#parameter-min-balance)

minBalance

integer

default:1

Required range: `0 <= x <= 999999`

#### Response

200

application/json

Success

[​](#response-items-token)

token

string

[​](#response-items-holders)

holders

object[]

Show child attributes

[Get user activity](/api-reference/core/get-user-activity)[Get total value of a user's positions](/api-reference/core/get-total-value-of-a-users-positions)

⌘I