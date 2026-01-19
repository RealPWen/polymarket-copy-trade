# Source: https://docs.polymarket.com/api-reference/tags/get-tag-by-id

Get tag by id

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/tags/{id}
```

200

Copy

Ask AI

```
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
```

GET

/

tags

/

{id}

Try it

Get tag by id

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/tags/{id}
```

200

Copy

Ask AI

```
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
```

#### Path Parameters

[​](#parameter-id)

id

integer

required

#### Query Parameters

[​](#parameter-include-template)

include\_template

boolean

#### Response

200

application/json

Tag

[​](#response-id)

id

string

[​](#response-label-one-of-0)

label

string | null

[​](#response-slug-one-of-0)

slug

string | null

[​](#response-force-show-one-of-0)

forceShow

boolean | null

[​](#response-published-at-one-of-0)

publishedAt

string | null

[​](#response-created-by-one-of-0)

createdBy

integer | null

[​](#response-updated-by-one-of-0)

updatedBy

integer | null

[​](#response-created-at-one-of-0)

createdAt

string<date-time> | null

[​](#response-updated-at-one-of-0)

updatedAt

string<date-time> | null

[​](#response-force-hide-one-of-0)

forceHide

boolean | null

[​](#response-is-carousel-one-of-0)

isCarousel

boolean | null

[List tags](/api-reference/tags/list-tags)[Get tag by slug](/api-reference/tags/get-tag-by-slug)

⌘I