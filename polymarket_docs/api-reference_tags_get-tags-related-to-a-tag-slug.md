# Source: https://docs.polymarket.com/api-reference/tags/get-tags-related-to-a-tag-slug

Get tags related to a tag slug

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/tags/slug/{slug}/related-tags/tags
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

/

slug

/

{slug}

/

related-tags

/

tags

Try it

Get tags related to a tag slug

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/tags/slug/{slug}/related-tags/tags
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

#### Path Parameters

[​](#parameter-slug)

slug

string

required

#### Query Parameters

[​](#parameter-omit-empty)

omit\_empty

boolean

[​](#parameter-status)

status

enum<string>

Available options:

`active`,

`closed`,

`all`

#### Response

200 - application/json

Related tags

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

[Get tags related to a tag id](/api-reference/tags/get-tags-related-to-a-tag-id)[List events](/api-reference/events/list-events)

⌘I