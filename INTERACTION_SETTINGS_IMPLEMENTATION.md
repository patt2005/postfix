# Interaction Settings Implementation

## TikTok API Requirements
Based on creator_info API response fields:
- `comment_disabled`: If true, comment interaction must be disabled
- `duet_disabled`: If true, duet interaction must be disabled  
- `stitch_disabled`: If true, stitch interaction must be disabled

## Implementation Details

### 1. No Default Checked State ✅
- **All toggles start unchecked** - Users must manually enable each interaction
- No `checked` attribute on any checkbox by default
- Resets to unchecked when switching accounts
- Clear instruction: "You must manually enable each interaction - none are checked by default"

### 2. Disabled Interaction Handling ✅

#### Visual Feedback When Disabled:
- **Greyed out** (opacity: 0.5) when disabled in account settings
- **Disabled attribute** prevents user interaction
- **Red error text** shows: "Disabled in your account settings"
- Toggle cannot be enabled if account has it disabled

#### Code Implementation:
```javascript
if (creatorSettings.comment_disabled) {
    commentToggle.disabled = true;
    commentControl.style.opacity = '0.5';
    document.getElementById('commentDisabledReason').style.display = 'block';
}
```

### 3. Photo Post Handling ✅

#### Detection:
- Checks file extension: `['jpg', 'jpeg', 'png', 'gif', 'webp']`

#### Behavior for Photos:
- **Hides** Duet and Stitch controls completely
- **Shows only** Allow Comments toggle
- **Displays note**: "For photo posts, only 'Allow Comments' is available"
- Automatically unchecks duet/stitch if photo selected

#### Behavior for Videos:
- Shows all three interaction options
- Each respects account-level restrictions

### 4. User Interface

#### HTML Structure:
```html
<!-- No checked attribute by default -->
<input type="checkbox" id="allowComments" name="allow_comments">
<input type="checkbox" id="allowDuet" name="allow_duet">
<input type="checkbox" id="allowStitch" name="allow_stitch">
```

#### Visual States:
- **Available**: Normal appearance, user can toggle
- **Disabled**: Greyed out (0.5 opacity), cannot toggle, shows reason
- **Hidden**: Not displayed (for photo posts)

### 5. Account-Specific Behavior

The app fetches settings from creator_info API per account:
```javascript
accountCreatorInfo[accountId] = {
    comment_disabled: false,  // From API
    duet_disabled: false,     // From API
    stitch_disabled: true,    // From API
}
```

When switching accounts:
1. Fetches new account's creator_info
2. Updates all toggle states
3. Resets all to unchecked
4. Applies new restrictions

## Example Scenarios

### Scenario 1: Public Account, All Enabled
```json
{
  "comment_disabled": false,
  "duet_disabled": false,
  "stitch_disabled": false
}
```
**Result**: All toggles available, none checked, user can enable any

### Scenario 2: Private Account
```json
{
  "comment_disabled": false,
  "duet_disabled": true,
  "stitch_disabled": true
}
```
**Result**: 
- Comments: Available to toggle
- Duet: Greyed out, disabled, shows "Disabled in account settings"
- Stitch: Greyed out, disabled, shows "Disabled in account settings"

### Scenario 3: Photo Upload
**Result**:
- Comments: Available to toggle
- Duet: Hidden completely
- Stitch: Hidden completely
- Note shown: "For photo posts, only 'Allow Comments' is available"

## User Experience Flow

1. **Initial State**: All toggles unchecked, no defaults
2. **User Action Required**: Must manually click each desired interaction
3. **Account Restrictions**: Cannot enable if greyed out
4. **Photo Detection**: Automatically adjusts available options
5. **Clear Feedback**: Visual and text indicators for all states

## Compliance Verification

### ✅ TikTok Requirements Met:
1. **Disabled interactions are greyed out** - Visual opacity 0.5 + disabled attribute
2. **Users must manually turn on** - No default checked state
3. **None checked by default** - All start as unchecked
4. **Photo posts hide duet/stitch** - Only comments shown for photos

### ✅ Additional Features:
1. **Clear messaging** - Explains why options are disabled
2. **Account switching** - Resets and reapplies settings
3. **Visual feedback** - Yellow notice box with instructions
4. **Reason display** - Shows "Disabled in account settings"

## Testing

Run `python3 test_interaction_settings.py` to verify:
- ✓ No default checked states
- ✓ Proper disabled handling
- ✓ Photo post detection
- ✓ User guidance displayed

## API Response Handling

The implementation correctly uses these fields from creator_info:
```json
{
  "data": {
    "comment_disabled": false,
    "duet_disabled": false,
    "stitch_disabled": true,
    "max_video_post_duration_sec": 300
  }
}
```

Each field directly controls the corresponding toggle's availability.