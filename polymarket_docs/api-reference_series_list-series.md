# Source: https://docs.polymarket.com/api-reference/series/list-series

List series

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/series
```

200

Copy

Ask AI

```
[
  {
    "id": "<string>",
    "ticker": "<string>",
    "slug": "<string>",
    "title": "<string>",
    "subtitle": "<string>",
    "seriesType": "<string>",
    "recurrence": "<string>",
    "description": "<string>",
    "image": "<string>",
    "icon": "<string>",
    "layout": "<string>",
    "active": true,
    "closed": true,
    "archived": true,
    "new": true,
    "featured": true,
    "restricted": true,
    "isTemplate": true,
    "templateVariables": true,
    "publishedAt": "<string>",
    "createdBy": "<string>",
    "updatedBy": "<string>",
    "createdAt": "2023-11-07T05:31:56Z",
    "updatedAt": "2023-11-07T05:31:56Z",
    "commentsEnabled": true,
    "competitive": "<string>",
    "volume24hr": 123,
    "volume": 123,
    "liquidity": 123,
    "startDate": "2023-11-07T05:31:56Z",
    "pythTokenID": "<string>",
    "cgAssetName": "<string>",
    "score": 123,
    "events": [
      {
        "id": "<string>",
        "ticker": "<string>",
        "slug": "<string>",
        "title": "<string>",
        "subtitle": "<string>",
        "description": "<string>",
        "resolutionSource": "<string>",
        "startDate": "2023-11-07T05:31:56Z",
        "creationDate": "2023-11-07T05:31:56Z",
        "endDate": "2023-11-07T05:31:56Z",
        "image": "<string>",
        "icon": "<string>",
        "active": true,
        "closed": true,
        "archived": true,
        "new": true,
        "featured": true,
        "restricted": true,
        "liquidity": 123,
        "volume": 123,
        "openInterest": 123,
        "sortBy": "<string>",
        "category": "<string>",
        "subcategory": "<string>",
        "isTemplate": true,
        "templateVariables": "<string>",
        "published_at": "<string>",
        "createdBy": "<string>",
        "updatedBy": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z",
        "commentsEnabled": true,
        "competitive": 123,
        "volume24hr": 123,
        "volume1wk": 123,
        "volume1mo": 123,
        "volume1yr": 123,
        "featuredImage": "<string>",
        "disqusThread": "<string>",
        "parentEvent": "<string>",
        "enableOrderBook": true,
        "liquidityAmm": 123,
        "liquidityClob": 123,
        "negRisk": true,
        "negRiskMarketID": "<string>",
        "negRiskFeeBips": 123,
        "commentCount": 123,
        "imageOptimized": {
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
        "iconOptimized": {
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
        "featuredImageOptimized": {
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
        "subEvents": [
          "<string>"
        ],
        "markets": [
          {
            "id": "<string>",
            "question": "<string>",
            "conditionId": "<string>",
            "slug": "<string>",
            "twitterCardImage": "<string>",
            "resolutionSource": "<string>",
            "endDate": "2023-11-07T05:31:56Z",
            "category": "<string>",
            "ammType": "<string>",
            "liquidity": "<string>",
            "sponsorName": "<string>",
            "sponsorImage": "<string>",
            "startDate": "2023-11-07T05:31:56Z",
            "xAxisValue": "<string>",
            "yAxisValue": "<string>",
            "denominationToken": "<string>",
            "fee": "<string>",
            "image": "<string>",
            "icon": "<string>",
            "lowerBound": "<string>",
            "upperBound": "<string>",
            "description": "<string>",
            "outcomes": "<string>",
            "outcomePrices": "<string>",
            "volume": "<string>",
            "active": true,
            "marketType": "<string>",
            "formatType": "<string>",
            "lowerBoundDate": "<string>",
            "upperBoundDate": "<string>",
            "closed": true,
            "marketMakerAddress": "<string>",
            "createdBy": 123,
            "updatedBy": 123,
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z",
            "closedTime": "<string>",
            "wideFormat": true,
            "new": true,
            "mailchimpTag": "<string>",
            "featured": true,
            "archived": true,
            "resolvedBy": "<string>",
            "restricted": true,
            "marketGroup": 123,
            "groupItemTitle": "<string>",
            "groupItemThreshold": "<string>",
            "questionID": "<string>",
            "umaEndDate": "<string>",
            "enableOrderBook": true,
            "orderPriceMinTickSize": 123,
            "orderMinSize": 123,
            "umaResolutionStatus": "<string>",
            "curationOrder": 123,
            "volumeNum": 123,
            "liquidityNum": 123,
            "endDateIso": "<string>",
            "startDateIso": "<string>",
            "umaEndDateIso": "<string>",
            "hasReviewedDates": true,
            "readyForCron": true,
            "commentsEnabled": true,
            "volume24hr": 123,
            "volume1wk": 123,
            "volume1mo": 123,
            "volume1yr": 123,
            "gameStartTime": "<string>",
            "secondsDelay": 123,
            "clobTokenIds": "<string>",
            "disqusThread": "<string>",
            "shortOutcomes": "<string>",
            "teamAID": "<string>",
            "teamBID": "<string>",
            "umaBond": "<string>",
            "umaReward": "<string>",
            "fpmmLive": true,
            "volume24hrAmm": 123,
            "volume1wkAmm": 123,
            "volume1moAmm": 123,
            "volume1yrAmm": 123,
            "volume24hrClob": 123,
            "volume1wkClob": 123,
            "volume1moClob": 123,
            "volume1yrClob": 123,
            "volumeAmm": 123,
            "volumeClob": 123,
            "liquidityAmm": 123,
            "liquidityClob": 123,
            "makerBaseFee": 123,
            "takerBaseFee": 123,
            "customLiveness": 123,
            "acceptingOrders": true,
            "notificationsEnabled": true,
            "score": 123,
            "imageOptimized": {
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
            "iconOptimized": {
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
            "events": "<array>",
            "categories": [
              {
                "id": "<string>",
                "label": "<string>",
                "parentCategory": "<string>",
                "slug": "<string>",
                "publishedAt": "<string>",
                "createdBy": "<string>",
                "updatedBy": "<string>",
                "createdAt": "2023-11-07T05:31:56Z",
                "updatedAt": "2023-11-07T05:31:56Z"
              }
            ],
            "tags": [
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
            ],
            "creator": "<string>",
            "ready": true,
            "funded": true,
            "pastSlugs": "<string>",
            "readyTimestamp": "2023-11-07T05:31:56Z",
            "fundedTimestamp": "2023-11-07T05:31:56Z",
            "acceptingOrdersTimestamp": "2023-11-07T05:31:56Z",
            "competitive": 123,
            "rewardsMinSize": 123,
            "rewardsMaxSpread": 123,
            "spread": 123,
            "automaticallyResolved": true,
            "oneDayPriceChange": 123,
            "oneHourPriceChange": 123,
            "oneWeekPriceChange": 123,
            "oneMonthPriceChange": 123,
            "oneYearPriceChange": 123,
            "lastTradePrice": 123,
            "bestBid": 123,
            "bestAsk": 123,
            "automaticallyActive": true,
            "clearBookOnStart": true,
            "chartColor": "<string>",
            "seriesColor": "<string>",
            "showGmpSeries": true,
            "showGmpOutcome": true,
            "manualActivation": true,
            "negRiskOther": true,
            "gameId": "<string>",
            "groupItemRange": "<string>",
            "sportsMarketType": "<string>",
            "line": 123,
            "umaResolutionStatuses": "<string>",
            "pendingDeployment": true,
            "deploying": true,
            "deployingTimestamp": "2023-11-07T05:31:56Z",
            "scheduledDeploymentTimestamp": "2023-11-07T05:31:56Z",
            "rfqEnabled": true,
            "eventStartTime": "2023-11-07T05:31:56Z"
          }
        ],
        "series": "<array>",
        "categories": [
          {
            "id": "<string>",
            "label": "<string>",
            "parentCategory": "<string>",
            "slug": "<string>",
            "publishedAt": "<string>",
            "createdBy": "<string>",
            "updatedBy": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z"
          }
        ],
        "collections": [
          {
            "id": "<string>",
            "ticker": "<string>",
            "slug": "<string>",
            "title": "<string>",
            "subtitle": "<string>",
            "collectionType": "<string>",
            "description": "<string>",
            "tags": "<string>",
            "image": "<string>",
            "icon": "<string>",
            "headerImage": "<string>",
            "layout": "<string>",
            "active": true,
            "closed": true,
            "archived": true,
            "new": true,
            "featured": true,
            "restricted": true,
            "isTemplate": true,
            "templateVariables": "<string>",
            "publishedAt": "<string>",
            "createdBy": "<string>",
            "updatedBy": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z",
            "commentsEnabled": true,
            "imageOptimized": {
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
            "iconOptimized": {
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
            "headerImageOptimized": {
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
            }
          }
        ],
        "tags": [
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
        ],
        "cyom": true,
        "closedTime": "2023-11-07T05:31:56Z",
        "showAllOutcomes": true,
        "showMarketImages": true,
        "automaticallyResolved": true,
        "enableNegRisk": true,
        "automaticallyActive": true,
        "eventDate": "<string>",
        "startTime": "2023-11-07T05:31:56Z",
        "eventWeek": 123,
        "seriesSlug": "<string>",
        "score": "<string>",
        "elapsed": "<string>",
        "period": "<string>",
        "live": true,
        "ended": true,
        "finishedTimestamp": "2023-11-07T05:31:56Z",
        "gmpChartMode": "<string>",
        "eventCreators": [
          {
            "id": "<string>",
            "creatorName": "<string>",
            "creatorHandle": "<string>",
            "creatorUrl": "<string>",
            "creatorImage": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z"
          }
        ],
        "tweetCount": 123,
        "chats": [
          {
            "id": "<string>",
            "channelId": "<string>",
            "channelName": "<string>",
            "channelImage": "<string>",
            "live": true,
            "startTime": "2023-11-07T05:31:56Z",
            "endTime": "2023-11-07T05:31:56Z"
          }
        ],
        "featuredOrder": 123,
        "estimateValue": true,
        "cantEstimate": true,
        "estimatedValue": "<string>",
        "templates": [
          {
            "id": "<string>",
            "eventTitle": "<string>",
            "eventSlug": "<string>",
            "eventImage": "<string>",
            "marketTitle": "<string>",
            "description": "<string>",
            "resolutionSource": "<string>",
            "negRisk": true,
            "sortBy": "<string>",
            "showMarketImages": true,
            "seriesSlug": "<string>",
            "outcomes": "<string>"
          }
        ],
        "spreadsMainLine": 123,
        "totalsMainLine": 123,
        "carouselMap": "<string>",
        "pendingDeployment": true,
        "deploying": true,
        "deployingTimestamp": "2023-11-07T05:31:56Z",
        "scheduledDeploymentTimestamp": "2023-11-07T05:31:56Z",
        "gameStatus": "<string>"
      }
    ],
    "collections": [
      {
        "id": "<string>",
        "ticker": "<string>",
        "slug": "<string>",
        "title": "<string>",
        "subtitle": "<string>",
        "collectionType": "<string>",
        "description": "<string>",
        "tags": "<string>",
        "image": "<string>",
        "icon": "<string>",
        "headerImage": "<string>",
        "layout": "<string>",
        "active": true,
        "closed": true,
        "archived": true,
        "new": true,
        "featured": true,
        "restricted": true,
        "isTemplate": true,
        "templateVariables": "<string>",
        "publishedAt": "<string>",
        "createdBy": "<string>",
        "updatedBy": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z",
        "commentsEnabled": true,
        "imageOptimized": {
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
        "iconOptimized": {
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
        "headerImageOptimized": {
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
        }
      }
    ],
    "categories": [
      {
        "id": "<string>",
        "label": "<string>",
        "parentCategory": "<string>",
        "slug": "<string>",
        "publishedAt": "<string>",
        "createdBy": "<string>",
        "updatedBy": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z"
      }
    ],
    "tags": [
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
    ],
    "commentCount": 123,
    "chats": [
      {
        "id": "<string>",
        "channelId": "<string>",
        "channelName": "<string>",
        "channelImage": "<string>",
        "live": true,
        "startTime": "2023-11-07T05:31:56Z",
        "endTime": "2023-11-07T05:31:56Z"
      }
    ]
  }
]
```

GET

/

series

Try it

List series

cURL

Copy

Ask AI

```
curl --request GET \
  --url https://gamma-api.polymarket.com/series
```

200

Copy

Ask AI

```
[
  {
    "id": "<string>",
    "ticker": "<string>",
    "slug": "<string>",
    "title": "<string>",
    "subtitle": "<string>",
    "seriesType": "<string>",
    "recurrence": "<string>",
    "description": "<string>",
    "image": "<string>",
    "icon": "<string>",
    "layout": "<string>",
    "active": true,
    "closed": true,
    "archived": true,
    "new": true,
    "featured": true,
    "restricted": true,
    "isTemplate": true,
    "templateVariables": true,
    "publishedAt": "<string>",
    "createdBy": "<string>",
    "updatedBy": "<string>",
    "createdAt": "2023-11-07T05:31:56Z",
    "updatedAt": "2023-11-07T05:31:56Z",
    "commentsEnabled": true,
    "competitive": "<string>",
    "volume24hr": 123,
    "volume": 123,
    "liquidity": 123,
    "startDate": "2023-11-07T05:31:56Z",
    "pythTokenID": "<string>",
    "cgAssetName": "<string>",
    "score": 123,
    "events": [
      {
        "id": "<string>",
        "ticker": "<string>",
        "slug": "<string>",
        "title": "<string>",
        "subtitle": "<string>",
        "description": "<string>",
        "resolutionSource": "<string>",
        "startDate": "2023-11-07T05:31:56Z",
        "creationDate": "2023-11-07T05:31:56Z",
        "endDate": "2023-11-07T05:31:56Z",
        "image": "<string>",
        "icon": "<string>",
        "active": true,
        "closed": true,
        "archived": true,
        "new": true,
        "featured": true,
        "restricted": true,
        "liquidity": 123,
        "volume": 123,
        "openInterest": 123,
        "sortBy": "<string>",
        "category": "<string>",
        "subcategory": "<string>",
        "isTemplate": true,
        "templateVariables": "<string>",
        "published_at": "<string>",
        "createdBy": "<string>",
        "updatedBy": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z",
        "commentsEnabled": true,
        "competitive": 123,
        "volume24hr": 123,
        "volume1wk": 123,
        "volume1mo": 123,
        "volume1yr": 123,
        "featuredImage": "<string>",
        "disqusThread": "<string>",
        "parentEvent": "<string>",
        "enableOrderBook": true,
        "liquidityAmm": 123,
        "liquidityClob": 123,
        "negRisk": true,
        "negRiskMarketID": "<string>",
        "negRiskFeeBips": 123,
        "commentCount": 123,
        "imageOptimized": {
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
        "iconOptimized": {
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
        "featuredImageOptimized": {
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
        "subEvents": [
          "<string>"
        ],
        "markets": [
          {
            "id": "<string>",
            "question": "<string>",
            "conditionId": "<string>",
            "slug": "<string>",
            "twitterCardImage": "<string>",
            "resolutionSource": "<string>",
            "endDate": "2023-11-07T05:31:56Z",
            "category": "<string>",
            "ammType": "<string>",
            "liquidity": "<string>",
            "sponsorName": "<string>",
            "sponsorImage": "<string>",
            "startDate": "2023-11-07T05:31:56Z",
            "xAxisValue": "<string>",
            "yAxisValue": "<string>",
            "denominationToken": "<string>",
            "fee": "<string>",
            "image": "<string>",
            "icon": "<string>",
            "lowerBound": "<string>",
            "upperBound": "<string>",
            "description": "<string>",
            "outcomes": "<string>",
            "outcomePrices": "<string>",
            "volume": "<string>",
            "active": true,
            "marketType": "<string>",
            "formatType": "<string>",
            "lowerBoundDate": "<string>",
            "upperBoundDate": "<string>",
            "closed": true,
            "marketMakerAddress": "<string>",
            "createdBy": 123,
            "updatedBy": 123,
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z",
            "closedTime": "<string>",
            "wideFormat": true,
            "new": true,
            "mailchimpTag": "<string>",
            "featured": true,
            "archived": true,
            "resolvedBy": "<string>",
            "restricted": true,
            "marketGroup": 123,
            "groupItemTitle": "<string>",
            "groupItemThreshold": "<string>",
            "questionID": "<string>",
            "umaEndDate": "<string>",
            "enableOrderBook": true,
            "orderPriceMinTickSize": 123,
            "orderMinSize": 123,
            "umaResolutionStatus": "<string>",
            "curationOrder": 123,
            "volumeNum": 123,
            "liquidityNum": 123,
            "endDateIso": "<string>",
            "startDateIso": "<string>",
            "umaEndDateIso": "<string>",
            "hasReviewedDates": true,
            "readyForCron": true,
            "commentsEnabled": true,
            "volume24hr": 123,
            "volume1wk": 123,
            "volume1mo": 123,
            "volume1yr": 123,
            "gameStartTime": "<string>",
            "secondsDelay": 123,
            "clobTokenIds": "<string>",
            "disqusThread": "<string>",
            "shortOutcomes": "<string>",
            "teamAID": "<string>",
            "teamBID": "<string>",
            "umaBond": "<string>",
            "umaReward": "<string>",
            "fpmmLive": true,
            "volume24hrAmm": 123,
            "volume1wkAmm": 123,
            "volume1moAmm": 123,
            "volume1yrAmm": 123,
            "volume24hrClob": 123,
            "volume1wkClob": 123,
            "volume1moClob": 123,
            "volume1yrClob": 123,
            "volumeAmm": 123,
            "volumeClob": 123,
            "liquidityAmm": 123,
            "liquidityClob": 123,
            "makerBaseFee": 123,
            "takerBaseFee": 123,
            "customLiveness": 123,
            "acceptingOrders": true,
            "notificationsEnabled": true,
            "score": 123,
            "imageOptimized": {
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
            "iconOptimized": {
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
            "events": "<array>",
            "categories": [
              {
                "id": "<string>",
                "label": "<string>",
                "parentCategory": "<string>",
                "slug": "<string>",
                "publishedAt": "<string>",
                "createdBy": "<string>",
                "updatedBy": "<string>",
                "createdAt": "2023-11-07T05:31:56Z",
                "updatedAt": "2023-11-07T05:31:56Z"
              }
            ],
            "tags": [
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
            ],
            "creator": "<string>",
            "ready": true,
            "funded": true,
            "pastSlugs": "<string>",
            "readyTimestamp": "2023-11-07T05:31:56Z",
            "fundedTimestamp": "2023-11-07T05:31:56Z",
            "acceptingOrdersTimestamp": "2023-11-07T05:31:56Z",
            "competitive": 123,
            "rewardsMinSize": 123,
            "rewardsMaxSpread": 123,
            "spread": 123,
            "automaticallyResolved": true,
            "oneDayPriceChange": 123,
            "oneHourPriceChange": 123,
            "oneWeekPriceChange": 123,
            "oneMonthPriceChange": 123,
            "oneYearPriceChange": 123,
            "lastTradePrice": 123,
            "bestBid": 123,
            "bestAsk": 123,
            "automaticallyActive": true,
            "clearBookOnStart": true,
            "chartColor": "<string>",
            "seriesColor": "<string>",
            "showGmpSeries": true,
            "showGmpOutcome": true,
            "manualActivation": true,
            "negRiskOther": true,
            "gameId": "<string>",
            "groupItemRange": "<string>",
            "sportsMarketType": "<string>",
            "line": 123,
            "umaResolutionStatuses": "<string>",
            "pendingDeployment": true,
            "deploying": true,
            "deployingTimestamp": "2023-11-07T05:31:56Z",
            "scheduledDeploymentTimestamp": "2023-11-07T05:31:56Z",
            "rfqEnabled": true,
            "eventStartTime": "2023-11-07T05:31:56Z"
          }
        ],
        "series": "<array>",
        "categories": [
          {
            "id": "<string>",
            "label": "<string>",
            "parentCategory": "<string>",
            "slug": "<string>",
            "publishedAt": "<string>",
            "createdBy": "<string>",
            "updatedBy": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z"
          }
        ],
        "collections": [
          {
            "id": "<string>",
            "ticker": "<string>",
            "slug": "<string>",
            "title": "<string>",
            "subtitle": "<string>",
            "collectionType": "<string>",
            "description": "<string>",
            "tags": "<string>",
            "image": "<string>",
            "icon": "<string>",
            "headerImage": "<string>",
            "layout": "<string>",
            "active": true,
            "closed": true,
            "archived": true,
            "new": true,
            "featured": true,
            "restricted": true,
            "isTemplate": true,
            "templateVariables": "<string>",
            "publishedAt": "<string>",
            "createdBy": "<string>",
            "updatedBy": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z",
            "commentsEnabled": true,
            "imageOptimized": {
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
            "iconOptimized": {
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
            "headerImageOptimized": {
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
            }
          }
        ],
        "tags": [
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
        ],
        "cyom": true,
        "closedTime": "2023-11-07T05:31:56Z",
        "showAllOutcomes": true,
        "showMarketImages": true,
        "automaticallyResolved": true,
        "enableNegRisk": true,
        "automaticallyActive": true,
        "eventDate": "<string>",
        "startTime": "2023-11-07T05:31:56Z",
        "eventWeek": 123,
        "seriesSlug": "<string>",
        "score": "<string>",
        "elapsed": "<string>",
        "period": "<string>",
        "live": true,
        "ended": true,
        "finishedTimestamp": "2023-11-07T05:31:56Z",
        "gmpChartMode": "<string>",
        "eventCreators": [
          {
            "id": "<string>",
            "creatorName": "<string>",
            "creatorHandle": "<string>",
            "creatorUrl": "<string>",
            "creatorImage": "<string>",
            "createdAt": "2023-11-07T05:31:56Z",
            "updatedAt": "2023-11-07T05:31:56Z"
          }
        ],
        "tweetCount": 123,
        "chats": [
          {
            "id": "<string>",
            "channelId": "<string>",
            "channelName": "<string>",
            "channelImage": "<string>",
            "live": true,
            "startTime": "2023-11-07T05:31:56Z",
            "endTime": "2023-11-07T05:31:56Z"
          }
        ],
        "featuredOrder": 123,
        "estimateValue": true,
        "cantEstimate": true,
        "estimatedValue": "<string>",
        "templates": [
          {
            "id": "<string>",
            "eventTitle": "<string>",
            "eventSlug": "<string>",
            "eventImage": "<string>",
            "marketTitle": "<string>",
            "description": "<string>",
            "resolutionSource": "<string>",
            "negRisk": true,
            "sortBy": "<string>",
            "showMarketImages": true,
            "seriesSlug": "<string>",
            "outcomes": "<string>"
          }
        ],
        "spreadsMainLine": 123,
        "totalsMainLine": 123,
        "carouselMap": "<string>",
        "pendingDeployment": true,
        "deploying": true,
        "deployingTimestamp": "2023-11-07T05:31:56Z",
        "scheduledDeploymentTimestamp": "2023-11-07T05:31:56Z",
        "gameStatus": "<string>"
      }
    ],
    "collections": [
      {
        "id": "<string>",
        "ticker": "<string>",
        "slug": "<string>",
        "title": "<string>",
        "subtitle": "<string>",
        "collectionType": "<string>",
        "description": "<string>",
        "tags": "<string>",
        "image": "<string>",
        "icon": "<string>",
        "headerImage": "<string>",
        "layout": "<string>",
        "active": true,
        "closed": true,
        "archived": true,
        "new": true,
        "featured": true,
        "restricted": true,
        "isTemplate": true,
        "templateVariables": "<string>",
        "publishedAt": "<string>",
        "createdBy": "<string>",
        "updatedBy": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z",
        "commentsEnabled": true,
        "imageOptimized": {
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
        "iconOptimized": {
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
        "headerImageOptimized": {
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
        }
      }
    ],
    "categories": [
      {
        "id": "<string>",
        "label": "<string>",
        "parentCategory": "<string>",
        "slug": "<string>",
        "publishedAt": "<string>",
        "createdBy": "<string>",
        "updatedBy": "<string>",
        "createdAt": "2023-11-07T05:31:56Z",
        "updatedAt": "2023-11-07T05:31:56Z"
      }
    ],
    "tags": [
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
    ],
    "commentCount": 123,
    "chats": [
      {
        "id": "<string>",
        "channelId": "<string>",
        "channelName": "<string>",
        "channelImage": "<string>",
        "live": true,
        "startTime": "2023-11-07T05:31:56Z",
        "endTime": "2023-11-07T05:31:56Z"
      }
    ]
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

[​](#parameter-slug)

slug

string[]

[​](#parameter-categories-ids)

categories\_ids

integer[]

[​](#parameter-categories-labels)

categories\_labels

string[]

[​](#parameter-closed)

closed

boolean

[​](#parameter-include-chat)

include\_chat

boolean

[​](#parameter-recurrence)

recurrence

string

#### Response

200 - application/json

List of series

[​](#response-items-id)

id

string

[​](#response-items-ticker-one-of-0)

ticker

string | null

[​](#response-items-slug-one-of-0)

slug

string | null

[​](#response-items-title-one-of-0)

title

string | null

[​](#response-items-subtitle-one-of-0)

subtitle

string | null

[​](#response-items-series-type-one-of-0)

seriesType

string | null

[​](#response-items-recurrence-one-of-0)

recurrence

string | null

[​](#response-items-description-one-of-0)

description

string | null

[​](#response-items-image-one-of-0)

image

string | null

[​](#response-items-icon-one-of-0)

icon

string | null

[​](#response-items-layout-one-of-0)

layout

string | null

[​](#response-items-active-one-of-0)

active

boolean | null

[​](#response-items-closed-one-of-0)

closed

boolean | null

[​](#response-items-archived-one-of-0)

archived

boolean | null

[​](#response-items-new-one-of-0)

new

boolean | null

[​](#response-items-featured-one-of-0)

featured

boolean | null

[​](#response-items-restricted-one-of-0)

restricted

boolean | null

[​](#response-items-is-template-one-of-0)

isTemplate

boolean | null

[​](#response-items-template-variables-one-of-0)

templateVariables

boolean | null

[​](#response-items-published-at-one-of-0)

publishedAt

string | null

[​](#response-items-created-by-one-of-0)

createdBy

string | null

[​](#response-items-updated-by-one-of-0)

updatedBy

string | null

[​](#response-items-created-at-one-of-0)

createdAt

string<date-time> | null

[​](#response-items-updated-at-one-of-0)

updatedAt

string<date-time> | null

[​](#response-items-comments-enabled-one-of-0)

commentsEnabled

boolean | null

[​](#response-items-competitive-one-of-0)

competitive

string | null

[​](#response-items-volume24hr-one-of-0)

volume24hr

number | null

[​](#response-items-volume-one-of-0)

volume

number | null

[​](#response-items-liquidity-one-of-0)

liquidity

number | null

[​](#response-items-start-date-one-of-0)

startDate

string<date-time> | null

[​](#response-items-pyth-token-id-one-of-0)

pythTokenID

string | null

[​](#response-items-cg-asset-name-one-of-0)

cgAssetName

string | null

[​](#response-items-score-one-of-0)

score

integer | null

[​](#response-items-events)

events

object[]

Show child attributes

[​](#response-items-collections)

collections

object[]

Show child attributes

[​](#response-items-categories)

categories

object[]

Show child attributes

[​](#response-items-tags)

tags

object[]

Show child attributes

[​](#response-items-comment-count-one-of-0)

commentCount

integer | null

[​](#response-items-chats)

chats

object[]

Show child attributes

[Get market by slug](/api-reference/markets/get-market-by-slug)[Get series by id](/api-reference/series/get-series-by-id)

⌘I