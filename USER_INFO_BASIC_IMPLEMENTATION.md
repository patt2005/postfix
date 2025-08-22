# User Info Basic Scope Implementation

## Overview
Updated the application to work exclusively with TikTok's `user.info.basic` permission scope, which provides limited user profile information.

## Available Fields with user.info.basic
According to TikTok API documentation, the basic scope only provides:
- `open_id` - Unique identifier for the user
- `union_id` - Union ID across TikTok apps
- `avatar_url` - User's profile picture URL
- `display_name` - User's display name

## Fields NOT Available with Basic Scope
The following fields require additional permissions and are NOT available:
- `username` - Actual @username
- `follower_count` - Number of followers
- `following_count` - Number of following
- `likes_count` - Total likes received
- `video_count` - Total videos posted
- `bio_description` - User bio
- `is_verified` - Verification status
- `profile_deep_link` - Deep link to profile

## Implementation Changes

### 1. Display API (`display_api.py`)
- **GET /api/user/profile/<account_id>**
  - Only requests: `open_id,union_id,avatar_url,display_name`
  - Uses stored database values for stats (followers, likes, etc.)
  - Returns '--' or 0 for unavailable fields

### 2. OAuth Callback (`app.py`)
- **Fields requested**: Only basic fields
- **Username handling**: Uses `display_name` as username fallback
- **Stats**: Sets to 0 for new accounts
- **Updates**: Only updates avatar and display_name on existing accounts

### 3. Dashboard UI (`dashboard.html`)
- **Profile display**: Shows avatar and display name
- **Stats display**: Shows '--' when stats are 0 or unavailable
- **Graceful degradation**: UI works without extended profile data

## API Request Example

### Request
```bash
curl -L -X GET 'https://open.tiktokapis.com/v2/user/info/?fields=open_id,union_id,avatar_url,display_name' \
-H 'Authorization: Bearer act.example12345Example12345Example'
```

### Response
```json
{
  "data": {
    "user": {
      "avatar_url": "https://p19-sign.tiktokcdn-us.com/tos-useast5-avt-0068-tx/example.jpeg",
      "open_id": "723f24d7-e717-40f8-a2b6-cb8464cd23b4",
      "union_id": "c9c60f44-a68e-4f5d-84dd-ce22faeb0ba1",
      "display_name": "Tik Toker"
    }
  },
  "error": {
    "code": "ok",
    "message": "",
    "log_id": "20220829194722CBE87ED59D524E727021"
  }
}
```

## User Experience

### What Users See:
1. **Profile Section**: 
   - Avatar image (if available)
   - Display name
   - Stats show as '--' instead of numbers

2. **Account Dropdown**:
   - Shows display name as identifier
   - Avatar shown in account info panel

3. **Account Management**:
   - Can add/remove accounts
   - Can refresh to update avatar and display name
   - Stats remain as stored values or '--'

### Limitations:
- Cannot display real follower counts
- Cannot show verification badges
- Username shows as display name
- No bio description available

## Database Handling
- Stores whatever data is available during OAuth
- Preserves existing stats if account already exists
- Uses display_name as username fallback
- Soft defaults to 0 for missing stats

## Testing
Run `python3 test_basic_scope.py` to verify:
- ✓ Display API uses only basic fields
- ✓ OAuth callback uses only basic fields  
- ✓ Username handling with display_name fallback
- ✓ Dashboard handles missing stats gracefully

## Compliance
This implementation fully complies with TikTok's API permissions:
- Only requests fields available with granted scope
- Handles missing data gracefully
- Provides functional UI despite limitations
- Follows TikTok's API best practices