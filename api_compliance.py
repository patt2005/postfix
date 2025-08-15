"""
TikTok API Compliance Endpoints
Implements all required UX compliance checks for TikTok content posting
"""

from flask import Blueprint, request, jsonify, session
from flask_login import login_required, current_user
from models import db, TikTokAccount
from tiktok_compliance import TikTokComplianceValidator, TikTokPostStatusMonitor, TikTokAPIErrorHandler
from config import TikTokConfig
import requests
import logging
import os

logger = logging.getLogger(__name__)

# Create blueprint
compliance_bp = Blueprint('compliance', __name__)

# TikTok API configuration
TIKTOK_BASE_URL = 'https://open.tiktokapis.com/v2'


@compliance_bp.route('/api/creator/info/enhanced', methods=['GET'])
@login_required
def get_enhanced_creator_info():
    """
    Enhanced creator info endpoint that fetches and validates creator capabilities
    Requirement 1a: Display creator nickname
    Requirement 1b: Check if creator can post
    Requirement 1c: Get max video duration
    """
    try:
        # Get account ID from request or use current account
        account_id = request.args.get('account_id')
        
        if account_id:
            account = TikTokAccount.query.filter_by(
                id=account_id,
                user_id=current_user.id,
                is_active=True
            ).first()
        else:
            # Get first active account
            account = TikTokAccount.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).first()
        
        if not account:
            return jsonify({'error': 'No TikTok account found'}), 404
        
        # Make API request to get creator info
        headers = {
            'Authorization': f'Bearer {account.access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        
        response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/creator_info/query/',
            headers=headers
        )
        
        if response.status_code == 200:
            creator_data = response.json()
            
            # Add account info to response
            if 'data' in creator_data:
                creator_data['data']['account_info'] = {
                    'account_id': account.id,
                    'username': account.username,
                    'display_name': account.display_name
                }
                
                # Log important info
                creator_info = creator_data['data']
                logger.info(f"Creator info fetched for @{account.username}")
                logger.info(f"Can post: {creator_info.get('creator_can_post', 'unknown')}")
                logger.info(f"Max video duration: {creator_info.get('max_video_post_duration_sec', 'unknown')}s")
            
            return jsonify(creator_data)
        else:
            error_data = response.json()
            logger.error(f"Failed to fetch creator info: {error_data}")
            
            # Handle specific errors
            if 'error' in error_data:
                error_code = error_data['error'].get('code')
                friendly_error = TikTokAPIErrorHandler.get_user_friendly_error(
                    error_code,
                    error_data['error'].get('message')
                )
                return jsonify({
                    'error': friendly_error,
                    'error_code': error_code
                }), response.status_code
            
            return jsonify(error_data), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching creator info: {str(e)}")
        return jsonify({'error': 'Failed to fetch creator information'}), 500


@compliance_bp.route('/api/post/video/compliant', methods=['POST'])
@login_required
def post_video_compliant():
    """
    Compliant video posting endpoint with all required checks
    Implements all UX requirements from TikTok documentation
    """
    try:
        data = request.get_json()
        
        # Get TikTok account
        account_id = data.get('tiktok_account_id')
        if not account_id:
            return jsonify({'error': 'Missing tiktok_account_id'}), 400
        
        account = TikTokAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not account:
            return jsonify({'error': 'TikTok account not found or not authorized'}), 404
        
        # Step 1: Fetch and validate creator info (Requirement 1)
        logger.info("Fetching creator info for compliance check...")
        headers = {
            'Authorization': f'Bearer {account.access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        
        creator_response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/creator_info/query/',
            headers=headers
        )
        
        if creator_response.status_code != 200:
            return jsonify({
                'error': 'Unable to verify creator capabilities',
                'details': creator_response.json()
            }), 400
        
        creator_info = creator_response.json().get('data', {})
        
        # Requirement 1b: Check if creator can post
        can_post, error_msg = TikTokComplianceValidator.validate_creator_can_post(creator_info)
        if not can_post:
            return jsonify({
                'error': error_msg,
                'can_retry': True,
                'retry_after': 'later'
            }), 429
        
        # Requirement 1c: Validate video duration
        if data.get('video_duration'):
            is_valid, error_msg = TikTokComplianceValidator.validate_video_duration(
                data['video_duration'],
                creator_info
            )
            if not is_valid:
                return jsonify({'error': error_msg}), 400
        
        # Requirement 2: Validate required metadata
        is_valid, missing_fields = TikTokComplianceValidator.validate_required_fields(data)
        if not is_valid:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Requirement 2b: Validate privacy level selection
        privacy_level = data.get('privacy_level')
        
        # REVIEW MODE CHECK: Override privacy level if in review mode
        if TikTokConfig.is_in_review_mode():
            # Force private posting during review
            if privacy_level != 'SELF_ONLY':
                logger.info(f"Review mode: Overriding privacy level from {privacy_level} to SELF_ONLY")
                original_privacy = privacy_level
                privacy_level = 'SELF_ONLY'
                data['privacy_level'] = 'SELF_ONLY'
                
                # Add warning to response
                data['review_mode_override'] = {
                    'original_privacy': original_privacy,
                    'forced_privacy': 'SELF_ONLY',
                    'reason': TikTokConfig.REVIEW_MODE_MESSAGES['privacy_restriction']
                }
        
        # Validate privacy level
        is_valid, error_msg = TikTokConfig.validate_privacy_level(privacy_level)
        if not is_valid:
            return jsonify({
                'error': error_msg,
                'valid_options': TikTokConfig.get_allowed_privacy_levels(),
                'review_mode': TikTokConfig.is_in_review_mode()
            }), 400
        
        # Requirement 3: Handle commercial content disclosure
        content_disclosure = data.get('content_disclosure', {})
        
        # REVIEW MODE CHECK: Disable commercial content during review
        if content_disclosure and TikTokConfig.is_in_review_mode():
            logger.info("Review mode: Commercial content disclosure disabled")
            content_disclosure = {}  # Clear commercial content
            data['review_mode_commercial_disabled'] = True
        
        if content_disclosure:
            your_brand = content_disclosure.get('your_brand', False)
            branded_content = content_disclosure.get('branded_content', False)
            
            # Validate commercial content selection
            is_valid, error_msg = TikTokComplianceValidator.validate_commercial_content_selection(
                True,  # commercial toggle is on if content_disclosure exists
                your_brand,
                branded_content
            )
            if not is_valid:
                return jsonify({'error': error_msg}), 400
            
            # Requirement 3b: Validate privacy for branded content
            if branded_content:
                is_valid, error_msg = TikTokComplianceValidator.validate_privacy_for_commercial_content(
                    privacy_level,
                    branded_content
                )
                if not is_valid:
                    return jsonify({'error': error_msg}), 400
        
        # Requirement 5c: Validate user consent
        if not data.get('user_consent'):
            return jsonify({
                'error': 'User consent is required before posting',
                'consent_required': True
            }), 400
        
        # Prepare post_info with validated data
        post_info = TikTokComplianceValidator.prepare_post_info(data, creator_info)
        
        # Prepare source info
        source_type = data.get('source_type', 'FILE_UPLOAD')
        if source_type == 'PULL_FROM_URL':
            source_info = {
                'source': 'PULL_FROM_URL',
                'video_url': data.get('video_url')
            }
        else:
            video_size = data.get('video_size', 0)
            source_info = {
                'source': 'FILE_UPLOAD',
                'video_size': video_size,
                'chunk_size': video_size,
                'total_chunk_count': 1
            }
        
        # Make the actual post request
        request_body = {
            'post_info': post_info,
            'source_info': source_info
        }
        
        logger.info(f"Posting video with compliance checks passed")
        logger.info(f"Post info: {post_info}")
        
        response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/video/init/',
            headers=headers,
            json=request_body
        )
        
        response_data = response.json()
        
        if response.status_code == 200:
            # Success - add compliance info to response
            response_data['compliance'] = {
                'creator_nickname': creator_info.get('creator_nickname'),
                'content_label': TikTokComplianceValidator.get_content_label(
                    content_disclosure.get('your_brand', False),
                    content_disclosure.get('branded_content', False)
                ) if content_disclosure else None,
                'processing_notice': 'Your content is being processed and will appear on your profile in a few minutes.'
            }
            
            return jsonify(response_data)
        else:
            # Handle API errors
            if 'error' in response_data:
                error_code = response_data['error'].get('code')
                friendly_error = TikTokAPIErrorHandler.get_user_friendly_error(
                    error_code,
                    response_data['error'].get('message')
                )
                
                should_retry = TikTokAPIErrorHandler.should_retry(error_code)
                
                return jsonify({
                    'error': friendly_error,
                    'error_code': error_code,
                    'can_retry': should_retry
                }), response.status_code
            
            return jsonify(response_data), response.status_code
            
    except Exception as e:
        logger.error(f"Error in compliant video posting: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to post video'}), 500


@compliance_bp.route('/api/post/status/enhanced/<publish_id>', methods=['GET'])
@login_required
def get_enhanced_post_status(publish_id):
    """
    Enhanced post status endpoint with user-friendly messages
    Requirement 5d: Notify users about processing time
    Requirement 5e: Poll status API for updates
    """
    try:
        # Get account from query params or session
        account_id = request.args.get('account_id')
        
        if account_id:
            account = TikTokAccount.query.filter_by(
                id=account_id,
                user_id=current_user.id,
                is_active=True
            ).first()
        else:
            account = TikTokAccount.query.filter_by(
                user_id=current_user.id,
                is_active=True
            ).first()
        
        if not account:
            return jsonify({'error': 'No TikTok account found'}), 404
        
        headers = {
            'Authorization': f'Bearer {account.access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        
        request_body = {
            'publish_id': publish_id
        }
        
        response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/status/fetch/',
            headers=headers,
            json=request_body
        )
        
        if response.status_code == 200:
            response_data = response.json()
            
            if 'data' in response_data:
                status = response_data['data'].get('status')
                fail_reason = response_data['data'].get('fail_reason')
                
                # Add user-friendly status message
                response_data['data']['user_message'] = TikTokPostStatusMonitor.get_user_friendly_status(
                    status,
                    fail_reason
                )
                
                # Add polling info
                response_data['data']['should_continue_polling'] = TikTokPostStatusMonitor.should_continue_polling(status)
                
                if response_data['data']['should_continue_polling']:
                    attempt = request.args.get('attempt', 0, type=int)
                    response_data['data']['next_poll_interval'] = TikTokPostStatusMonitor.get_poll_interval(
                        status,
                        attempt
                    )
            
            return jsonify(response_data)
        else:
            error_data = response.json()
            return jsonify(error_data), response.status_code
            
    except Exception as e:
        logger.error(f"Error fetching post status: {str(e)}")
        return jsonify({'error': 'Failed to fetch post status'}), 500


@compliance_bp.route('/api/review/status', methods=['GET'])
@login_required
def get_review_status():
    """
    Get current review mode status and restrictions
    """
    review_status = TikTokConfig.get_review_status()
    review_warning = TikTokConfig.format_review_warning()
    
    return jsonify({
        'status': review_status,
        'warning': review_warning,
        'message': TikTokConfig.REVIEW_MODE_MESSAGES['approval_pending'] if TikTokConfig.is_in_review_mode() else 'App approved for public posting'
    })


@compliance_bp.route('/api/validate/video', methods=['POST'])
@login_required
def validate_video():
    """
    Validate video before posting
    Checks duration, format, and size requirements
    """
    try:
        data = request.get_json()
        
        # Get account
        account_id = data.get('account_id')
        if not account_id:
            return jsonify({'error': 'Missing account_id'}), 400
        
        account = TikTokAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            is_active=True
        ).first()
        
        if not account:
            return jsonify({'error': 'Account not found'}), 404
        
        # Fetch creator info for validation
        headers = {
            'Authorization': f'Bearer {account.access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        
        creator_response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/creator_info/query/',
            headers=headers
        )
        
        if creator_response.status_code != 200:
            return jsonify({'error': 'Unable to fetch creator info'}), 400
        
        creator_info = creator_response.json().get('data', {})
        
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate video duration
        video_duration = data.get('duration_seconds')
        if video_duration:
            is_valid, error_msg = TikTokComplianceValidator.validate_video_duration(
                video_duration,
                creator_info
            )
            if not is_valid:
                validation_results['is_valid'] = False
                validation_results['errors'].append(error_msg)
        
        # Check if creator can post
        can_post, error_msg = TikTokComplianceValidator.validate_creator_can_post(creator_info)
        if not can_post:
            validation_results['is_valid'] = False
            validation_results['errors'].append(error_msg)
        
        # Add creator info to response
        validation_results['creator_info'] = {
            'nickname': creator_info.get('creator_nickname'),
            'max_video_duration': creator_info.get('max_video_post_duration_sec'),
            'can_post': creator_info.get('creator_can_post'),
            'privacy_options': TikTokComplianceValidator.get_privacy_options_from_creator_info(creator_info),
            'interaction_capabilities': TikTokComplianceValidator.check_interaction_capabilities(creator_info)
        }
        
        return jsonify(validation_results)
        
    except Exception as e:
        logger.error(f"Error validating video: {str(e)}")
        return jsonify({'error': 'Validation failed'}), 500