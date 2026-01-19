# Source: https://docs.polymarket.com/api-reference/sports/get-sports-metadata-information

Get sports metadata information

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/sports
```

200

Copy

Ask AI

```
[
  {
    "sport": "<string>",
    "image": "<string>",
    "resolution": "<string>",
    "ordering": "<string>",
    "tags": "<string>",
    "series": "<string>"
  }
]
```

GET

/

sports

Try it

Get sports metadata information

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/sports
```

200

Copy

Ask AI

```
[
  {
    "sport": "<string>",
    "image": "<string>",
    "resolution": "<string>",
    "ordering": "<string>",
    "tags": "<string>",
    "series": "<string>"
  }
]
```

#### Response

200 - application/json

List of sports metadata objects containing sport configuration details, visual assets, and related identifiers

[​](#response-items-sport)

sport

string

The sport identifier or abbreviation

[​](#response-items-image)

image

string<uri>

URL to the sport's logo or image asset

[​](#response-items-resolution)

resolution

string<uri>

URL to the official resolution source for the sport (e.g., league website)

[​](#response-items-ordering)

ordering

string

Preferred ordering for sport display, typically "home" or "away"

[​](#response-items-tags)

tags

string

Comma-separated list of tag IDs associated with the sport for categorization and filtering

[​](#response-items-series)

series

string

Series identifier linking the sport to a specific tournament or season series

[List teams](/api-reference/sports/list-teams)[Get valid sports market types](/api-reference/sports/get-valid-sports-market-types)

⌘I