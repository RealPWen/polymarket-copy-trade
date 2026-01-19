# Source: https://docs.polymarket.com/developers/RTDS/RTDS-comments

On this page

* [Overview](#overview)
* [Subscription Details](#subscription-details)
* [Subscription Message](#subscription-message)
* [Message Format](#message-format)
* [Message Types](#message-types)
* [comment\_created](#comment-created)
* [comment\_removed](#comment-removed)
* [reaction\_created](#reaction-created)
* [reaction\_removed](#reaction-removed)
* [Payload Fields](#payload-fields)
* [Profile Object Fields](#profile-object-fields)
* [Parent Entity Types](#parent-entity-types)
* [Example Messages](#example-messages)
* [New Comment Created](#new-comment-created)
* [Reply to Existing Comment](#reply-to-existing-comment)
* [Comment Hierarchy](#comment-hierarchy)
* [Use Cases](#use-cases)
* [Content](#content)
* [Notes](#notes)

Polymarket provides a Typescript client for interacting with this streaming service. [Download and view it’s documentation here](https://github.com/Polymarket/real-time-data-client)

## [​](#overview) Overview

The comments subscription provides real-time updates for comment-related events on the Polymarket platform. This includes new comments being created, as well as other comment interactions like reactions and replies.

## [​](#subscription-details) Subscription Details

* **Topic**: `comments`
* **Type**: `comment_created` (and potentially other comment event types like `reaction_created`)
* **Authentication**: May require Gamma authentication for user-specific data
* **Filters**: Optional (can filter by specific comment IDs, users, or events)

## [​](#subscription-message) Subscription Message

Copy

Ask AI

```
{
  "action": "subscribe",
  "subscriptions": [
    {
      "topic": "comments", 
      "type": "comment_created"
    }
  ]
}
```

## [​](#message-format) Message Format

When subscribed to comments, you’ll receive messages with the following structure:

Copy

Ask AI

```
{
  "topic": "comments",
  "type": "comment_created",
  "timestamp": 1753454975808,
  "payload": {
    "body": "do you know what the term encircle means? it means to surround from all sides, Russia has present on only 1 side, that's the opposite of an encirclement",
    "createdAt": "2025-07-25T14:49:35.801298Z",
    "id": "1763355",
    "parentCommentID": "1763325",
    "parentEntityID": 18396,
    "parentEntityType": "Event",
    "profile": {
      "baseAddress": "0xce533188d53a16ed580fd5121dedf166d3482677",
      "displayUsernamePublic": true,
      "name": "salted.caramel",
      "proxyWallet": "0x4ca749dcfa93c87e5ee23e2d21ff4422c7a4c1ee",
      "pseudonym": "Adored-Disparity"
    },
    "reactionCount": 0,
    "replyAddress": "0x0bda5d16f76cd1d3485bcc7a44bc6fa7db004cdd",
    "reportCount": 0,
    "userAddress": "0xce533188d53a16ed580fd5121dedf166d3482677"
  }
}
```

## [​](#message-types) Message Types

### [​](#comment-created) comment\_created

Triggered when a user creates a new comment on an event or in reply to another comment.

### [​](#comment-removed) comment\_removed

Triggered when a comment is removed or deleted.

### [​](#reaction-created) reaction\_created

Triggered when a user adds a reaction to an existing comment.

### [​](#reaction-removed) reaction\_removed

Triggered when a reaction is removed from a comment.

## [​](#payload-fields) Payload Fields

| Field | Type | Description |
| --- | --- | --- |
| `body` | string | The text content of the comment |
| `createdAt` | string | ISO 8601 timestamp when the comment was created |
| `id` | string | Unique identifier for this comment |
| `parentCommentID` | string | ID of the parent comment if this is a reply (null for top-level comments) |
| `parentEntityID` | number | ID of the parent entity (event, market, etc.) |
| `parentEntityType` | string | Type of parent entity (e.g., “Event”, “Market”) |
| `profile` | object | Profile information of the user who created the comment |
| `reactionCount` | number | Current number of reactions on this comment |
| `replyAddress` | string | Polygon address for replies (may be different from userAddress) |
| `reportCount` | number | Current number of reports on this comment |
| `userAddress` | string | Polygon address of the user who created the comment |

### [​](#profile-object-fields) Profile Object Fields

| Field | Type | Description |
| --- | --- | --- |
| `baseAddress` | string | User profile address |
| `displayUsernamePublic` | boolean | Whether the username should be displayed publicly |
| `name` | string | User’s display name |
| `proxyWallet` | string | Proxy wallet address used for transactions |
| `pseudonym` | string | Generated pseudonym for the user |

## [​](#parent-entity-types) Parent Entity Types

The following parent entity types are supported:

* `Event` - Comments on prediction events
* `Market` - Comments on specific markets
* Additional entity types may be available

## [​](#example-messages) Example Messages

### [​](#new-comment-created) New Comment Created

Copy

Ask AI

```
{
  "topic": "comments",
  "type": "comment_created",
  "timestamp": 1753454975808,
  "payload": {
    "body": "do you know what the term encircle means? it means to surround from all sides, Russia has present on only 1 side, that's the opposite of an encirclement",
    "createdAt": "2025-07-25T14:49:35.801298Z",
    "id": "1763355",
    "parentCommentID": "1763325",
    "parentEntityID": 18396,
    "parentEntityType": "Event",
    "profile": {
      "baseAddress": "0xce533188d53a16ed580fd5121dedf166d3482677",
      "displayUsernamePublic": true,
      "name": "salted.caramel",
      "proxyWallet": "0x4ca749dcfa93c87e5ee23e2d21ff4422c7a4c1ee",
      "pseudonym": "Adored-Disparity"
    },
    "reactionCount": 0,
    "replyAddress": "0x0bda5d16f76cd1d3485bcc7a44bc6fa7db004cdd",
    "reportCount": 0,
    "userAddress": "0xce533188d53a16ed580fd5121dedf166d3482677"
  }
}
```

### [​](#reply-to-existing-comment) Reply to Existing Comment

Copy

Ask AI

```
{
  "topic": "comments",
  "type": "comment_created",
  "timestamp": 1753454985123,
  "payload": {
    "body": "That's a good point about the definition of encirclement.",
    "createdAt": "2025-07-25T14:49:45.120000Z",
    "id": "1763356",
    "parentCommentID": "1763355",
    "parentEntityID": 18396,
    "parentEntityType": "Event",
    "profile": {
      "baseAddress": "0x1234567890abcdef1234567890abcdef12345678",
      "displayUsernamePublic": true,
      "name": "trader",
      "proxyWallet": "0x9876543210fedcba9876543210fedcba98765432",
      "pseudonym": "Bright-Analysis"
    },
    "reactionCount": 0,
    "replyAddress": "0x0bda5d16f76cd1d3485bcc7a44bc6fa7db004cdd",
    "reportCount": 0,
    "userAddress": "0x1234567890abcdef1234567890abcdef12345678"
  }
}
```

## [​](#comment-hierarchy) Comment Hierarchy

Comments support nested threading:

* **Top-level comments**: `parentCommentID` is null or empty
* **Reply comments**: `parentCommentID` contains the ID of the parent comment
* All comments are associated with a `parentEntityID` and `parentEntityType`

## [​](#use-cases) Use Cases

* Real-time comment feed displays
* Discussion thread monitoring
* Community sentiment analysis

## [​](#content) Content

* Comments include `reactionCount` and `reportCount`
* Comment body contains the full text content

## [​](#notes) Notes

* The `createdAt` timestamp uses ISO 8601 format with timezone information
* The outer `timestamp` field represents when the WebSocket message was sent
* User profiles include both primary addresses and proxy wallet addresses

[RTDS Crypto Prices](/developers/RTDS/RTDS-crypto-prices)[Overview](/developers/gamma-markets-api/overview)

⌘I