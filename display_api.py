"""
TikTok Display API Implementation
Handles user profile information and video listing/querying
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, TikTokAccount, UserVideo
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
    Get TikTok user profile information including followers, avatar, display name
    Uses Display API: GET /v2/user/info/
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
        
        # Prepare request headers
        headers = {
            'Authorization': f'Bearer {account.access_token}',
        }
        
        # Fields to retrieve
        fields = 'open_id,union_id,avatar_url,avatar_url_100,avatar_url_200,display_name,bio_description,profile_deep_link,is_verified,follower_count,following_count,likes_count,video_count'
        
        # Make API request
        response = requests.get(
            f'{TIKTOK_BASE_URL}/user/info/',
            headers=headers,
            params={'fields': fields}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data and 'user' in data['data']:
                user_info = data['data']['user']
                
                # Update account information in database
                account.display_name = user_info.get('display_name')
                account.avatar_url = user_info.get('avatar_url_200') or user_info.get('avatar_url')
                account.follower_count = user_info.get('follower_count', 0)
                account.following_count = user_info.get('following_count', 0)
                account.likes_count = user_info.get('likes_count', 0)
                account.video_count = user_info.get('video_count', 0)
                account.is_verified = user_info.get('is_verified', False)
                account.bio = user_info.get('bio_description', '')
                account.last_profile_update = datetime.utcnow()
                
                db.session.commit()
                
                # Format response
                profile_data = {
                    'account_id': account_id,
                    'username': account.username,
                    'display_name': user_info.get('display_name'),
                    'avatar_url': user_info.get('avatar_url_200') or user_info.get('avatar_url'),
                    'avatar_url_100': user_info.get('avatar_url_100'),
                    'bio': user_info.get('bio_description'),
                    'is_verified': user_info.get('is_verified', False),
                    'stats': {
                        'followers': user_info.get('follower_count', 0),
                        'following': user_info.get('following_count', 0),
                        'likes': user_info.get('likes_count', 0),
                        'videos': user_info.get('video_count', 0)
                    },
                    'profile_link': user_info.get('profile_deep_link'),
                    'last_updated': account.last_profile_update.isoformat() if account.last_profile_update else None
                }
                
                logger.info(f"Profile fetched for @{account.username}: {user_info.get('follower_count', 0)} followers")
                
                return jsonify({
                    'success': True,
                    'data': profile_data
                })
            else:
                return jsonify({'error': 'Invalid response from TikTok API'}), 500
        else:
            error_data = response.json()
            logger.error(f"Failed to fetch user profile: {error_data}")
            return jsonify({
                'error': 'Failed to fetch profile',
                'details': error_data.get('error', {}).get('message')
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching user profile: {str(e)}")
        return jsonify({'error': 'Failed to fetch user profile'}), 500


@display_bp.route('/api/user/videos/<int:account_id>', methods=['POST'])
@login_required
def get_user_videos(account_id):
    """
    Get list of user's TikTok videos
    Uses Display API: POST /v2/video/list/
    """
    try:
        # Get request parameters
        data = request.get_json() or {}
        max_count = min(data.get('max_count', 20), 100)  # Limit to 100 videos
        cursor = data.get('cursor', 0)
        
        # Get the TikTok account
        account = TikTokAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Prepare request
        headers = {
            'Authorization': f'Bearer {account.access_token}',
            'Content-Type': 'application/json'
        }
        
        # Fields to retrieve for videos
        fields = 'id,title,video_description,create_time,duration,height,width,cover_image_url,share_url,embed_link,embed_html,view_count,like_count,comment_count,share_count'
        
        request_body = {
            'max_count': max_count
        }
        
        if cursor:
            request_body['cursor'] = cursor
        
        # Make API request
        response = requests.post(
            f'{TIKTOK_BASE_URL}/video/list/',
            headers=headers,
            params={'fields': fields},
            json=request_body
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                videos_data = data['data'].get('videos', [])
                
                # Process and store videos
                processed_videos = []
                for video in videos_data:
                    # Check if video already exists
                    existing_video = UserVideo.query.filter_by(
                        tiktok_account_id=account_id,
                        video_id=video['id']
                    ).first()
                    
                    if existing_video:
                        # Update existing video
                        existing_video.title = video.get('title')
                        existing_video.description = video.get('video_description')
                        existing_video.duration = video.get('duration')
                        existing_video.cover_image_url = video.get('cover_image_url')
                        existing_video.view_count = video.get('view_count', 0)
                        existing_video.like_count = video.get('like_count', 0)
                        existing_video.comment_count = video.get('comment_count', 0)
                        existing_video.share_count = video.get('share_count', 0)
                        existing_video.last_updated = datetime.utcnow()
                    else:
                        # Create new video record
                        new_video = UserVideo(
                            tiktok_account_id=account_id,
                            video_id=video['id'],
                            title=video.get('title'),
                            description=video.get('video_description'),
                            create_time=datetime.fromtimestamp(video.get('create_time', 0)),
                            duration=video.get('duration'),
                            height=video.get('height'),
                            width=video.get('width'),
                            cover_image_url=video.get('cover_image_url'),
                            share_url=video.get('share_url'),
                            embed_link=video.get('embed_link'),
                            embed_html=video.get('embed_html'),
                            view_count=video.get('view_count', 0),
                            like_count=video.get('like_count', 0),
                            comment_count=video.get('comment_count', 0),
                            share_count=video.get('share_count', 0),
                            last_updated=datetime.utcnow()
                        )
                        db.session.add(new_video)
                    
                    processed_videos.append({
                        'id': video['id'],
                        'title': video.get('title'),
                        'description': video.get('video_description'),
                        'create_time': video.get('create_time'),
                        'duration': video.get('duration'),
                        'cover_image_url': video.get('cover_image_url'),
                        'share_url': video.get('share_url'),
                        'embed_link': video.get('embed_link'),
                        'stats': {
                            'views': video.get('view_count', 0),
                            'likes': video.get('like_count', 0),
                            'comments': video.get('comment_count', 0),
                            'shares': video.get('share_count', 0)
                        }
                    })
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'data': {
                        'videos': processed_videos,
                        'cursor': data['data'].get('cursor'),
                        'has_more': data['data'].get('has_more', False),
                        'total_fetched': len(processed_videos)
                    }
                })
            else:
                return jsonify({'error': 'Invalid response from TikTok API'}), 500
        else:
            error_data = response.json()
            logger.error(f"Failed to fetch videos: {error_data}")
            return jsonify({
                'error': 'Failed to fetch videos',
                'details': error_data.get('error', {}).get('message')
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching user videos: {str(e)}")
        return jsonify({'error': 'Failed to fetch videos'}), 500


@display_bp.route('/api/videos/query', methods=['POST'])
@login_required
def query_videos():
    """
    Query specific videos by IDs to refresh metadata
    Uses Display API: POST /v2/video/query/
    """
    try:
        data = request.get_json()
        video_ids = data.get('video_ids', [])
        account_id = data.get('account_id')
        
        if not video_ids:
            return jsonify({'error': 'No video IDs provided'}), 400
        
        # Get the TikTok account
        account = TikTokAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Prepare request
        headers = {
            'Authorization': f'Bearer {account.access_token}',
            'Content-Type': 'application/json'
        }
        
        fields = 'id,title,video_description,duration,cover_image_url,share_url,embed_link,view_count,like_count,comment_count,share_count'
        
        request_body = {
            'filters': {
                'video_ids': video_ids[:20]  # Limit to 20 videos per request
            }
        }
        
        # Make API request
        response = requests.post(
            f'{TIKTOK_BASE_URL}/video/query/',
            headers=headers,
            params={'fields': fields},
            json=request_body
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'data' in data:
                videos_data = data['data'].get('videos', [])
                
                # Update video records
                updated_videos = []
                for video in videos_data:
                    existing_video = UserVideo.query.filter_by(
                        tiktok_account_id=account_id,
                        video_id=video['id']
                    ).first()
                    
                    if existing_video:
                        # Update metadata
                        existing_video.title = video.get('title')
                        existing_video.description = video.get('video_description')
                        existing_video.cover_image_url = video.get('cover_image_url')
                        existing_video.view_count = video.get('view_count', 0)
                        existing_video.like_count = video.get('like_count', 0)
                        existing_video.comment_count = video.get('comment_count', 0)
                        existing_video.share_count = video.get('share_count', 0)
                        existing_video.last_updated = datetime.utcnow()
                    
                    updated_videos.append({
                        'id': video['id'],
                        'title': video.get('title'),
                        'cover_image_url': video.get('cover_image_url'),
                        'embed_link': video.get('embed_link'),
                        'stats': {
                            'views': video.get('view_count', 0),
                            'likes': video.get('like_count', 0),
                            'comments': video.get('comment_count', 0),
                            'shares': video.get('share_count', 0)
                        }
                    })
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'data': {
                        'videos': updated_videos,
                        'total_updated': len(updated_videos)
                    }
                })
            else:
                return jsonify({'error': 'Invalid response from TikTok API'}), 500
        else:
            error_data = response.json()
            logger.error(f"Failed to query videos: {error_data}")
            return jsonify({
                'error': 'Failed to query videos',
                'details': error_data.get('error', {}).get('message')
            }), response.status_code
            
    except Exception as e:
        logger.error(f"Error querying videos: {str(e)}")
        return jsonify({'error': 'Failed to query videos'}), 500


@display_bp.route('/api/videos/select', methods=['POST'])
@login_required
def select_videos():
    """
    Save user's selected videos for display in the app
    """
    try:
        data = request.get_json()
        video_ids = data.get('video_ids', [])
        account_id = data.get('account_id')
        
        if not video_ids:
            return jsonify({'error': 'No videos selected'}), 400
        
        # Update selected status for videos
        UserVideo.query.filter(
            UserVideo.tiktok_account_id == account_id,
            UserVideo.video_id.in_(video_ids)
        ).update({'is_selected': True}, synchronize_session=False)
        
        # Deselect other videos
        UserVideo.query.filter(
            UserVideo.tiktok_account_id == account_id,
            ~UserVideo.video_id.in_(video_ids)
        ).update({'is_selected': False}, synchronize_session=False)
        
        db.session.commit()
        
        # Get selected videos
        selected = UserVideo.query.filter_by(
            tiktok_account_id=account_id,
            is_selected=True
        ).all()
        
        return jsonify({
            'success': True,
            'data': {
                'selected_count': len(selected),
                'video_ids': [v.video_id for v in selected]
            }
        })
        
    except Exception as e:
        logger.error(f"Error selecting videos: {str(e)}")
        return jsonify({'error': 'Failed to select videos'}), 500


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
                
                fields = 'display_name,avatar_url,follower_count,following_count,likes_count,video_count'
                
                response = requests.get(
                    f'{TIKTOK_BASE_URL}/user/info/',
                    headers=headers,
                    params={'fields': fields}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'user' in data['data']:
                        user_info = data['data']['user']
                        
                        # Update account
                        account.display_name = user_info.get('display_name')
                        account.avatar_url = user_info.get('avatar_url')
                        account.follower_count = user_info.get('follower_count', 0)
                        account.following_count = user_info.get('following_count', 0)
                        account.likes_count = user_info.get('likes_count', 0)
                        account.video_count = user_info.get('video_count', 0)
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