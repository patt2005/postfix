# TikTok API Compliance Helper Functions
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class TikTokComplianceValidator:
    """Validates posts against TikTok's UX requirements"""
    
    @staticmethod
    def validate_creator_can_post(creator_info: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Check if creator can make more posts at this moment
        Returns: (can_post, error_message)
        """
        if not creator_info:
            return False, "Creator info not available"
        
        can_post = creator_info.get('creator_can_post', True)
        if not can_post:
            return False, "You've reached your posting limit. Please try again later."
        
        return True, None
    
    @staticmethod
    def validate_video_duration(duration_seconds: int, creator_info: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate video duration against creator's max allowed duration
        Returns: (is_valid, error_message)
        """
        if not creator_info:
            return False, "Creator info not available"
        
        max_duration = creator_info.get('max_video_post_duration_sec', 60)
        
        if duration_seconds > max_duration:
            return False, f"Video duration ({duration_seconds}s) exceeds maximum allowed ({max_duration}s)"
        
        return True, None
    
    @staticmethod
    def validate_privacy_for_commercial_content(
        privacy_level: str, 
        is_branded_content: bool
    ) -> tuple[bool, Optional[str]]:
        """
        Validate privacy settings for commercial content
        Branded content cannot be set to private (SELF_ONLY)
        """
        if is_branded_content and privacy_level == 'SELF_ONLY':
            return False, "Branded content visibility cannot be set to private"
        
        return True, None
    
    @staticmethod
    def get_privacy_options_from_creator_info(creator_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Get privacy level options from creator_info API response
        Falls back to defaults if not available
        """
        if creator_info and 'privacy_level_options' in creator_info:
            return creator_info['privacy_level_options']
        
        # Default privacy options
        return [
            {'value': 'PUBLIC_TO_EVERYONE', 'label': 'Public'},
            {'value': 'MUTUAL_FOLLOW_FRIENDS', 'label': 'Friends'},
            {'value': 'SELF_ONLY', 'label': 'Only Me'}
        ]
    
    @staticmethod
    def check_interaction_capabilities(creator_info: Dict[str, Any]) -> Dict[str, bool]:
        """
        Check which interactions are disabled in creator's app settings
        """
        return {
            'comment_disabled': creator_info.get('comment_disabled', False),
            'duet_disabled': creator_info.get('duet_disabled', False),
            'stitch_disabled': creator_info.get('stitch_disabled', False)
        }
    
    @staticmethod
    def validate_commercial_content_selection(
        commercial_toggle: bool,
        your_brand: bool,
        branded_content: bool
    ) -> tuple[bool, Optional[str]]:
        """
        Validate that at least one commercial content option is selected when toggle is on
        """
        if commercial_toggle and not (your_brand or branded_content):
            return False, "You need to indicate if your content promotes yourself, a third party, or both"
        
        return True, None
    
    @staticmethod
    def get_consent_text(your_brand: bool, branded_content: bool) -> str:
        """
        Get the appropriate consent text based on commercial content selection
        """
        base_text = "By posting, you agree to TikTok's Music Usage Confirmation"
        
        if branded_content:
            return f"{base_text} and Branded Content Policy"
        
        return base_text
    
    @staticmethod
    def get_content_label(your_brand: bool, branded_content: bool) -> Optional[str]:
        """
        Get the content label that will be displayed on the video
        """
        if your_brand and branded_content:
            return "Paid partnership"
        elif branded_content:
            return "Paid partnership"
        elif your_brand:
            return "Promotional content"
        
        return None
    
    @staticmethod
    def validate_required_fields(post_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate all required fields are present
        Returns: (is_valid, list_of_missing_fields)
        """
        required_fields = ['title', 'privacy_level']
        missing_fields = []
        
        for field in required_fields:
            if not post_data.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            return False, missing_fields
        
        return True, []
    
    @staticmethod
    def prepare_post_info(
        post_data: Dict[str, Any],
        creator_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Prepare post_info object with proper interaction settings
        """
        # Get interaction capabilities
        capabilities = TikTokComplianceValidator.check_interaction_capabilities(creator_info)
        
        post_info = {
            'title': post_data.get('title', ''),
            'privacy_level': post_data.get('privacy_level', 'PUBLIC_TO_EVERYONE'),
            'video_cover_timestamp_ms': post_data.get('video_cover_timestamp_ms', 1000)
        }
        
        # Handle comment setting
        if not capabilities['comment_disabled']:
            post_info['disable_comment'] = post_data.get('disable_comment', False)
        else:
            # If comments are disabled in app settings, always disable
            post_info['disable_comment'] = True
        
        # Handle duet setting (not applicable to photo posts)
        if not post_data.get('is_photo_post', False):
            if not capabilities['duet_disabled']:
                post_info['disable_duet'] = post_data.get('disable_duet', False)
            else:
                post_info['disable_duet'] = True
        
        # Handle stitch setting (not applicable to photo posts)
        if not post_data.get('is_photo_post', False):
            if not capabilities['stitch_disabled']:
                post_info['disable_stitch'] = post_data.get('disable_stitch', False)
            else:
                post_info['disable_stitch'] = True
        
        # Add commercial content disclosure if applicable
        if post_data.get('content_disclosure'):
            disclosure = post_data['content_disclosure']
            if disclosure.get('your_brand') or disclosure.get('branded_content'):
                post_info['content_disclosure'] = {
                    'is_promotional': disclosure.get('your_brand', False),
                    'is_branded_content': disclosure.get('branded_content', False)
                }
        
        return post_info


class TikTokPostStatusMonitor:
    """Monitors post status and provides user feedback"""
    
    STATUS_MESSAGES = {
        'PROCESSING_UPLOAD': 'Your video is being uploaded to TikTok servers...',
        'PROCESSING_DOWNLOAD': 'TikTok is processing your video...',
        'PUBLISH_COMPLETE': 'Your video has been published successfully! It may take a few minutes to appear on your profile.',
        'FAILED': 'Unfortunately, your post failed to publish.'
    }
    
    @staticmethod
    def get_user_friendly_status(status: str, fail_reason: Optional[str] = None) -> str:
        """
        Convert API status to user-friendly message
        """
        message = TikTokPostStatusMonitor.STATUS_MESSAGES.get(
            status, 
            f'Post status: {status}'
        )
        
        if status == 'FAILED' and fail_reason:
            message += f' Reason: {fail_reason}'
        
        return message
    
    @staticmethod
    def should_continue_polling(status: str) -> bool:
        """
        Determine if we should continue polling for status updates
        """
        return status in ['PROCESSING_UPLOAD', 'PROCESSING_DOWNLOAD', 'PROCESSING']
    
    @staticmethod
    def get_poll_interval(status: str, attempt_number: int) -> int:
        """
        Get polling interval in seconds based on status and attempt number
        Uses exponential backoff
        """
        base_interval = 5  # 5 seconds
        max_interval = 30  # 30 seconds
        
        if status in ['PROCESSING_UPLOAD', 'PROCESSING_DOWNLOAD']:
            # Use exponential backoff with cap
            interval = min(base_interval * (1.5 ** attempt_number), max_interval)
            return int(interval)
        
        return base_interval


class TikTokAPIErrorHandler:
    """Handles TikTok API errors with user-friendly messages"""
    
    ERROR_MESSAGES = {
        'access_token_invalid': 'Your session has expired. Please reconnect your TikTok account.',
        'scope_not_authorized': 'Additional permissions required. Please reconnect your TikTok account.',
        'url_ownership_unverified': 'Domain verification required. Please verify your domain in TikTok Developer Portal or use file upload instead.',
        'rate_limit_exceeded': 'Too many requests. Please wait a moment and try again.',
        'video_too_large': 'Video file is too large. Please compress or trim your video.',
        'invalid_privacy_level': 'Invalid privacy setting selected.',
        'creator_cannot_post': 'You have reached your posting limit for today. Please try again tomorrow.'
    }
    
    @staticmethod
    def get_user_friendly_error(error_code: str, error_message: Optional[str] = None) -> str:
        """
        Convert API error codes to user-friendly messages
        """
        friendly_message = TikTokAPIErrorHandler.ERROR_MESSAGES.get(
            error_code,
            error_message or f'An error occurred: {error_code}'
        )
        
        return friendly_message
    
    @staticmethod
    def should_retry(error_code: str) -> bool:
        """
        Determine if the error is retryable
        """
        retryable_errors = ['rate_limit_exceeded', 'temporary_error', 'service_unavailable']
        return error_code in retryable_errors