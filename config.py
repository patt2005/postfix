"""
Configuration file for TikTok API settings and review mode
"""
import os
from datetime import datetime

class TikTokConfig:
    """TikTok API configuration and review status"""
    
    # Review Mode Settings
    # Set this to False once your app passes TikTok's review
    REVIEW_MODE = True  # ⚠️ IMPORTANT: Keep True until TikTok approves your app
    
    # Review approval date (update when approved)
    REVIEW_APPROVED_DATE = None  # Set to datetime when approved, e.g., datetime(2024, 12, 25)
    
    # Allowed privacy levels during review
    # During review, only allow SELF_ONLY (private) posts
    REVIEW_MODE_PRIVACY_LEVELS = ['SELF_ONLY']
    
    # Production privacy levels (after approval)
    PRODUCTION_PRIVACY_LEVELS = ['PUBLIC_TO_EVERYONE', 'MUTUAL_FOLLOW_FRIENDS', 'SELF_ONLY']
    
    # Test accounts (optional - for internal testing)
    TEST_ACCOUNT_IDS = os.environ.get('TEST_ACCOUNT_IDS', '').split(',') if os.environ.get('TEST_ACCOUNT_IDS') else []
    
    # Review mode restrictions
    REVIEW_MODE_RESTRICTIONS = {
        'max_daily_posts': 10,  # Limit posts during testing
        'allow_public_posts': False,
        'allow_commercial_content': False,  # Disable commercial content during review
        'require_watermark': True,  # Add "TEST" watermark during review
        'allowed_video_sources': ['FILE_UPLOAD'],  # Only allow file uploads during review
    }
    
    # Review mode messages
    REVIEW_MODE_MESSAGES = {
        'privacy_restriction': 'During review period, only private posts (visible to you) are allowed. Public posting will be enabled after TikTok approval.',
        'commercial_restriction': 'Commercial content disclosure is disabled during the review period.',
        'posting_notice': '⚠️ App in Review Mode: Posts are private and for testing only.',
        'approval_pending': 'This app is pending TikTok review. Some features are limited.',
    }
    
    @classmethod
    def is_in_review_mode(cls):
        """Check if app is in review mode"""
        return cls.REVIEW_MODE and cls.REVIEW_APPROVED_DATE is None
    
    @classmethod
    def get_allowed_privacy_levels(cls):
        """Get allowed privacy levels based on review status"""
        if cls.is_in_review_mode():
            return cls.REVIEW_MODE_PRIVACY_LEVELS
        return cls.PRODUCTION_PRIVACY_LEVELS
    
    @classmethod
    def can_post_publicly(cls):
        """Check if public posting is allowed"""
        return not cls.is_in_review_mode()
    
    @classmethod
    def can_use_commercial_content(cls):
        """Check if commercial content disclosure is allowed"""
        return not cls.is_in_review_mode()
    
    @classmethod
    def get_review_status(cls):
        """Get current review status details"""
        return {
            'in_review': cls.is_in_review_mode(),
            'approved_date': cls.REVIEW_APPROVED_DATE.isoformat() if cls.REVIEW_APPROVED_DATE else None,
            'restrictions': cls.REVIEW_MODE_RESTRICTIONS if cls.is_in_review_mode() else None,
            'allowed_privacy_levels': cls.get_allowed_privacy_levels(),
            'can_post_publicly': cls.can_post_publicly(),
            'can_use_commercial_content': cls.can_use_commercial_content(),
        }
    
    @classmethod
    def validate_privacy_level(cls, privacy_level):
        """Validate if a privacy level is allowed"""
        allowed = cls.get_allowed_privacy_levels()
        if privacy_level not in allowed:
            if cls.is_in_review_mode():
                return False, cls.REVIEW_MODE_MESSAGES['privacy_restriction']
            return False, f"Invalid privacy level. Allowed: {', '.join(allowed)}"
        return True, None
    
    @classmethod
    def format_review_warning(cls):
        """Get formatted warning message for review mode"""
        if not cls.is_in_review_mode():
            return None
        
        return {
            'type': 'review_mode',
            'title': '🔒 App in Review Mode',
            'message': cls.REVIEW_MODE_MESSAGES['posting_notice'],
            'restrictions': [
                'Only private posts allowed (visible to you only)',
                'Commercial content disclosure disabled',
                f'Maximum {cls.REVIEW_MODE_RESTRICTIONS["max_daily_posts"]} test posts per day',
                'Public posting will be enabled after TikTok approval'
            ]
        }