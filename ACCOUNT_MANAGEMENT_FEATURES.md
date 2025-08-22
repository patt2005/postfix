# TikTok Account Management Features

## Overview
Enhanced the dashboard page with comprehensive TikTok account management capabilities, including account selection, profile display using TikTok's Display API, and account add/remove functionality.

## Features Implemented

### 1. Enhanced Account Selection Dropdown
- **Location**: Dashboard page (`templates/dashboard.html`)
- **Features**:
  - Dropdown shows all connected TikTok accounts
  - Displays username and display name for each account
  - Stores additional metadata (avatar URL, follower count)
  - Auto-selects first account if only one exists

### 2. Account Information Display
- **Visual Elements**:
  - Profile avatar or placeholder icon
  - Display name and username
  - Follower count
  - Refresh button to update profile data
- **Data Source**: TikTok Display API (`/v2/user/info/`)
- **Auto-updates**: When account is selected from dropdown

### 3. Add Account Button
- **Functionality**: 
  - Redirects to TikTok OAuth flow (`/auth/tiktok/add`)
  - Uses TikTok Login Kit for authentication
  - Supports multiple accounts per user
  - Shows even when accounts exist (for adding more)
  - Special "Connect TikTok Account" button when no accounts exist

### 4. Remove Account Button
- **Functionality**:
  - Only enabled when an account is selected
  - Shows confirmation dialog before removal
  - Revokes TikTok access token on removal
  - Soft-deletes account from database
  - Automatically switches to another account if available
  - Reloads page if last account is removed

### 5. Profile Refresh
- **API Integration**: Display API endpoint `/api/user/profile/<account_id>`
- **Updates**:
  - Avatar URL
  - Display name
  - Bio description
  - Follower/following counts
  - Likes and video counts
  - Verification status
- **Triggers**: 
  - On account selection
  - Manual refresh button click
  - After adding new account

## Technical Implementation

### Frontend (JavaScript)
```javascript
// Key functions added:
- displayAccountInfo(account) - Shows account details in UI
- Enhanced accountPicker change handler
- Remove account with API call and UI update
- Add account redirection to OAuth flow
- Profile refresh functionality
```

### Backend Routes
1. **OAuth Flow**:
   - `/auth/tiktok` - Initial OAuth redirect
   - `/auth/tiktok/add` - Add additional account
   - `/auth/tiktok/callback` - OAuth callback handler

2. **Account Management API**:
   - `GET /api/accounts/list` - List all user's TikTok accounts
   - `POST /api/accounts/switch/<id>` - Switch active account
   - `DELETE /api/accounts/<id>` - Remove account (with token revocation)

3. **Display API Integration**:
   - `GET /api/user/profile/<id>` - Fetch user profile
   - `POST /api/user/videos/<id>` - Get user's videos
   - `POST /api/videos/query` - Query specific videos

### Database Schema
- **TikTokAccount** model stores:
  - OAuth tokens (access & refresh)
  - Profile information
  - Statistics (followers, likes, etc.)
  - Multiple accounts per user support

## User Experience Flow

1. **First Time User**:
   - Sees "No TikTok accounts connected" message
   - Clicks "Connect TikTok Account" button
   - Redirected to TikTok Login Kit
   - Account added and auto-selected

2. **Adding Additional Account**:
   - Click "Add Account" button
   - Authenticate with TikTok
   - New account appears in dropdown
   - Can switch between accounts

3. **Managing Accounts**:
   - Select account from dropdown to view details
   - Click "Remove" to disconnect account
   - Click "Refresh" to update profile data
   - Account info shows avatar, name, and followers

## Security Features
- CSRF protection with state tokens
- OAuth 2.0 with PKCE flow
- Secure token storage in database
- Token revocation on account removal
- Soft delete preserves data integrity

## API Compliance
- Uses TikTok Display API for profile data
- Follows TikTok OAuth 2.0 specifications
- Implements proper token management
- Respects rate limits and scopes