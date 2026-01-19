# Source: https://docs.polymarket.com/api-reference/comments/list-comments

List comments

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/comments
```

200

Copy

Ask AI

```
[
  {
    "id": "<string>",
    "body": "<string>",
    "parentEntityType": "<string>",
    "parentEntityID": 123,
    "parentCommentID": "<string>",
    "userAddress": "<string>",
    "replyAddress": "<string>",
    "createdAt": "2023-11-07T05:31:56Z",
    "updatedAt": "2023-11-07T05:31:56Z",
    "profile": {
      "name": "<string>",
      "pseudonym": "<string>",
      "displayUsernamePublic": true,
      "bio": "<string>",
      "isMod": true,
      "isCreator": true,
      "proxyWallet": "<string>",
      "baseAddress": "<string>",
      "profileImage": "<string>",
      "profileImageOptimized": {
        "id": "<string>",
        "imageUrlSource": "<string>",
        "imageUrlOptimized": "<string>",
        "imageSizeKbSource": 123,
        "imageSizeKbOptimized": 123,
        "imageOptimizedComplete": true,
        "imageOptimizedLastUpdated": "<string>",
        "relID": 123,
        "field": "<string>",
        "relname": "<string>"
      },
      "positions": [
        {
          "tokenId": "<string>",
          "positionSize": "<string>"
        }
      ]
    },
    "reactions": [
      {
        "id": "<string>",
        "commentID": 123,
        "reactionType": "<string>",
        "icon": "<string>",
        "userAddress": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "profile": {
          "name": "<string>",
          "pseudonym": "<string>",
          "displayUsernamePublic": true,
          "bio": "<string>",
          "isMod": true,
          "isCreator": true,
          "proxyWallet": "<string>",
          "baseAddress": "<string>",
          "profileImage": "<string>",
          "profileImageOptimized": {
            "id": "<string>",
            "imageUrlSource": "<string>",
            "imageUrlOptimized": "<string>",
            "imageSizeKbSource": 123,
            "imageSizeKbOptimized": 123,
            "imageOptimizedComplete": true,
            "imageOptimizedLastUpdated": "<string>",
            "relID": 123,
            "field": "<string>",
            "relname": "<string>"
          },
          "positions": [
            {
              "tokenId": "<string>",
              "positionSize": "<string>"
            }
          ]
        }
      }
    ],
    "reportCount": 123,
    "reactionCount": 123
  }
]
```

GET

/

comments

Try it

List comments

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/comments
```

200

Copy

Ask AI

```
[
  {
    "id": "<string>",
    "body": "<string>",
    "parentEntityType": "<string>",
    "parentEntityID": 123,
    "parentCommentID": "<string>",
    "userAddress": "<string>",
    "replyAddress": "<string>",
    "createdAt": "2023-11-07T05:31:56Z",
    "updatedAt": "2023-11-07T05:31:56Z",
    "profile": {
      "name": "<string>",
      "pseudonym": "<string>",
      "displayUsernamePublic": true,
      "bio": "<string>",
      "isMod": true,
      "isCreator": true,
      "proxyWallet": "<string>",
      "baseAddress": "<string>",
      "profileImage": "<string>",
      "profileImageOptimized": {
        "id": "<string>",
        "imageUrlSource": "<string>",
        "imageUrlOptimized": "<string>",
        "imageSizeKbSource": 123,
        "imageSizeKbOptimized": 123,
        "imageOptimizedComplete": true,
        "imageOptimizedLastUpdated": "<string>",
        "relID": 123,
        "field": "<string>",
        "relname": "<string>"
      },
      "positions": [
        {
          "tokenId": "<string>",
          "positionSize": "<string>"
        }
      ]
    },
    "reactions": [
      {
        "id": "<string>",
        "commentID": 123,
        "reactionType": "<string>",
        "icon": "<string>",
        "userAddress": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "profile": {
          "name": "<string>",
          "pseudonym": "<string>",
          "displayUsernamePublic": true,
          "bio": "<string>",
          "isMod": true,
          "isCreator": true,
          "proxyWallet": "<string>",
          "baseAddress": "<string>",
          "profileImage": "<string>",
          "profileImageOptimized": {
            "id": "<string>",
            "imageUrlSource": "<string>",
            "imageUrlOptimized": "<string>",
            "imageSizeKbSource": 123,
            "imageSizeKbOptimized": 123,
            "imageOptimizedComplete": true,
            "imageOptimizedLastUpdated": "<string>",
            "relID": 123,
            "field": "<string>",
            "relname": "<string>"
          },
          "positions": [
            {
              "tokenId": "<string>",
              "positionSize": "<string>"
            }
          ]
        }
      }
    ],
    "reportCount": 123,
    "reactionCount": 123
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

[​](#parameter-parent-entity-type)

parent\_entity\_type

enum<string>

Available options:

`Event`,

`Series`,

`market`

[​](#parameter-parent-entity-id)

parent\_entity\_id

integer

[​](#parameter-get-positions)

get\_positions

boolean

[​](#parameter-holders-only)

holders\_only

boolean

#### Response

200 - application/json

List of comments

[​](#response-items-id)

id

string

[​](#response-items-body-one-of-0)

body

string | null

[​](#response-items-parent-entity-type-one-of-0)

parentEntityType

string | null

[​](#response-items-parent-entity-id-one-of-0)

parentEntityID

integer | null

[​](#response-items-parent-comment-id-one-of-0)

parentCommentID

string | null

[​](#response-items-user-address-one-of-0)

userAddress

string | null

[​](#response-items-reply-address-one-of-0)

replyAddress

string | null

[​](#response-items-created-at-one-of-0)

createdAt

string<date-time> | null

[​](#response-items-updated-at-one-of-0)

updatedAt

string<date-time> | null

[​](#response-items-profile)

profile

object

Show child attributes

[​](#response-items-reactions)

reactions

object[]

Show child attributes

[​](#response-items-report-count-one-of-0)

reportCount

integer | null

[​](#response-items-reaction-count-one-of-0)

reactionCount

integer | null

[Get series by id](/api-reference/series/get-series-by-id)[Get comments by comment id](/api-reference/comments/get-comments-by-comment-id)

⌘I