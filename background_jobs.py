"""
Background jobs for TikTok app
Handles token refresh and profile updates
"""

import os
import logging
import requests
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, TikTokAccount
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)

# Create database engine
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# TikTok API configuration
TIKTOK_BASE_URL = 'https://open.tiktokapis.com/v2'
TIKTOK_TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/'

def refresh_access_tokens():
    """
    Refresh access tokens for all accounts that are about to expire
    Runs every 6 hours
    """
    session = Session()
    try:
        # Get accounts with tokens expiring in the next 12 hours
        expiry_threshold = datetime.utcnow() + timedelta(hours=12)
        
        accounts = session.query(TikTokAccount).filter(
            TikTokAccount.is_active == True,
            TikTokAccount.token_expires_at < expiry_threshold,
            TikTokAccount.refresh_token.isnot(None)
        ).all()
        
        logger.info(f"Found {len(accounts)} accounts needing token refresh")
        
        for account in accounts:
            try:
                # Prepare refresh request
                data = {
                    'client_key': os.environ.get('TIKTOK_CLIENT_KEY'),
                    'client_secret': os.environ.get('TIKTOK_CLIENT_SECRET'),
                    'grant_type': 'refresh_token',
                    'refresh_token': account.refresh_token
                }
                
                # Make refresh request
                response = requests.post(TIKTOK_TOKEN_URL, data=data)
                
                if response.status_code == 200:
                    token_data = response.json()
                    
                    if 'data' in token_data:
                        # Update tokens
                        account.access_token = token_data['data'].get('access_token')
                        account.refresh_token = token_data['data'].get('refresh_token')
                        account.token_expires_at = datetime.utcnow() + timedelta(
                            seconds=token_data['data'].get('expires_in', 86400)
                        )
                        account.refresh_token_expires_at = datetime.utcnow() + timedelta(
                            seconds=token_data['data'].get('refresh_expires_in', 31536000)
                        )
                        
                        session.commit()
                        logger.info(f"Successfully refreshed token for @{account.username}")
                    else:
                        logger.error(f"Failed to refresh token for @{account.username}: Invalid response")
                else:
                    logger.error(f"Failed to refresh token for @{account.username}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error refreshing token for @{account.username}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in refresh_access_tokens: {str(e)}")
    finally:
        session.close()

def update_user_profiles():
    """
    Update user profile information for all active accounts
    Runs every 12 hours
    """
    session = Session()
    try:
        accounts = session.query(TikTokAccount).filter(
            TikTokAccount.is_active == True
        ).all()
        
        logger.info(f"Updating profiles for {len(accounts)} accounts")
        
        for account in accounts:
            try:
                headers = {
                    'Authorization': f'Bearer {account.access_token}',
                }
                
                fields = 'display_name,avatar_url,follower_count,following_count,likes_count,video_count,is_verified,bio_description'
                
                response = requests.get(
                    f'{TIKTOK_BASE_URL}/user/info/',
                    headers=headers,
                    params={'fields': fields}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'user' in data['data']:
                        user_info = data['data']['user']
                        
                        # Update account info
                        account.display_name = user_info.get('display_name')
                        account.avatar_url = user_info.get('avatar_url')
                        account.follower_count = user_info.get('follower_count', 0)
                        account.following_count = user_info.get('following_count', 0)
                        account.likes_count = user_info.get('likes_count', 0)
                        account.video_count = user_info.get('video_count', 0)
                        account.is_verified = user_info.get('is_verified', False)
                        account.bio = user_info.get('bio_description', '')
                        account.last_profile_update = datetime.utcnow()
                        
                        session.commit()
                        logger.info(f"Updated profile for @{account.username}")
                else:
                    logger.error(f"Failed to update profile for @{account.username}: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error updating profile for @{account.username}: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in update_user_profiles: {str(e)}")
    finally:
        session.close()

# Removed refresh_video_metadata function as we now use PostedVideo model

def start_scheduler():
    """
    Start the background job scheduler
    """
    scheduler = BackgroundScheduler()
    
    # Schedule token refresh every 6 hours
    scheduler.add_job(
        refresh_access_tokens,
        'interval',
        hours=6,
        id='refresh_tokens',
        replace_existing=True
    )
    
    # Schedule profile updates every 12 hours
    scheduler.add_job(
        update_user_profiles,
        'interval',
        hours=12,
        id='update_profiles',
        replace_existing=True
    )

    # Run jobs immediately on startup
    scheduler.add_job(refresh_access_tokens, 'date', run_date=datetime.now())
    scheduler.add_job(update_user_profiles, 'date', run_date=datetime.now())
    
    scheduler.start()
    logger.info("Background job scheduler started")
    
    return scheduler

if __name__ == "__main__":
    # Start scheduler when run directly
    scheduler = start_scheduler()
    
    try:
        # Keep the script running
        import time
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Background job scheduler stopped")