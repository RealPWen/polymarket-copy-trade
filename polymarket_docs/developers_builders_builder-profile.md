# Source: https://docs.polymarket.com/developers/builders/builder-profile

On this page

* [Accessing Your Builder Profile](#accessing-your-builder-profile)
* [Builder Profile Settings](#builder-profile-settings)
* [Customize Your Builder Identity](#customize-your-builder-identity)
* [View Your Builder Information](#view-your-builder-information)
* [Builder API Keys](#builder-api-keys)
* [Creating API Keys](#creating-api-keys)
* [Managing API Keys](#managing-api-keys)
* [Next Steps](#next-steps)

## [​](#accessing-your-builder-profile) Accessing Your Builder Profile

## Direct Link

Go to [polymarket.com/settings?tab=builder](https://polymarket.com/settings?tab=builder)

## From Profile Menu

Click your profile image and Select “Builders”

---

## [​](#builder-profile-settings) Builder Profile Settings

![Builder Settings Page](https://mintcdn.com/polymarket-292d1b1b/Quu9lXyXHL-5rjVX/images/builder-profile-image.png?fit=max&auto=format&n=Quu9lXyXHL-5rjVX&q=85&s=67176050b411016e3bfea47bc6fd8fbb)

### [​](#customize-your-builder-identity) Customize Your Builder Identity

* **Profile Picture**: Upload a custom image for the [Builder Leaderboard](https://builders.polymarket.com/)
* **Builder Name**: Set the name displayed publicly on the leaderboard

### [​](#view-your-builder-information) View Your Builder Information

* **Builder Address**: Your unique builder address for identification
* **Creation Date**: When your builder account was created
* **Current Tier**: Your rate limit tier (Unverified or Verified)

---

## [​](#builder-api-keys) Builder API Keys

Builder API keys are required to access the relayer and for CLOB order attribution.

### [​](#creating-api-keys) Creating API Keys

In the **Builder Keys** section of your profile’s **Builder Settings**:

1. View existing API keys with their creation dates and status
2. Click **”+ Create New”** to generate a new API key

Each API key includes:

| Credential | Description |
| --- | --- |
| `apiKey` | Your builder API key identifier |
| `secret` | Secret key for signing requests |
| `passphrase` | Additional authentication passphrase |

### [​](#managing-api-keys) Managing API Keys

* **Multiple Keys**: Create separate keys for different environments
* **Active Status**: Keys show “ACTIVE” when operational

---

## [​](#next-steps) Next Steps

[## Order Attribution

Start attributing customer orders to your account](/developers/builders/order-attribution)[## Builder Leaderboard

View your public profile and stats](https://builders.polymarket.com/)

[Builder Tiers](/developers/builders/builder-tiers)[Order Attribution](/developers/builders/order-attribution)

⌘I