# Source: https://docs.polymarket.com/api-reference/profiles/get-public-profile-by-wallet-address

Get public profile by wallet address

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/public-profile
```

200

400

404

Copy

Ask AI

```
{
  "createdAt": "2023-11-07T05:31:56Z",
  "proxyWallet": "<string>",
  "profileImage": "<string>",
  "displayUsernamePublic": true,
  "bio": "<string>",
  "pseudonym": "<string>",
  "name": "<string>",
  "users": [
    {
      "id": "<string>",
      "creator": true,
      "mod": true
    }
  ],
  "xUsername": "<string>",
  "verifiedBadge": true
}
```

GET

/

public-profile

Try it

Get public profile by wallet address

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/public-profile
```

200

400

404

Copy

Ask AI

```
{
  "createdAt": "2023-11-07T05:31:56Z",
  "proxyWallet": "<string>",
  "profileImage": "<string>",
  "displayUsernamePublic": true,
  "bio": "<string>",
  "pseudonym": "<string>",
  "name": "<string>",
  "users": [
    {
      "id": "<string>",
      "creator": true,
      "mod": true
    }
  ],
  "xUsername": "<string>",
  "verifiedBadge": true
}
```

#### Query Parameters

[​](#parameter-address)

address

string

required

The wallet address (proxy wallet or user address)

#### Response

200

application/json

Public profile information

[​](#response-created-at-one-of-0)

createdAt

string<date-time> | null

ISO 8601 timestamp of when the profile was created

[​](#response-proxy-wallet-one-of-0)

proxyWallet

string | null

The proxy wallet address

[​](#response-profile-image-one-of-0)

profileImage

string<uri> | null

URL to the profile image

[​](#response-display-username-public-one-of-0)

displayUsernamePublic

boolean | null

Whether the username is displayed publicly

[​](#response-bio-one-of-0)

bio

string | null

Profile bio

[​](#response-pseudonym-one-of-0)

pseudonym

string | null

Auto-generated pseudonym

[​](#response-name-one-of-0)

name

string | null

User-chosen display name

[​](#response-users-one-of-0)

users

object[] | null

Array of associated user objects

Show child attributes

[​](#response-x-username-one-of-0)

xUsername

string | null

X (Twitter) username

[​](#response-verified-badge-one-of-0)

verifiedBadge

boolean | null

Whether the profile has a verified badge

[Get comments by user address](/api-reference/comments/get-comments-by-user-address)[Search markets, events, and profiles](/api-reference/search/search-markets-events-and-profiles)

⌘I