# Source: https://docs.polymarket.com/api-reference/tags/get-related-tags-relationships-by-tag-slug

Get related tags (relationships) by tag slug

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/tags/slug/{slug}/related-tags
```

200

Copy

Ask AI

```
[
  {
    "id": "<string>",
    "tagID": 123,
    "relatedTagID": 123,
    "rank": 123
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

Try it

Get related tags (relationships) by tag slug

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/tags/slug/{slug}/related-tags
```

200

Copy

Ask AI

```
[
  {
    "id": "<string>",
    "tagID": 123,
    "relatedTagID": 123,
    "rank": 123
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

Related tag relationships

[​](#response-items-id)

id

string

[​](#response-items-tag-id-one-of-0)

tagID

integer | null

[​](#response-items-related-tag-id-one-of-0)

relatedTagID

integer | null

[​](#response-items-rank-one-of-0)

rank

integer | null

[Get related tags (relationships) by tag id](/api-reference/tags/get-related-tags-relationships-by-tag-id)[Get tags related to a tag id](/api-reference/tags/get-tags-related-to-a-tag-id)

⌘I