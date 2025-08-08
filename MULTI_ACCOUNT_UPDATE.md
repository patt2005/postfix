# Multi-Account Support Implementation Guide

## Summary of Changes

This document outlines the implementation of multi-account support for the TikTok posting app, allowing users to connect and manage multiple TikTok accounts.

## 1. Database Schema Changes

### New Models Structure:
- **User**: Main user account (email-based)
- **TikTokAccount**: Individual TikTok accounts linked to a User
- **ScheduledPost**: Now references both User and specific TikTokAccount

## 2. Key Features

1. **Multiple TikTok Accounts**: Users can connect multiple TikTok accounts
2. **Account Selection**: Users can select which account to post from
3. **Account Management**: Add, remove, and switch between TikTok accounts
4. **Per-Account Posting**: Each scheduled post is assigned to a specific TikTok account

## 3. Database Migration

Run the following commands to apply the database changes:

```bash
flask db upgrade
```

## 4. New API Endpoints

### Authentication
- `GET /auth/tiktok` - Initial login or add account (auto-detects)
- `GET /auth/tiktok/add` - Explicitly add a new TikTok account (requires login)
- `GET /auth/tiktok/callback` - OAuth callback (handles both scenarios)

### Account Management
- `GET /api/accounts/list` - List all TikTok accounts for current user
- `POST /api/accounts/switch/<account_id>` - Switch active TikTok account
- `DELETE /api/accounts/<account_id>` - Remove a TikTok account

### Posting (Updated)
- All posting endpoints now use the selected TikTok account
- `tiktok_account_id` is required in scheduled posts

## 5. Session Management

New session variables:
- `user_id` - Main user ID
- `current_tiktok_account_id` - Active TikTok account ID
- `tiktok_access_token` - Access token for current TikTok account (backward compatibility)

## 6. Dashboard Updates Needed

The dashboard needs to be updated to:
1. Show account selector dropdown
2. Display multiple connected accounts
3. Allow adding new accounts
4. Show which account each scheduled post will use

## 7. Implementation Steps

### Step 1: Update the callback function in app.py
Replace the entire `/auth/tiktok/callback` route with the new version from `app_callback_new.py`

### Step 2: Add account management endpoints
Add these new routes to app.py:

```python
@app.route('/api/accounts/list')
@login_required
def list_tiktok_accounts():
    user_id = session.get('user_id')
    accounts = TikTokAccount.query.filter_by(user_id=user_id, is_active=True).all()
    
    return jsonify({
        'accounts': [{
            'id': acc.id,
            'username': acc.username,
            'display_name': acc.display_name,
            'avatar_url': acc.avatar_url,
            'follower_count': acc.follower_count,
            'is_current': acc.id == session.get('current_tiktok_account_id')
        } for acc in accounts]
    })

@app.route('/api/accounts/switch/<int:account_id>', methods=['POST'])
@login_required
def switch_tiktok_account(account_id):
    user_id = session.get('user_id')
    account = TikTokAccount.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    session['current_tiktok_account_id'] = account.id
    session['tiktok_access_token'] = account.access_token
    
    return jsonify({'success': True, 'account': {
        'id': account.id,
        'username': account.username,
        'display_name': account.display_name
    }})

@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_tiktok_account(account_id):
    user_id = session.get('user_id')
    account = TikTokAccount.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    # Check if this is the last account
    account_count = TikTokAccount.query.filter_by(user_id=user_id, is_active=True).count()
    if account_count <= 1:
        return jsonify({'error': 'Cannot delete the last account'}), 400
    
    account.is_active = False
    db.session.commit()
    
    # Switch to another account if this was the current one
    if session.get('current_tiktok_account_id') == account_id:
        other_account = TikTokAccount.query.filter_by(user_id=user_id, is_active=True).first()
        if other_account:
            session['current_tiktok_account_id'] = other_account.id
            session['tiktok_access_token'] = other_account.access_token
    
    return jsonify({'success': True})
```

### Step 3: Update posting endpoints
Modify the post creation endpoints to use the current TikTok account:

```python
@app.route('/api/scheduled/create', methods=['POST'])
@login_required
def create_scheduled_post():
    user_id = session.get('user_id')
    tiktok_account_id = session.get('current_tiktok_account_id')
    
    if not tiktok_account_id:
        return jsonify({'error': 'No TikTok account selected'}), 400
    
    data = request.get_json()
    
    # ... validation ...
    
    scheduled_post = ScheduledPost(
        user_id=user_id,
        tiktok_account_id=tiktok_account_id,  # Add this
        # ... rest of fields ...
    )
    
    # ... rest of function ...
```

## 8. Testing

1. Test initial login flow
2. Test adding additional accounts
3. Test switching between accounts
4. Test posting to different accounts
5. Test account deletion

## 9. Notes

- The system maintains backward compatibility with existing single-account setups
- Each TikTok account stores its own access tokens
- The `is_active` flag allows soft deletion of accounts
- Account switching updates both session and active tokens