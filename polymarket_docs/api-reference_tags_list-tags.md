# Source: https://docs.polymarket.com/api-reference/tags/list-tags

List tags

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/tags
```

200

Copy

Ask AI

```
[
  {
    "id": "<string>",
    "label": "<string>",
    "slug": "<string>",
    "forceShow": true,
    "publishedAt": "<string>",
    "createdBy": 123,
    "updatedBy": 123,
    "createdAt": "2023-11-07T05:31:56Z",
    "updatedAt": "2023-11-07T05:31:56Z",
    "forceHide": true,
    "isCarousel": true
  }
]
```

GET

/

tags

Try it

List tags

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/tags
```

200

Copy

Ask AI

```
[
  {
    "id": "<string>",
    "label": "<string>",
    "slug": "<string>",
    "forceShow": true,
    "publishedAt": "<string>",
    "createdBy": 123,
    "updatedBy": 123,
    "createdAt": "2023-11-07T05:31:56Z",
    "updatedAt": "2023-11-07T05:31:56Z",
    "forceHide": true,
    "isCarousel": true
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

[​](#parameter-include-template)

include\_template

boolean

[​](#parameter-is-carousel)

is\_carousel

boolean

#### Response

200 - application/json

List of tags

[​](#response-items-id)

id

string

[​](#response-items-label-one-of-0)

label

string | null

[​](#response-items-slug-one-of-0)

slug

string | null

[​](#response-items-force-show-one-of-0)

forceShow

boolean | null

[​](#response-items-published-at-one-of-0)

publishedAt

string | null

[​](#response-items-created-by-one-of-0)

createdBy

integer | null

[​](#response-items-updated-by-one-of-0)

updatedBy

integer | null

[​](#response-items-created-at-one-of-0)

createdAt

string<date-time> | null

[​](#response-items-updated-at-one-of-0)

updatedAt

string<date-time> | null

[​](#response-items-force-hide-one-of-0)

forceHide

boolean | null

[​](#response-items-is-carousel-one-of-0)

isCarousel

boolean | null

[Get valid sports market types](/api-reference/sports/get-valid-sports-market-types)[Get tag by id](/api-reference/tags/get-tag-by-id)

⌘I