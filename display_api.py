"""
TikTok Display API Implementation
Handles user profile information and video listing/querying
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, TikTokAccount
import requests
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

# Create blueprint
display_bp = Blueprint('display', __name__)

# TikTok API configuration
TIKTOK_BASE_URL = 'https://open.tiktokapis.com/v2'

@display_bp.route('/api/user/profile/<int:account_id>', methods=['GET'])
@login_required
def get_user_profile(account_id):
    """
    Get TikTok user profile information using creator_info/query endpoint
    This works with video.publish scope and provides avatar, username, and nickname
    """
    try:
        # Get the TikTok account
        account = TikTokAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            is_active=True
        ).first()

        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Check if token is expired and try to refresh if needed
        if account.token_expires_at and account.token_expires_at < datetime.utcnow():
            logger.warning(f"Access token expired for account {account.username}, attempting refresh")
            from app import refresh_tiktok_token  # Import refresh function
            
            if account.refresh_token:
                refreshed = refresh_tiktok_token(account)
                if not refreshed:
                    return jsonify({
                        'error': 'Your TikTok session has expired and could not be renewed. Please reconnect your account.',
                        'error_type': 'refresh_failed',
                        'requires_reauth': True
                    }), 401
            else:
                return jsonify({
                    'error': 'Your TikTok session has expired. Please reconnect your account.',
                    'error_type': 'no_refresh_token',
                    'requires_reauth': True
                }), 401
        
        # Use creator_info/query endpoint which works with video.publish scope
        headers = {
            'Authorization': f'Bearer {account.access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        
        # Make POST request to creator_info/query endpoint
        response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/creator_info/query/',
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                creator_info = data['data']
                
                # Update account information with creator info
                # creator_username is the unique ID, creator_nickname is the display name
                account.username = creator_info.get('creator_username', '')
                account.display_name = creator_info.get('creator_nickname', '')
                account.avatar_url = creator_info.get('creator_avatar_url', '')
                account.last_profile_update = datetime.utcnow()
                
                db.session.commit()
                
                # Format response with creator info data
                profile_data = {
                    'account_id': account_id,
                    'username': creator_info.get('creator_username', ''),  # Unique ID
                    'display_name': creator_info.get('creator_nickname', ''),  # Display name
                    'avatar_url': creator_info.get('creator_avatar_url', ''),
                    'bio': account.bio,  # Use stored value if available
                    'is_verified': account.is_verified,  # Use stored value
                    'stats': {
                        'followers': account.follower_count or 0,  # Use stored values
                        'following': account.following_count or 0,
                        'likes': account.likes_count or 0,
                        'videos': account.video_count or 0
                    },
                    # Additional creator info fields
                    'privacy_level_options': creator_info.get('privacy_level_options', []),
                    'comment_disabled': creator_info.get('comment_disabled', False),
                    'duet_disabled': creator_info.get('duet_disabled', False),
                    'stitch_disabled': creator_info.get('stitch_disabled', False),
                    'max_video_duration': creator_info.get('max_video_post_duration_sec', 60),
                    'last_updated': account.last_profile_update.isoformat() if account.last_profile_update else None
                }
                
                logger.info(f"Profile fetched for {creator_info.get('creator_username')} - {creator_info.get('creator_nickname')}")
                
                return jsonify({
                    'success': True,
                    'data': profile_data
                })
            else:
                return jsonify({'error': 'Invalid response from TikTok API'}), 500
        else:
            error_data = response.json()
            logger.error(f"Failed to fetch user profile: {error_data}")
            
            # Handle specific error types
            if response.status_code == 401:
                # Token expired or invalid
                error_code = error_data.get('error', {}).get('code', '')
                if 'token' in error_code.lower() or 'unauthorized' in error_code.lower():
                    return jsonify({
                        'error': 'Your TikTok session has expired. Please reconnect your account.',
                        'error_type': 'session_expired',
                        'requires_reauth': True
                    }), 401
            elif response.status_code == 403:
                # Forbidden - potentially refresh token expired
                return jsonify({
                    'error': 'Access denied. Your TikTok session may have expired.',
                    'error_type': 'access_denied',
                    'requires_reauth': True
                }), 403
            
            return jsonify({
                'error': 'Failed to fetch profile',
                'details': error_data.get('error', {}).get('message'),
                'error_code': error_data.get('error', {}).get('code')
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return jsonify({'error': 'Failed to fetch user profile'}), 500


# Removed UserVideo-related endpoints as we now use PostedVideo model


@display_bp.route('/api/profile/refresh-all', methods=['POST'])
@login_required
def refresh_all_profiles():
    """
    Refresh profile information for all active accounts
    Used by background jobs
    """
    try:
        # Get all active accounts for current user
        accounts = TikTokAccount.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        refreshed = []
        failed = []
        
        for account in accounts:
            try:
                # Fetch profile for each account
                headers = {
                    'Authorization': f'Bearer {account.access_token}',
                }
                
                # Only basic fields available with user.info.basic scope
                fields = 'open_id,union_id,avatar_url,display_name'
                
                response = requests.get(
                    f'{TIKTOK_BASE_URL}/user/info/',
                    headers=headers,
                    params={'fields': fields}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'user' in data['data']:
                        user_info = data['data']['user']
                        
                        # Update account with basic fields only
                        account.display_name = user_info.get('display_name')
                        account.avatar_url = user_info.get('avatar_url')
                        # Stats fields not available with basic scope - keep existing values
                        account.last_profile_update = datetime.utcnow()
                        
                        refreshed.append(account.username)
                else:
                    failed.append(account.username)
                    
            except Exception as e:
                logger.error(f"Failed to refresh profile for {account.username}: {str(e)}")
                failed.append(account.username)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'refreshed': refreshed,
                'failed': failed,
                'total': len(accounts)
            }
        })
        
    except Exception as e:
        logger.error(f"Error refreshing profiles: {str(e)}")
        return jsonify({'error': 'Failed to refresh profiles'}), 500