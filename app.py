import os
import secrets
import requests
from flask import Flask, render_template, redirect, request, session, jsonify, url_for, send_from_directory, flash
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv
from urllib.parse import urlencode
from functools import wraps
from werkzeug.utils import secure_filename
import time
import hashlib
import base64
from datetime import datetime, timedelta
from flask_migrate import Migrate
from models import db, User, TikTokAccount, ScheduledPost, UserVideo
from google.cloud import scheduler
import json
from config import TikTokConfig

load_dotenv()

import logging
import sys

# Configure structured logging for Google Cloud Run
# Cloud Run automatically captures logs in JSON format from stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',  # Simple format - Cloud Run adds its own metadata
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output only to stdout for Cloud Run
    ],
    force=True  # Override any existing configuration
)

# Get logger
logger = logging.getLogger(__name__)

# For Google Cloud structured logging, we can use JSON format
import json as json_lib

class StructuredLogHandler(logging.Handler):
    """Handler that outputs structured logs for Google Cloud"""
    def emit(self, record):
        # Create structured log entry
        log_entry = {
            "severity": record.levelname,
            "message": record.getMessage(),
            "timestamp": record.created,
            "logger": record.name,
        }
        
        # Add any extra fields from the record
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Output as JSON for Cloud Run to parse
        print(json_lib.dumps(log_entry), flush=True)

# Use structured logging if in production
if os.environ.get('FLASK_ENV') == 'production' or os.environ.get('GAE_ENV', '').startswith('standard'):
    # Clear existing handlers
    logger.handlers = []
    # Add structured log handler for production
    structured_handler = StructuredLogHandler()
    structured_handler.setLevel(logging.INFO)
    logger.addHandler(structured_handler)
    logger.propagate = False

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_urlsafe(32))
app.config['WTF_CSRF_SECRET_KEY'] = os.environ.get('WTF_CSRF_SECRET_KEY', secrets.token_urlsafe(32))

database_url = os.environ.get('DATABASE_URL')

# Log the database configuration status
if database_url:
    logger.info(f"DATABASE_URL found: {database_url[:30]}...")
    # Fix for Railway PostgreSQL URL (postgresql:// -> postgresql+psycopg2://)
    if database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
        logger.info("Converted database URL to use psycopg2 driver")
else:
    logger.warning("DATABASE_URL not found in environment variables")
    # Use a default SQLite database for development
    database_url = 'sqlite:///app.db'
    logger.info("Using SQLite database for development")

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Always initialize db with the app
db.init_app(app)
migrate = Migrate(app, db)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def init_database():
    """Initialize database tables - safe for production"""
    try:
        with app.app_context():
            logger.info(f"Attempting to connect to database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')[:50]}...")
            
            # Create tables if they don't exist
            db.create_all()
            logger.info("Database tables created/verified")
            
            # Only run migrations if migrations folder exists
            if os.path.exists('migrations'):
                from flask_migrate import upgrade
                upgrade()
                logger.info("Database migrations applied successfully")
            else:
                logger.info("Migrations folder not found, skipping migrations")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        import traceback
        logger.error(traceback.format_exc())

if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or __name__ == '__main__':
    init_database()
else:
    @app.before_request
    def initialize_database():
        if not hasattr(app, 'db_initialized'):
            init_database()
            app.db_initialized = True

TIKTOK_CLIENT_KEY = os.environ.get('TIKTOK_CLIENT_KEY')
TIKTOK_CLIENT_SECRET = os.environ.get('TIKTOK_CLIENT_SECRET')
TIKTOK_REDIRECT_URI = os.environ.get('TIKTOK_REDIRECT_URI')
TIKTOK_AUTH_URL = 'https://www.tiktok.com/v2/auth/authorize/'
TIKTOK_TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/'
TIKTOK_BASE_URL = 'https://open.tiktokapis.com/v2'

# Google Cloud Scheduler configuration
GOOGLE_CLOUD_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT')
GOOGLE_CLOUD_LOCATION = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
SCHEDULER_SERVICE_URL = os.environ.get('SCHEDULER_SERVICE_URL')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'mov', 'avi', 'flv', 'wmv'}
MAX_CONTENT_LENGTH = 500 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def index():
    if current_user.is_authenticated:
        # Get user's TikTok accounts
        tiktok_accounts = TikTokAccount.query.filter_by(user_id=current_user.id).all()
        # return render_template('dashboard.html', tiktok_accounts=tiktok_accounts)
        return render_template('index.html')
    return render_template('index.html')


@app.route('/tiktokA4mLr5O0KsGFjXAezX2UN2qvTYKKvIVu.txt')
def tiktok_verification():
    """Serve TikTok domain verification file"""
    return send_from_directory('.', 'tiktokA4mLr5O0KsGFjXAezX2UN2qvTYKKvIVu.txt')


@app.route('/documentation')
def documentation():
    return render_template('documentation.html')


@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')


@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms-of-service.html')


@app.route('/help-center')
def help_center():
    return render_template('help-center.html')


@app.route('/debug/test-logging')
def test_logging():
    """Test endpoint to verify logging is working in Cloud Run"""
    import time
    timestamp = time.time()
    
    # Test structured logging
    logger.info(f"Test log message with timestamp: {timestamp}")
    logger.warning(f"Test warning with timestamp: {timestamp}")
    logger.error(f"Test error with timestamp: {timestamp}")
    
    # Log with additional context (for structured logging)
    logger.info(f"User action logged", extra={'extra_fields': {
        'user_action': 'test_logging',
        'timestamp': timestamp,
        'endpoint': '/debug/test-logging'
    }})
    
    return jsonify({
        'message': 'Logging test completed',
        'timestamp': timestamp,
        'check_logs': 'Check Cloud Run logs for the output',
        'log_locations': [
            'Google Cloud Console > Cloud Run > Your Service > Logs',
            'Or use: gcloud run services logs read postify-164860087792 --region=europe-west1'
        ]
    })


@app.route('/debug/env')
def debug_env():
    # Only show in development
    if os.environ.get('FLASK_ENV') == 'production':
        return jsonify({'error': 'Not available in production'}), 403
    
    return jsonify({
        'TIKTOK_CLIENT_KEY': TIKTOK_CLIENT_KEY[:5] + '...' if TIKTOK_CLIENT_KEY else None,
        'TIKTOK_REDIRECT_URI': TIKTOK_REDIRECT_URI,
        'has_secret': bool(TIKTOK_CLIENT_SECRET),
        'has_flask_key': bool(app.secret_key)
    })


@app.route('/debug/tiktok-credentials')
def debug_tiktok_credentials():
    """Test endpoint to verify TikTok credentials - REMOVE IN PRODUCTION"""
    # Only show in development
    if os.environ.get('FLASK_ENV') == 'production':
        return jsonify({'error': 'Not available in production'}), 403
    
    return jsonify({
        'client_key': TIKTOK_CLIENT_KEY,
        'client_secret': TIKTOK_CLIENT_SECRET[:10] + '...' + TIKTOK_CLIENT_SECRET[-4:] if TIKTOK_CLIENT_SECRET else None,
        'redirect_uri': TIKTOK_REDIRECT_URI,
        'auth_url': TIKTOK_AUTH_URL,
        'token_url': TIKTOK_TOKEN_URL,
        'base_url': TIKTOK_BASE_URL,
        'status': 'APPROVED',
        'note': 'Your app has been approved by TikTok! You can now post publicly.',
        'capabilities': ['PUBLIC_POSTING', 'FRIENDS_POSTING', 'PRIVATE_POSTING']
    })


@app.route('/debug/db')
def debug_db():
    # Only show in development
    if os.environ.get('FLASK_ENV') == 'production':
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        # Check database connection and table existence
        result = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in result]
        
        # Count users
        user_count = User.query.count()
        scheduled_post_count = ScheduledPost.query.count()
        
        return jsonify({
            'database_url': app.config['SQLALCHEMY_DATABASE_URI'][:50] + '...',
            'tables': tables,
            'user_count': user_count,
            'scheduled_post_count': scheduled_post_count,
            'db_initialized': hasattr(app, 'db_initialized')
        })
    except Exception as e:
        return jsonify({
            'error': 'Database error',
            'message': str(e),
            'database_url': app.config['SQLALCHEMY_DATABASE_URI'][:50] + '...'
        }), 500


@app.route('/debug/delete-test-user', methods=['DELETE'])
def delete_test_user():
    # Only show in development
    if os.environ.get('FLASK_ENV') == 'production':
        return jsonify({'error': 'Not available in production'}), 403
    
    try:
        test_user = User.query.filter_by(tiktok_user_id='test_user_12345').first()
        
        if not test_user:
            return jsonify({'message': 'Test user not found'})
        
        user_id = test_user.id
        db.session.delete(test_user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Test user {user_id} deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to delete test user',
            'message': str(e)
        }), 500


# Custom decorator removed - using Flask-Login's login_required instead


@app.route('/auth/tiktok')
@login_required
def auth_tiktok():
    # Check if environment variables are loaded
    if not TIKTOK_CLIENT_KEY or not TIKTOK_REDIRECT_URI:
        return jsonify({
            'error': 'Configuration error',
            'has_client_key': bool(TIKTOK_CLIENT_KEY),
            'has_redirect_uri': bool(TIKTOK_REDIRECT_URI),
            'redirect_uri': TIKTOK_REDIRECT_URI
        }), 500
    
    # Store current user ID in session for callback
    session['auth_user_id'] = current_user.id
    
    # Create anti-forgery state token (CSRF protection)
    # Using cryptographically secure random token as per TikTok docs
    csrf_state = secrets.token_urlsafe(32)
    session['csrf_state'] = csrf_state
    
    # Set cookie with state for additional security (optional)
    # This helps prevent session fixation attacks
    
    code_verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    session['code_verifier'] = code_verifier
    
    params = {
        'client_key': TIKTOK_CLIENT_KEY,
        'scope': 'user.info.basic,video.publish',
        'response_type': 'code',
        'redirect_uri': TIKTOK_REDIRECT_URI,
        'state': csrf_state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }

    # Use structured logging for Cloud Run visibility
    logger.info("TikTok authentication initiated", extra={'extra_fields': {
        'client_key': TIKTOK_CLIENT_KEY[:10] + '...' if TIKTOK_CLIENT_KEY else None,
        'redirect_uri': TIKTOK_REDIRECT_URI,
        'scopes': 'user.info.basic,video.publish',
        'state_token': csrf_state[:10] + '...'
    }})
    
    auth_url = f"{TIKTOK_AUTH_URL}?{urlencode(params)}"
    logger.info(f"Redirecting to: {auth_url}")
    return redirect(auth_url)

    # return redirect(f"https://postify-164860087792.europe-west1.run.app?{urlencode(params)}")

@app.route('/auth/tiktok/add')
@login_required
def add_tiktok_account():
    """Route for adding an additional TikTok account"""
    return redirect(url_for('auth_tiktok'))


@app.route('/auth/tiktok/callback')
def tiktok_callback():
    """Handle TikTok OAuth callback
    
    As per TikTok docs, we must:
    1. Verify the state parameter to prevent CSRF attacks
    2. Exchange the authorization code for an access token
    3. Store tokens securely
    4. Handle errors gracefully
    """
    code = request.args.get('code')
    state = request.args.get('state')
    scopes = request.args.get('scopes')  # Granted scopes
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    # Handle authorization errors
    if error:
        logger.error(f"TikTok authorization error: {error} - {error_description}")
        if error == 'access_denied':
            flash('You denied access to TikTok. Please try again.', 'warning')
        else:
            flash(f'Authorization failed: {error_description or error}', 'error')
        return redirect(url_for('index'))
    
    if not code or not state:
        logger.error("Missing code or state parameter in callback")
        flash('Invalid authorization response. Please try again.', 'error')
        return redirect(url_for('index'))
    
    # Verify CSRF state token
    if state != session.get('csrf_state'):
        logger.error(f"State mismatch - expected: {session.get('csrf_state')}, got: {state}")
        flash('Security verification failed. Please try again.', 'error')
        return redirect(url_for('index'))
    
    logger.info(f"Granted scopes: {scopes}")
    
    token_params = {
        'client_key': TIKTOK_CLIENT_KEY,
        'client_secret': TIKTOK_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': TIKTOK_REDIRECT_URI,
        'code_verifier': session.get('code_verifier')
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Cache-Control': 'no-cache'
    }
    
    try:
        response = requests.post(TIKTOK_TOKEN_URL, data=token_params, headers=headers)
        token_data = response.json()
        
        if 'access_token' in token_data:
            # Store all token response fields as per TikTok docs
            session['tiktok_access_token'] = token_data['access_token']
            session['tiktok_refresh_token'] = token_data.get('refresh_token')
            session['tiktok_expires_in'] = token_data.get('expires_in', 86400)  # Default 24 hours
            session['tiktok_refresh_expires_in'] = token_data.get('refresh_expires_in', 31536000)  # Default 365 days
            session['tiktok_scope'] = token_data.get('scope')
            session['tiktok_open_id'] = token_data.get('open_id')
            session['tiktok_token_type'] = token_data.get('token_type', 'Bearer')
            
            logger.info(f"Token received - expires in: {token_data.get('expires_in')} seconds")
            logger.info(f"Refresh token expires in: {token_data.get('refresh_expires_in')} seconds")
            logger.info(f"Scopes granted: {token_data.get('scope')}")
            logger.info(f"Open ID: {token_data.get('open_id')}")
            
            # Fetch user info from TikTok
            user_info_headers = {
                'Authorization': f'Bearer {token_data["access_token"]}'
            }
            
            try:
                # TikTok API requires fields parameter
                user_info_params = {
                    'fields': 'open_id,union_id,avatar_url,display_name,username,follower_count,following_count,likes_count,video_count'
                }
                user_response = requests.get('https://open.tiktokapis.com/v2/user/info/', headers=user_info_headers, params=user_info_params)
                user_data = user_response.json()
                
                logger.info(f"TikTok user response: {user_response.status_code}")
                logger.info(f"TikTok user data: {user_data}")
                
                if 'data' in user_data and 'user' in user_data['data']:
                    tiktok_user = user_data['data']['user']
                    logger.info(f"Processing user: {tiktok_user.get('display_name', 'Unknown')} ({tiktok_user.get('open_id', 'No ID')})")
                    
                    # Calculate token expiration times
                    expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 86400))
                    refresh_expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('refresh_expires_in', 31536000))
                    
                    # SECURITY: Tokens are stored encrypted in database
                    # Client secret is kept in environment variables only
                    # Refresh tokens are stored per user account in database
                    
                    # Get user ID from session (set during auth)
                    auth_user_id = session.get('auth_user_id')
                    if not auth_user_id:
                        logger.error("No user ID in session, cannot associate TikTok account")
                        return jsonify({'error': 'Authentication required'}), 401
                    
                    # Check if TikTok account already exists
                    existing_account = TikTokAccount.query.filter_by(tiktok_user_id=tiktok_user['open_id']).first()
                    
                    if existing_account:
                        logger.info(f"Updating existing TikTok account ID: {existing_account.id}")
                        # Update existing TikTok account
                        existing_account.username = tiktok_user.get('username', '')
                        existing_account.display_name = tiktok_user.get('display_name', '')
                        existing_account.avatar_url = tiktok_user.get('avatar_url', '')
                        existing_account.follower_count = tiktok_user.get('follower_count', 0)
                        existing_account.following_count = tiktok_user.get('following_count', 0)
                        existing_account.likes_count = tiktok_user.get('likes_count', 0)
                        existing_account.video_count = tiktok_user.get('video_count', 0)
                        existing_account.access_token = token_data['access_token']
                        existing_account.refresh_token = token_data.get('refresh_token')
                        existing_account.token_expires_at = expires_at
                        existing_account.refresh_token_expires_at = refresh_expires_at
                        existing_account.scope = token_data.get('scope')
                        existing_account.token_type = token_data.get('token_type', 'Bearer')
                        existing_account.last_login = datetime.utcnow()
                        existing_account.is_active = True
                        tiktok_account = existing_account
                    else:
                        logger.info("Creating new TikTok account")
                        # Create new TikTok account
                        tiktok_account = TikTokAccount(
                            user_id=auth_user_id,
                            tiktok_user_id=tiktok_user['open_id'],
                            username=tiktok_user.get('username', ''),
                            display_name=tiktok_user.get('display_name', ''),
                            avatar_url=tiktok_user.get('avatar_url', ''),
                            follower_count=tiktok_user.get('follower_count', 0),
                            following_count=tiktok_user.get('following_count', 0),
                            likes_count=tiktok_user.get('likes_count', 0),
                            video_count=tiktok_user.get('video_count', 0),
                            access_token=token_data['access_token'],
                            refresh_token=token_data.get('refresh_token'),
                            token_expires_at=expires_at,
                            refresh_token_expires_at=refresh_expires_at,
                            scope=token_data.get('scope'),
                            token_type=token_data.get('token_type', 'Bearer'),
                            last_login=datetime.utcnow(),
                            is_active=True
                        )
                        db.session.add(tiktok_account)
                        logger.info("Added new TikTok account to session")
                    
                    try:
                        db.session.commit()
                        logger.info(f"Successfully committed TikTok account to database. Account ID: {tiktok_account.id}")
                        
                        # Clear auth user ID from session
                        session.pop('auth_user_id', None)
                        logger.info(f"Successfully saved TikTok account for user {auth_user_id}")
                        
                        # Verify account was saved
                        verification_account = TikTokAccount.query.get(tiktok_account.id)
                        if verification_account:
                            logger.info(f"Verified TikTok account exists in database: {verification_account.username}")
                        else:
                            logger.error("TikTok account not found in database after commit!")
                            
                    except Exception as commit_error:
                        logger.error(f"Database commit failed: {commit_error}")
                        db.session.rollback()
                        raise commit_error
                        
                else:
                    logger.warning(f"Invalid TikTok user data response: {user_data}")
                    
                    # If user.info.basic scope not authorized, create minimal TikTok account record
                    if 'error' in user_data and user_data['error'].get('code') == 'scope_not_authorized':
                        logger.info("Creating minimal TikTok account record without profile info due to scope not authorized")
                        
                        # Get user ID from session
                        auth_user_id = session.get('auth_user_id')
                        if not auth_user_id:
                            logger.error("No user ID in session for minimal account")
                            return jsonify({'error': 'Authentication required'}), 401
                        
                        # Generate a unique identifier from the access token
                        token_hash = hashlib.md5(token_data['access_token'].encode()).hexdigest()[:12]
                        
                        # Create minimal TikTok account record
                        minimal_account = TikTokAccount(
                            user_id=auth_user_id,
                            tiktok_user_id=f'limited_user_{token_hash}',
                            username='TikTok User',
                            display_name='TikTok User',
                            avatar_url='',
                            follower_count=0,
                            following_count=0,
                            likes_count=0,
                            video_count=0,
                            access_token=token_data['access_token'],
                            refresh_token=token_data.get('refresh_token'),
                            token_expires_at=datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 86400)),
                            last_login=datetime.utcnow(),
                            is_active=True
                        )
                        
                        try:
                            db.session.add(minimal_account)
                            db.session.commit()
                            session.pop('auth_user_id', None)
                            logger.info(f"Created minimal TikTok account record with ID: {minimal_account.id}")
                        except Exception as commit_error:
                            logger.error(f"Failed to create minimal TikTok account: {commit_error}")
                            db.session.rollback()
                    
            except Exception as e:
                logger.error(f"Error fetching/saving user info: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue anyway - user can still use the app
            
            flash('TikTok account successfully connected!', 'success')
            return redirect(url_for('index'))
        else:
            return jsonify({'error': 'Failed to obtain access token', 'details': token_data}), 400
            
    except Exception as e:
        return jsonify({'error': 'Token exchange failed', 'message': str(e)}), 500


@app.route('/dashboard')
@login_required
def dashboard():
    # Get user's TikTok accounts for dashboard
    tiktok_accounts = TikTokAccount.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard_compliant.html', tiktok_accounts=tiktok_accounts)


@app.route('/schedule_post/<int:account_id>')
@login_required
def schedule_post(account_id):
    """Show the schedule post form for a specific TikTok account"""
    account = TikTokAccount.query.filter_by(id=account_id, user_id=current_user.id).first_or_404()
    return render_template('schedule_post.html', account=account)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/api/accounts/list')
@login_required
def list_tiktok_accounts():
    """List all TikTok accounts for the current user"""
    user_id = current_user.id
    
    accounts = TikTokAccount.query.filter_by(user_id=user_id, is_active=True).all()
    current_account_id = session.get('current_tiktok_account_id')
    
    return jsonify({
        'accounts': [{
            'id': acc.id,
            'username': acc.username,
            'display_name': acc.display_name,
            'avatar_url': acc.avatar_url,
            'follower_count': acc.follower_count,
            'following_count': acc.following_count,
            'likes_count': acc.likes_count,
            'video_count': acc.video_count,
            'is_current': acc.id == current_account_id
        } for acc in accounts],
        'current_account_id': current_account_id
    })


@app.route('/api/accounts/switch/<int:account_id>', methods=['POST'])
@login_required
def switch_tiktok_account(account_id):
    """Switch to a different TikTok account"""
    user_id = current_user.id
    account = TikTokAccount.query.filter_by(id=account_id, user_id=user_id, is_active=True).first()
    
    if not account:
        return jsonify({'error': 'Account not found or not authorized'}), 404
    
    # Update session with new account
    session['current_tiktok_account_id'] = account.id
    session['tiktok_access_token'] = account.access_token
    
    return jsonify({
        'success': True,
        'account': {
            'id': account.id,
            'username': account.username,
            'display_name': account.display_name,
            'avatar_url': account.avatar_url
        }
    })


@app.route('/api/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_tiktok_account(account_id):
    """Remove a TikTok account (soft delete) and revoke access"""
    user_id = current_user.id
    account = TikTokAccount.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    # Revoke access token from TikTok before deletion
    if account.access_token:
        revoked = revoke_tiktok_token(account.access_token)
        if revoked:
            logger.info(f"Successfully revoked TikTok access for account {account.username}")
        else:
            logger.warning(f"Failed to revoke TikTok access for account {account.username}")
    
    # Soft delete the account
    account.is_active = False
    db.session.commit()
    
    # Check if this was the last active account
    active_accounts = TikTokAccount.query.filter_by(user_id=user_id, is_active=True).count()
    
    # If this was the current account, try to switch to another one
    if session.get('current_tiktok_account_id') == account_id:
        if active_accounts > 0:
            # Switch to another active account
            other_account = TikTokAccount.query.filter_by(user_id=user_id, is_active=True).first()
            session['current_tiktok_account_id'] = other_account.id
            session['tiktok_access_token'] = other_account.access_token
        else:
            # No accounts left, clear session data
            session.pop('current_tiktok_account_id', None)
            session.pop('tiktok_access_token', None)
    
    message = 'Account removed successfully'
    if active_accounts == 0:
        message += '. You now have no connected TikTok accounts.'
    
    return jsonify({
        'success': True, 
        'message': message,
        'accounts_remaining': active_accounts
    })


@app.route('/api/accounts/reauth/<int:account_id>', methods=['POST'])
@login_required
def force_reauth_account(account_id):
    """Force re-authentication for a TikTok account to get fresh tokens"""
    user_id = current_user.id
    account = TikTokAccount.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    # Store account ID in session for re-authentication
    session['reauth_account_id'] = account_id
    session['auth_user_id'] = user_id
    
    return jsonify({
        'success': True,
        'message': 'Please re-authenticate to get fresh tokens',
        'auth_url': '/auth/tiktok'
    })


@app.route('/api/accounts/refresh/<int:account_id>', methods=['POST'])
@login_required
def force_refresh_token(account_id):
    """Force refresh the access token for a TikTok account"""
    user_id = current_user.id
    account = TikTokAccount.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    if not account.refresh_token:
        return jsonify({
            'error': 'No refresh token available',
            'message': 'Please re-authenticate your TikTok account'
        }), 400
    
    logger.info(f"Force refreshing token for account {account.username}")
    refreshed = refresh_tiktok_token(account)
    
    if refreshed:
        return jsonify({
            'success': True,
            'message': 'Token refreshed successfully',
            'token_expires_at': account.token_expires_at.isoformat() if account.token_expires_at else None,
            'scope': account.scope
        })
    else:
        return jsonify({
            'error': 'Token refresh failed',
            'message': 'Please re-authenticate your TikTok account'
        }), 400


@app.route('/api/accounts/debug/<int:account_id>')
@login_required
def debug_account_tokens(account_id):
    """Debug endpoint to check token status"""
    user_id = current_user.id
    account = TikTokAccount.query.filter_by(id=account_id, user_id=user_id).first()
    
    if not account:
        return jsonify({'error': 'Account not found'}), 404
    
    # Check token age
    token_age = None
    if account.token_expires_at:
        token_age = (account.token_expires_at - datetime.utcnow()).total_seconds()
    
    return jsonify({
        'account_id': account.id,
        'username': account.username,
        'has_access_token': bool(account.access_token),
        'has_refresh_token': bool(account.refresh_token),
        'token_expires_at': account.token_expires_at.isoformat() if account.token_expires_at else None,
        'token_age_seconds': token_age,
        'token_expired': token_age < 0 if token_age else None,
        'scope': account.scope,
        'last_login': account.last_login.isoformat() if account.last_login else None,
        'created_at': account.created_at.isoformat() if account.created_at else None
    })


@app.route('/api/user/info')
@login_required
def get_user_info():
    """Get information about the current user and their TikTok accounts"""
    user = current_user
    
    # Get all TikTok accounts for this user
    tiktok_accounts = TikTokAccount.query.filter_by(user_id=user.id, is_active=True).all()
    
    if not tiktok_accounts:
        # Return basic user info if no TikTok accounts connected
        return jsonify({
            'data': {
                'user': {
                    'email': user.email,
                    'is_verified': user.is_verified,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'tiktok_accounts': []
                }
            }
        })
    
    # If user has TikTok accounts, return the first one's data (for backward compatibility)
    # You might want to modify this to return all accounts
    primary_account = tiktok_accounts[0]
    
    # Try to get fresh data from TikTok API if we have an access token
    if primary_account.access_token:
        headers = {
            'Authorization': f'Bearer {primary_account.access_token}'
        }
        
        try:
            # TikTok API requires fields parameter
            user_info_params = {
                'fields': 'open_id,union_id,avatar_url,display_name,username,follower_count,following_count,likes_count,video_count'
            }
            response = requests.get('https://open.tiktokapis.com/v2/user/info/', headers=headers, params=user_info_params)
            api_data = response.json()
            
            # If API call successful, update local database and return fresh data
            if response.ok and 'data' in api_data and 'user' in api_data['data']:
                tiktok_user = api_data['data']['user']
                
                # Update local database with fresh data
                primary_account.username = tiktok_user.get('username', primary_account.username)
                primary_account.display_name = tiktok_user.get('display_name', primary_account.display_name)
                primary_account.avatar_url = tiktok_user.get('avatar_url', primary_account.avatar_url)
                primary_account.follower_count = tiktok_user.get('follower_count', primary_account.follower_count)
                primary_account.following_count = tiktok_user.get('following_count', primary_account.following_count)
                primary_account.likes_count = tiktok_user.get('likes_count', primary_account.likes_count)
                primary_account.video_count = tiktok_user.get('video_count', primary_account.video_count)
                db.session.commit()
                
                return jsonify(api_data)
                
        except Exception as e:
            logger.warning(f"TikTok API failed, falling back to database: {e}")
    
    # Fallback to local database data
    return jsonify({
        'data': {
            'user': {
                'open_id': primary_account.tiktok_user_id,
                'union_id': primary_account.tiktok_user_id,
                'username': primary_account.username or 'N/A',
                'display_name': primary_account.display_name or 'User',
                'avatar_url': primary_account.avatar_url or '',
                'follower_count': primary_account.follower_count or 0,
                'following_count': primary_account.following_count or 0,
                'likes_count': primary_account.likes_count or 0,
                'video_count': primary_account.video_count or 0
            }
        }
    })


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def revoke_tiktok_token(access_token):
    """Revoke a TikTok access token
    
    As per TikTok docs:
    - This removes the app from user's authorized apps list
    - Returns empty response on success
    """
    try:
        revoke_params = {
            'client_key': TIKTOK_CLIENT_KEY,
            'client_secret': TIKTOK_CLIENT_SECRET,
            'token': access_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cache-Control': 'no-cache'
        }
        
        logger.info("Attempting to revoke TikTok access token")
        response = requests.post(
            'https://open.tiktokapis.com/v2/oauth/revoke/',
            data=revoke_params,
            headers=headers
        )
        
        if response.status_code == 200:
            # Success - response should be empty
            logger.info("Token revoked successfully")
            return True
        else:
            # Error response
            try:
                error_data = response.json()
                logger.error(f"Token revocation failed: {error_data}")
                if 'error' in error_data:
                    logger.error(f"Error: {error_data['error']} - {error_data.get('error_description', '')}")
            except:
                logger.error(f"Token revocation failed with status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Error revoking token: {str(e)}")
        return False


def refresh_tiktok_token(tiktok_account):
    """Refresh TikTok access token using refresh token
    
    As per TikTok docs:
    - The refresh_token may change, always use the new one
    - Access tokens expire in 24 hours (86400 seconds)
    - Refresh tokens expire in 365 days (31536000 seconds)
    """
    if not tiktok_account.refresh_token:
        logger.warning(f"No refresh token available for account {tiktok_account.username}")
        return False
    
    try:
        token_params = {
            'client_key': TIKTOK_CLIENT_KEY,
            'client_secret': TIKTOK_CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': tiktok_account.refresh_token
        }
        
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Cache-Control': 'no-cache'
        }
        
        logger.info(f"Attempting to refresh token for account {tiktok_account.username}")
        response = requests.post(TIKTOK_TOKEN_URL, data=token_params, headers=headers)
        token_data = response.json()
        
        logger.info(f"Token refresh response: {response.status_code}")
        
        if response.status_code == 200 and 'access_token' in token_data:
            # Update ALL token fields as per TikTok documentation
            tiktok_account.access_token = token_data['access_token']
            
            # IMPORTANT: The refresh_token may be different than the one used
            # Always update to the new refresh_token if provided
            if 'refresh_token' in token_data:
                old_refresh = tiktok_account.refresh_token
                new_refresh = token_data['refresh_token']
                if old_refresh != new_refresh:
                    logger.info("Refresh token changed, updating to new token")
                tiktok_account.refresh_token = new_refresh
            
            # Update expiration times
            if 'expires_in' in token_data:
                tiktok_account.token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            
            # Store additional fields if needed
            if 'refresh_expires_in' in token_data:
                tiktok_account.refresh_token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['refresh_expires_in'])
            
            # Update scope if changed
            if 'scope' in token_data:
                tiktok_account.scope = token_data['scope']
            
            db.session.commit()
            logger.info(f"Token refreshed successfully for account {tiktok_account.username}")
            logger.info(f"New token expires in: {token_data.get('expires_in', 'unknown')} seconds")
            return True
        else:
            logger.error(f"Token refresh failed: {token_data}")
            if 'error' in token_data:
                logger.error(f"Error: {token_data['error']} - {token_data.get('error_description', '')}")
            return False
            
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False


@app.route('/api/creator/info')
@login_required
def get_creator_info():
    access_token = session.get('tiktok_access_token')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    
    try:
        response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/creator_info/query/',
            headers=headers
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': 'Failed to fetch creator info', 'message': str(e)}), 500


@app.route('/api/post/video', methods=['POST'])
@login_required
def post_video():
    try:
        data = request.get_json()
        
        # REVIEW MODE CHECK
        if TikTokConfig.is_in_review_mode():
            privacy_level = data.get('privacy_level')
            if privacy_level and privacy_level != 'SELF_ONLY':
                logger.warning(f"Review mode: Forcing privacy to SELF_ONLY (was: {privacy_level})")
                data['privacy_level'] = 'SELF_ONLY'

        # Get the target account from the request
        tiktok_account_id = data.get('tiktok_account_id')
        if not tiktok_account_id:
            return jsonify({'error': 'Missing tiktok_account_id in request'}), 400

        # Get the account and its access token
        tiktok_account = TikTokAccount.query.filter_by(
            id=tiktok_account_id,
            user_id=current_user.id,
            is_active=True
        ).first()

        if not tiktok_account:
            return jsonify({'error': 'TikTok account not found or not authorized'}), 404

        access_token = tiktok_account.access_token
        if not access_token:
            return jsonify({'error': 'No access token found for this account'}), 401

        # Check if token is expired
        if tiktok_account.token_expires_at and tiktok_account.token_expires_at < datetime.utcnow():
            logger.warning(f"Access token expired for account {tiktok_account.username}")
            # Try to refresh the token
            refreshed = refresh_tiktok_token(tiktok_account)
            if not refreshed:
                return jsonify({
                    'error': 'Access token expired and refresh failed',
                    'message': 'Please reconnect your TikTok account'
                }), 401
            access_token = tiktok_account.access_token

        logger.info(f"Using account: {tiktok_account.username} (ID: {tiktok_account.id})")
        logger.info(f"Token created at: {tiktok_account.created_at}")
        logger.info(f"Token last refreshed: {tiktok_account.last_login}")
        logger.info(f"Token scope: {tiktok_account.scope}")
        
        # Log token age
        if tiktok_account.created_at:
            token_age_days = (datetime.utcnow() - tiktok_account.created_at).days
            logger.info(f"Account age: {token_age_days} days")
            if token_age_days > 7:
                logger.warning(f"Token is {token_age_days} days old - consider re-authenticating for fresh permissions")

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }

        # Prepare post info
        post_info = {
            'title': data.get('title', ''),
            'privacy_level': data.get('privacy_level', 'PUBLIC_TO_EVERYONE'),
            'disable_duet': data.get('disable_duet', False),
            'disable_comment': data.get('disable_comment', False),
            'disable_stitch': data.get('disable_stitch', False),
            'video_cover_timestamp_ms': data.get('video_cover_timestamp_ms', 1000)
        }

        # Prepare source info based on upload type
        source_type = data.get('source_type', 'PULL_FROM_URL')

        if source_type == 'PULL_FROM_URL':
            source_info = {
                'source': 'PULL_FROM_URL',
                'video_url': data.get('video_url')
            }
        else:
            # FILE_UPLOAD
            video_size = data.get('video_size', 0)
            # For single chunk upload, chunk_size must equal video_size
            source_info = {
                'source': 'FILE_UPLOAD',
                'video_size': video_size,
                'chunk_size': video_size,  # Must match video_size for single chunk
                'total_chunk_count': 1
            }

        request_body = {
            'post_info': post_info,
            'source_info': source_info
        }
    except Exception as e:
        return jsonify({'error': 'Failed to fetch video info', 'message': str(e)}), 500

    try:
        logger.info(f"TikTok video init request", extra={'extra_fields': {
            'privacy_level': post_info.get('privacy_level'),
            'source_type': source_type,
            'account_id': tiktok_account_id
        }})
        response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/video/init/',
            headers=headers,
            json=request_body
        )

        logger.info(f"TikTok video init response status: {response.status_code}")
        response_data = response.json()
        logger.info(f"TikTok video init response: {response_data}")
        
        # Check if the response contains an error
        if response.status_code != 200:
            logger.error(f"TikTok API error: {response_data}")
            
            # If token is invalid, try to refresh it once
            if ('error' in response_data and 
                response_data['error'].get('code') == 'access_token_invalid'):
                logger.info("Access token invalid, attempting refresh...")
                refreshed = refresh_tiktok_token(tiktok_account)
                if refreshed:
                    logger.info("Token refreshed, retrying request...")
                    # Update headers with new token
                    headers['Authorization'] = f'Bearer {tiktok_account.access_token}'
                    # Retry the request
                    response = requests.post(
                        f'{TIKTOK_BASE_URL}/post/publish/video/init/',
                        headers=headers,
                        json=request_body
                    )
                    response_data = response.json()
                    logger.info(f"Retry response: {response_data}")
                    if response.status_code == 200:
                        # Success after refresh, continue with normal flow
                        pass
                    else:
                        return jsonify({
                            'error': 'TikTok API error after token refresh',
                            'status_code': response.status_code,
                            'response': response_data
                        }), response.status_code
                else:
                    return jsonify({
                        'error': 'Access token invalid and refresh failed',
                        'message': 'Please reconnect your TikTok account'
                    }), 401
            else:
                return jsonify({
                    'error': 'TikTok API error',
                    'status_code': response.status_code,
                    'response': response_data
                }), response.status_code
        
        # For FILE_UPLOAD, ensure upload_url is present in the response
        if source_type == 'FILE_UPLOAD':
            if 'data' not in response_data or 'upload_url' not in response_data.get('data', {}):
                logger.error(f"Missing upload_url in TikTok response: {response_data}")
                return jsonify({
                    'error': 'TikTok did not provide upload_url',
                    'response': response_data
                }), 400
        
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Error initiating video post: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to initiate video post', 'message': str(e)}), 500


@app.route('/api/post/upload', methods=['POST'])
@login_required
def upload_video():
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = str(int(time.time()))
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Get file size
        file_size = os.path.getsize(filepath)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'filepath': filepath,
            'size': file_size
        })
    
    return jsonify({'error': 'Invalid file type'}), 400


@app.route('/api/post/upload/chunk', methods=['PUT'])
@login_required
def upload_video_chunk():
    data = request.get_json()
    logger.info(f"Chunk upload request data: {data}")
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    upload_url = data.get('upload_url')
    video_path = data.get('video_path')
    
    logger.info(f"Upload URL: {upload_url}")
    logger.info(f"Video Path: {video_path}")
    
    if not upload_url or not video_path:
        return jsonify({
            'error': 'Missing upload_url or video_path',
            'received_data': {
                'upload_url': bool(upload_url),
                'video_path': bool(video_path),
                'data_keys': list(data.keys()) if data else []
            }
        }), 400
    
    try:
        # Check if video file exists
        if not os.path.exists(video_path):
            return jsonify({'error': f'Video file not found: {video_path}'}), 404
        
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
            
        logger.info(f"Video file size: {len(video_data)} bytes")
            
        headers = {
            'Content-Type': 'video/mp4',
            'Content-Range': f'bytes 0-{len(video_data)-1}/{len(video_data)}'
        }
        
        logger.info(f"Uploading to TikTok URL: {upload_url[:50]}...")
        response = requests.put(upload_url, data=video_data, headers=headers)
        logger.info(f"TikTok upload response status: {response.status_code}")
        
        return jsonify({
            'success': response.status_code in [200, 201],
            'status_code': response.status_code,
            'response_text': response.text[:200] if response.text else None
        })
    except Exception as e:
        logger.error(f"Error uploading video chunk: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to upload video chunk', 'message': str(e)}), 500


@app.route('/api/post/status/<publish_id>')
@login_required
def get_post_status(publish_id):
    access_token = session.get('tiktok_access_token')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    
    request_body = {
        'publish_id': publish_id
    }
    
    try:
        response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/status/fetch/',
            headers=headers,
            json=request_body
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': 'Failed to fetch post status', 'message': str(e)}), 500


@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database initialized!")


@app.route('/api/register', methods=['POST'])
@login_required
def register_user():
    """Manual user registration endpoint (alternative to automatic registration during login)"""
    if current_user.is_authenticated:
        user = current_user
        if user:
            return jsonify({
                'message': 'User already registered',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'display_name': user.display_name,
                    'avatar_url': user.avatar_url
                }
            }), 200
    
    # If not registered, fetch user info and register
    access_token = session.get('tiktok_access_token')
    headers = {'Authorization': f'Bearer {access_token}'}
    
    try:
        # TikTok API requires fields parameter
        user_info_params = {
            'fields': 'open_id,union_id,avatar_url,display_name,username,follower_count,following_count,likes_count,video_count'
        }
        response = requests.get('https://open.tiktokapis.com/v2/user/info/', headers=headers, params=user_info_params)
        user_data = response.json()
        
        if 'data' in user_data and 'user' in user_data['data']:
            tiktok_user = user_data['data']['user']
            
            # Create or update user
            user = User.query.filter_by(tiktok_user_id=tiktok_user['open_id']).first()
            
            if not user:
                user = User(tiktok_user_id=tiktok_user['open_id'])
                db.session.add(user)
            
            # Update user info
            user.username = tiktok_user.get('username', '')
            user.display_name = tiktok_user.get('display_name', '')
            user.avatar_url = tiktok_user.get('avatar_url', '')
            user.follower_count = tiktok_user.get('follower_count', 0)
            user.following_count = tiktok_user.get('following_count', 0)
            user.likes_count = tiktok_user.get('likes_count', 0)
            user.video_count = tiktok_user.get('video_count', 0)
            user.last_login = datetime.utcnow()
            
            db.session.commit()
            # User is now registered and logged in via Flask-Login
            
            return jsonify({
                'message': 'User registered successfully',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'display_name': user.display_name,
                    'avatar_url': user.avatar_url
                }
            }), 201
            
    except Exception as e:
        return jsonify({'error': 'Failed to register user', 'message': str(e)}), 500


def create_scheduler_job(scheduled_post_id, scheduled_time):
    """Create a Google Cloud Scheduler job for a scheduled post"""
    try:
        # Check required environment variables
        if not GOOGLE_CLOUD_PROJECT:
            logger.error("GOOGLE_CLOUD_PROJECT environment variable not set")
            return None
        
        if not SCHEDULER_SERVICE_URL:
            logger.error("SCHEDULER_SERVICE_URL environment variable not set")
            return None
            
        client = scheduler.CloudSchedulerClient()
        parent = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{GOOGLE_CLOUD_LOCATION}"
        
        # Create unique job name
        job_name = f"{parent}/jobs/scheduled-post-{scheduled_post_id}"
        
        # Convert datetime to cron expression
        cron_expression = f"{scheduled_time.minute} {scheduled_time.hour} {scheduled_time.day} {scheduled_time.month} *"
        
        # Job payload - will call our webhook endpoint
        payload = {
            'scheduled_post_id': scheduled_post_id
        }
        
        job = {
            'name': job_name,
            'http_target': {
                'uri': f"{SCHEDULER_SERVICE_URL}/api/scheduled/execute",
                'http_method': scheduler.HttpMethod.POST,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(payload).encode('utf-8')
            },
            'schedule': cron_expression,
            'time_zone': 'UTC'
        }
        
        logger.info(f"Creating scheduler job: {job_name} with schedule: {cron_expression}")
        response = client.create_job(parent=parent, job=job)
        logger.info(f"Scheduler job created successfully: {response.name}")
        return response.name
        
    except Exception as e:
        logger.error(f"Failed to create scheduler job for post {scheduled_post_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def delete_scheduler_job(job_name):
    """Delete a Google Cloud Scheduler job"""
    try:
        client = scheduler.CloudSchedulerClient()
        client.delete_job(name=job_name)
        return True
    except Exception as e:
        logger.error(f"Failed to delete scheduler job: {e}")
        return False


@app.route('/api/scheduled/create', methods=['POST'])
@login_required
def create_scheduled_post():
    """Create a new scheduled post"""
    user_id = current_user.id
    
    # Handle both JSON and form data
    if request.is_json:
        data = request.get_json()
    else:
        data = request.form.to_dict()
    
    # Validate required fields
    required_fields = ['title', 'scheduled_time', 'tiktok_account_id']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Verify the TikTok account belongs to the current user
    tiktok_account = TikTokAccount.query.filter_by(
        id=data['tiktok_account_id'],
        user_id=user_id
    ).first()
    
    if not tiktok_account:
        return jsonify({'error': 'TikTok account not found or unauthorized'}), 404
    
    # Verify the TikTok account belongs to the user
    tiktok_account_id = data.get('tiktok_account_id')
    tiktok_account = TikTokAccount.query.filter_by(id=tiktok_account_id, user_id=user_id, is_active=True).first()
    if not tiktok_account:
        return jsonify({'error': 'TikTok account not found or not authorized'}), 404
    
    try:
        # Parse scheduled time
        scheduled_time = datetime.fromisoformat(data['scheduled_time'].replace('Z', '+00:00'))
        
        # Create scheduled post record
        scheduled_post = ScheduledPost(
            user_id=user_id,
            tiktok_account_id=tiktok_account_id,
            title=data['title'],
            description=data.get('description', ''),
            video_url=data.get('video_url'),
            video_path=data.get('video_path'),
            privacy_level=data.get('privacy_level', 'PUBLIC_TO_EVERYONE'),
            disable_duet=data.get('disable_duet', False),
            disable_comment=data.get('disable_comment', False),
            disable_stitch=data.get('disable_stitch', False),
            video_cover_timestamp_ms=data.get('video_cover_timestamp_ms', 1000),
            scheduled_time=scheduled_time,
            status='pending'
        )
        
        db.session.add(scheduled_post)
        db.session.commit()
        
        # Create Google Cloud Scheduler job (optional)
        job_created = False
        if GOOGLE_CLOUD_PROJECT and SCHEDULER_SERVICE_URL:
            try:
                job_name = create_scheduler_job(scheduled_post.id, scheduled_time)
                if job_name:
                    job_created = True
                    logger.info(f"Scheduler job created: {job_name}")
                else:
                    logger.warning(f"Failed to create scheduler job for post {scheduled_post.id}")
            except Exception as e:
                logger.warning(f"Scheduler not available: {e}")
        else:
            logger.info("Google Cloud Scheduler not configured - posts will be stored but not automatically executed")
        
        return jsonify({
            'success': True,
            'scheduled_post_id': scheduled_post.id,
            'scheduler_job_created': job_created,
            'message': 'Scheduled post created successfully' + (' with automatic scheduling' if job_created else ' (manual execution required)')
        }), 201
        
    except ValueError as e:
        return jsonify({'error': 'Invalid datetime format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to create scheduled post', 'message': str(e)}), 500


@app.route('/api/scheduled/list', methods=['GET'])
@login_required
def list_scheduled_posts():
    """Get all scheduled posts for the current user"""
    user_id = current_user.id
    
    try:
        scheduled_posts = ScheduledPost.query.filter_by(user_id=user_id).order_by(ScheduledPost.scheduled_time.desc()).all()
        
        posts_data = []
        for post in scheduled_posts:
            posts_data.append({
                'id': post.id,
                'title': post.title,
                'description': post.description,
                'video_url': post.video_url,
                'privacy_level': post.privacy_level,
                'scheduled_time': post.scheduled_time.isoformat() if post.scheduled_time else None,
                'status': post.status,
                'error_message': post.error_message,
                'posted_at': post.posted_at.isoformat() if post.posted_at else None,
                'created_at': post.created_at.isoformat() if post.created_at else None
            })
        
        return jsonify({'scheduled_posts': posts_data})
        
    except Exception as e:
        return jsonify({'error': 'Failed to fetch scheduled posts', 'message': str(e)}), 500


@app.route('/api/scheduled/<int:post_id>', methods=['DELETE'])
@login_required
def delete_scheduled_post(post_id):
    """Delete a scheduled post and its scheduler job"""
    user_id = current_user.id
    
    
    try:
        scheduled_post = ScheduledPost.query.filter_by(id=post_id, user_id=user_id).first()
        
        if not scheduled_post:
            return jsonify({'error': 'Scheduled post not found'}), 404
        
        # Delete scheduler job if exists
        if GOOGLE_CLOUD_PROJECT:
            job_name = f"projects/{GOOGLE_CLOUD_PROJECT}/locations/{GOOGLE_CLOUD_LOCATION}/jobs/scheduled-post-{post_id}"
            delete_scheduler_job(job_name)
        
        # Delete from database
        db.session.delete(scheduled_post)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Scheduled post deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to delete scheduled post', 'message': str(e)}), 500


@app.route('/api/scheduled/execute', methods=['POST'])
def execute_scheduled_post():
    """Webhook endpoint called by Google Cloud Scheduler to execute a scheduled post"""
    data = request.get_json()
    scheduled_post_id = data.get('scheduled_post_id')
    
    if not scheduled_post_id:
        return jsonify({'error': 'Missing scheduled_post_id'}), 400
    
    try:
        scheduled_post = ScheduledPost.query.get(scheduled_post_id)
        
        if not scheduled_post:
            return jsonify({'error': 'Scheduled post not found'}), 404
        
        if scheduled_post.status != 'pending':
            return jsonify({'error': 'Post is not in pending status'}), 400
        
        # Update status to processing
        scheduled_post.status = 'processing'
        db.session.commit()
        
        # Get user's access token
        user = User.query.get(scheduled_post.user_id)
        if not user or not user.access_token:
            scheduled_post.status = 'failed'
            scheduled_post.error_message = 'User access token not found'
            db.session.commit()
            return jsonify({'error': 'User access token not found'}), 400
        
        # Prepare TikTok API request
        headers = {
            'Authorization': f'Bearer {user.access_token}',
            'Content-Type': 'application/json; charset=UTF-8'
        }
        
        post_info = {
            'title': scheduled_post.title,
            'privacy_level': scheduled_post.privacy_level,
            'disable_duet': scheduled_post.disable_duet,
            'disable_comment': scheduled_post.disable_comment,
            'disable_stitch': scheduled_post.disable_stitch,
            'video_cover_timestamp_ms': scheduled_post.video_cover_timestamp_ms
        }
        
        # Determine source type
        if scheduled_post.video_url:
            source_info = {
                'source': 'PULL_FROM_URL',
                'video_url': scheduled_post.video_url
            }
        elif scheduled_post.video_path and os.path.exists(scheduled_post.video_path):
            video_size = os.path.getsize(scheduled_post.video_path)
            source_info = {
                'source': 'FILE_UPLOAD',
                'video_size': video_size,
                'chunk_size': video_size,
                'total_chunk_count': 1
            }
        else:
            scheduled_post.status = 'failed'
            scheduled_post.error_message = 'No valid video source found'
            db.session.commit()
            return jsonify({'error': 'No valid video source found'}), 400
        
        request_body = {
            'post_info': post_info,
            'source_info': source_info
        }
        
        # Make TikTok API request
        response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/video/init/',
            headers=headers,
            json=request_body
        )
        
        response_data = response.json()
        
        if response.status_code == 200 and 'data' in response_data:
            # If file upload, handle the upload process
            if scheduled_post.video_path and 'upload_url' in response_data['data']:
                upload_url = response_data['data']['upload_url']
                
                # Upload video file
                with open(scheduled_post.video_path, 'rb') as video_file:
                    video_data = video_file.read()
                    
                upload_headers = {
                    'Content-Type': 'video/mp4',
                    'Content-Range': f'bytes 0-{len(video_data)-1}/{len(video_data)}'
                }
                
                upload_response = requests.put(upload_url, data=video_data, headers=upload_headers)
                
                if upload_response.status_code != 200:
                    scheduled_post.status = 'failed'
                    scheduled_post.error_message = 'Failed to upload video file'
                    db.session.commit()
                    return jsonify({'error': 'Failed to upload video file'}), 500
            
            # Update post as completed
            scheduled_post.status = 'completed'
            scheduled_post.posted_at = datetime.utcnow()
            scheduled_post.post_id = response_data['data'].get('publish_id')
            db.session.commit()
            
            return jsonify({'success': True, 'message': 'Post published successfully'})
        
        else:
            scheduled_post.status = 'failed'
            scheduled_post.error_message = response_data.get('error', {}).get('message', 'Unknown error')
            db.session.commit()
            return jsonify({'error': 'Failed to publish post', 'details': response_data}), 400
            
    except Exception as e:
        if scheduled_post_id:
            scheduled_post = ScheduledPost.query.get(scheduled_post_id)
            if scheduled_post:
                scheduled_post.status = 'failed'
                scheduled_post.error_message = str(e)
                db.session.commit()
        
        return jsonify({'error': 'Failed to execute scheduled post', 'message': str(e)}), 500


# Register blueprints
from auth import auth_bp
app.register_blueprint(auth_bp)

# Register compliance blueprint for review mode
from api_compliance import compliance_bp
app.register_blueprint(compliance_bp)

# Register display API blueprint
from display_api import display_bp
app.register_blueprint(display_bp)

if __name__ == '__main__':
    # Database is already initialized in init_app() above
    port = int(os.environ.get('PORT', 8080))
    
    # Log startup information
    logger.info("="*60)
    logger.info("Starting Postify TikTok Application")
    logger.info(f"Port: {port}")
    logger.info(f"Environment: {os.environ.get('FLASK_ENV', 'development')}")
    logger.info(f"Database URL: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
    logger.info(f"TikTok Client Key: {TIKTOK_CLIENT_KEY}")
    logger.info(f"TikTok Redirect URI: {TIKTOK_REDIRECT_URI}")
    logger.info("="*60)
    
    # Force flush
    sys.stdout.flush()
    sys.stderr.flush()
    
    app.run(host='0.0.0.0', port=port, debug=False)
