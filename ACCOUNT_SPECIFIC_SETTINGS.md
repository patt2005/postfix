# Account-Specific Settings Implementation

## Overview
Implemented account-specific settings from the creator_info API response, ensuring each TikTok account uses its own max video duration, privacy options, and interaction restrictions as required by TikTok's Content Posting API.

## Key Requirements Met

### 1. Max Video Duration (Per Account)
- Each account has its own `max_video_post_duration_sec`
- Different users have different maximum video-duration privileges
- Dashboard displays account-specific max duration
- Video validation uses account-specific limits
- Upload prevention for videos exceeding account limit

### 2. Privacy Level Options (Per Account)
- Privacy dropdown shows only options available for the specific account
- Public accounts see: `PUBLIC_TO_EVERYONE`, `MUTUAL_FOLLOW_FRIENDS`, `SELF_ONLY`
- Private accounts see: `FOLLOWER_OF_CREATOR`, `MUTUAL_FOLLOW_FRIENDS`, `SELF_ONLY`
- Options are fetched from `privacy_level_options` in creator_info response

### 3. Interaction Settings (Per Account)
- Comment toggle disabled if `comment_disabled: true`
- Duet toggle disabled if `duet_disabled: true`
- Stitch toggle disabled if `stitch_disabled: true`
- Settings update when switching between accounts

## Implementation Details

### JavaScript Storage Structure
```javascript
accountCreatorInfo[accountId] = {
    max_video_duration: 300,  // Seconds
    privacy_level_options: ['PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'SELF_ONLY'],
    comment_disabled: false,
    duet_disabled: false,
    stitch_disabled: false
}
```

### Account Switching Behavior
When user switches accounts:
1. Fetches creator_info for the selected account
2. Updates max video duration display
3. Rebuilds privacy options dropdown
4. Updates interaction toggle states
5. Re-validates current video if selected

### Privacy Options Mapping
```javascript
const privacyLabels = {
    'PUBLIC_TO_EVERYONE': 'Public',
    'MUTUAL_FOLLOW_FRIENDS': 'Friends',
    'FOLLOWER_OF_CREATOR': 'Followers Only',
    'SELF_ONLY': 'Only Me'
}
```

## User Experience

### Video Duration
- Shows: "Max duration: 300 seconds" (account-specific)
- Error: "Video exceeds maximum allowed duration of 300 seconds for this account"
- Alert: "Maximum duration allowed for this account is 300 seconds"

### Privacy Selection
- Dropdown only shows options returned by creator_info API
- No hardcoded options - fully dynamic based on account
- Clear labels for each privacy level

### Interaction Controls
- Toggles automatically disable if restricted for account
- Visual feedback (opacity) for disabled options
- Prevents selection of unavailable interactions

## API Compliance

### Creator Info Response Used
```json
{
  "data": {
    "creator_avatar_url": "https://...",
    "creator_username": "tiktok",
    "creator_nickname": "TikTok Official",
    "privacy_level_options": ["PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "SELF_ONLY"],
    "comment_disabled": false,
    "duet_disabled": false,
    "stitch_disabled": true,
    "max_video_post_duration_sec": 300
  }
}
```

### Fields Utilized
- ✅ `max_video_post_duration_sec` - For video validation
- ✅ `privacy_level_options` - For privacy dropdown
- ✅ `comment_disabled` - For comment toggle
- ✅ `duet_disabled` - For duet toggle
- ✅ `stitch_disabled` - For stitch toggle
- ✅ `creator_username` - For unique ID
- ✅ `creator_nickname` - For display name
- ✅ `creator_avatar_url` - For profile picture

## Testing

Run `python3 test_account_specific_settings.py` to verify:
- ✓ Account-specific settings storage
- ✓ Privacy options per account
- ✓ Max duration validation per account
- ✓ Interaction settings per account

## Benefits

1. **Full API Compliance**: Uses exact values from creator_info response
2. **Account Isolation**: Each account has independent settings
3. **Dynamic Updates**: Settings refresh when switching accounts
4. **Proper Validation**: Prevents posts that violate account limits
5. **Clear UX**: Users see only available options for their account