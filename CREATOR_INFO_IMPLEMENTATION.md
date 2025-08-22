# Creator Info Query API Implementation

## Overview
Implemented TikTok's `/v2/post/publish/creator_info/query/` endpoint to fetch user profile information. This endpoint works with the `video.publish` scope and provides more complete user information than the basic user info endpoint.

## API Endpoint Details

### Endpoint
```
POST https://open.tiktokapis.com/v2/post/publish/creator_info/query/
```

### Required Scope
- `video.publish` (which your app already has)

### Headers
```
Authorization: Bearer {access_token}
Content-Type: application/json; charset=UTF-8
```

## Data Available from Creator Info API

### User Information
- **creator_username**: The unique ID of the TikTok creator (e.g., "tiktok")
- **creator_nickname**: The display name of the creator (e.g., "TikTok Official")
- **creator_avatar_url**: URL to the creator's avatar (TTL: 2 hours)

### Privacy & Interaction Settings
- **privacy_level_options**: Available privacy levels for posts
- **comment_disabled**: Whether comments are disabled
- **duet_disabled**: Whether duets are disabled
- **stitch_disabled**: Whether stitches are disabled
- **max_video_post_duration_sec**: Maximum allowed video duration

## Implementation Changes

### 1. Display API (`display_api.py`)
- Updated `/api/user/profile/<account_id>` to use creator_info endpoint
- Fetches and stores:
  - Username (unique ID)
  - Display name (nickname)
  - Avatar URL
  - Privacy and interaction settings

### 2. OAuth Callback (`app.py`)
- First attempts to fetch user info via creator_info/query
- Falls back to basic user/info endpoint if needed
- Properly stores both username and display_name

### 3. New API Route
- Added `/api/creator/info/query/<account_id>` route
- Allows fetching creator info for any connected account
- Updates database with latest information

### 4. Dashboard UI
- Shows display name prominently
- Shows @username only if different from display name
- Handles both fields gracefully

## Example API Response

```json
{
  "data": {
    "creator_avatar_url": "https://lf16-tt4d.tiktokcdn.com/...",
    "creator_username": "tiktok",
    "creator_nickname": "TikTok Official",
    "privacy_level_options": [
      "PUBLIC_TO_EVERYONE",
      "MUTUAL_FOLLOW_FRIENDS", 
      "SELF_ONLY"
    ],
    "comment_disabled": false,
    "duet_disabled": false,
    "stitch_disabled": true,
    "max_video_post_duration_sec": 300
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": "202210112248442CB9319E1FB30C1073F3"
  }
}
```

## User Experience Improvements

### What Users Now See:
1. **Proper Username**: Actual TikTok username (unique ID)
2. **Display Name**: User's chosen display name/nickname
3. **Avatar**: Current profile picture with 2-hour TTL
4. **Privacy Options**: Available privacy settings for their account
5. **Video Limits**: Maximum video duration they can post

### Display Logic:
- If username and display_name are different: Shows "Display Name @username"
- If they're the same: Shows only the display name
- No more generic "User" placeholders

## Benefits

1. **Works with video.publish scope**: No need for additional permissions
2. **Complete user info**: Gets both unique ID and display name
3. **Fresh data**: Avatar URLs have 2-hour TTL, ensuring current images
4. **Privacy settings**: Knows what privacy options are available
5. **Posting limits**: Knows maximum video duration allowed

## Testing

Run `python3 test_creator_info.py` to verify:
- ✓ Creator info endpoint properly configured
- ✓ OAuth callback uses creator_info
- ✓ New routes added and working
- ✓ Dashboard handles both username and display_name

## Compliance

This implementation follows TikTok's API documentation exactly:
- Uses proper POST method with JSON content type
- Respects rate limits (20 requests per minute per user)
- Handles all response fields appropriately
- Updates UI based on available privacy options