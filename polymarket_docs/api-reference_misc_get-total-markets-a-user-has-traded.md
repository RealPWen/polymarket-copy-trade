# Source: https://docs.polymarket.com/api-reference/misc/get-total-markets-a-user-has-traded

Get total markets a user has traded

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/traded
```

200

400

401

500

Copy

Ask AI

```
{
  "user": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
  "traded": 123
}
```

GET

/

traded

Try it

Get total markets a user has traded

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://data-api.polymarket.com/traded
```

200

400

401

500

Copy

Ask AI

```
{
  "user": "0x56687bf447db6ffa42ffe2204a05edaa20f55839",
  "traded": 123
}
```

#### Query Parameters

[​](#parameter-user)

user

string

required

User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

#### Response

200

application/json

Success

[​](#response-user)

user

string

User Profile Address (0x-prefixed, 40 hex chars)

Example:

`"0x56687bf447db6ffa42ffe2204a05edaa20f55839"`

[​](#response-traded)

traded

integer

[Get trader leaderboard rankings](/api-reference/core/get-trader-leaderboard-rankings)[Get open interest](/api-reference/misc/get-open-interest)

⌘I