# Source: https://docs.polymarket.com/api-reference/sports/list-teams

List teams

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/teams
```

200

Copy

Ask AI

```
[
  {
    "id": 123,
    "name": "<string>",
    "league": "<string>",
    "record": "<string>",
    "logo": "<string>",
    "abbreviation": "<string>",
    "alias": "<string>",
    "createdAt": "2023-11-07T05:31:56Z",
    "updatedAt": "2023-11-07T05:31:56Z"
  }
]
```

GET

/

teams

Try it

List teams

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/teams
```

200

Copy

Ask AI

```
[
  {
    "id": 123,
    "name": "<string>",
    "league": "<string>",
    "record": "<string>",
    "logo": "<string>",
    "abbreviation": "<string>",
    "alias": "<string>",
    "createdAt": "2023-11-07T05:31:56Z",
    "updatedAt": "2023-11-07T05:31:56Z"
  }
]
```

#### Query Parameters

[​](#parameter-limit)

limit

integer

Required range: `x >= 0`

[​](#parameter-offset)

offset

integer

Required range: `x >= 0`

[​](#parameter-order)

order

string

Comma-separated list of fields to order by

[​](#parameter-ascending)

ascending

boolean

[​](#parameter-league)

league

string[]

[​](#parameter-name)

name

string[]

[​](#parameter-abbreviation)

abbreviation

string[]

#### Response

200 - application/json

List of teams

[​](#response-items-id)

id

integer

[​](#response-items-name-one-of-0)

name

string | null

[​](#response-items-league-one-of-0)

league

string | null

[​](#response-items-record-one-of-0)

record

string | null

[​](#response-items-logo-one-of-0)

logo

string | null

[​](#response-items-abbreviation-one-of-0)

abbreviation

string | null

[​](#response-items-alias-one-of-0)

alias

string | null

[​](#response-items-created-at-one-of-0)

createdAt

string<date-time> | null

[​](#response-items-updated-at-one-of-0)

updatedAt

string<date-time> | null

[Gamma API Health check](/api-reference/gamma-status/gamma-api-health-check)[Get sports metadata information](/api-reference/sports/get-sports-metadata-information)

⌘I