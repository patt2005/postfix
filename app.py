import os
import secrets
import requests
from flask import Flask, render_template, redirect, request, session, jsonify, url_for, send_from_directory
from dotenv import load_dotenv
from urllib.parse import urlencode
from functools import wraps
from werkzeug.utils import secure_filename
import time
import hashlib
import base64
from datetime import datetime, timedelta
from flask_migrate import Migrate
from models import db, User, ScheduledPost
from google.cloud import scheduler
import json

load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', secrets.token_urlsafe(32))

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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'tiktok_access_token' not in session:
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/auth/tiktok')
def tiktok_auth():
    # Check if environment variables are loaded
    if not TIKTOK_CLIENT_KEY or not TIKTOK_REDIRECT_URI:
        return jsonify({
            'error': 'Configuration error',
            'has_client_key': bool(TIKTOK_CLIENT_KEY),
            'has_redirect_uri': bool(TIKTOK_REDIRECT_URI),
            'redirect_uri': TIKTOK_REDIRECT_URI
        }), 500
    
    csrf_state = secrets.token_urlsafe(32)
    session['csrf_state'] = csrf_state
    
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
    
    auth_url = f"{TIKTOK_AUTH_URL}?{urlencode(params)}"
    return redirect(auth_url)


@app.route('/auth/tiktok/callback')
def tiktok_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    error_description = request.args.get('error_description')
    
    if error:
        return jsonify({'error': error, 'description': error_description}), 400
    
    if not code or not state:
        return jsonify({'error': 'Missing code or state parameter'}), 400
    
    if state != session.get('csrf_state'):
        return jsonify({'error': 'Invalid state parameter'}), 400
    
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
            session['tiktok_access_token'] = token_data['access_token']
            session['tiktok_refresh_token'] = token_data.get('refresh_token')
            session['tiktok_expires_in'] = token_data.get('expires_in')
            session['tiktok_scope'] = token_data.get('scope')
            
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
                    
                    # Calculate token expiration time
                    expires_at = datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 86400))
                    
                    # Check if user exists
                    existing_user = User.query.filter_by(tiktok_user_id=tiktok_user['open_id']).first()
                    
                    if existing_user:
                        logger.info(f"Updating existing user ID: {existing_user.id}")
                        # Update existing user
                        existing_user.username = tiktok_user.get('username', '')
                        existing_user.display_name = tiktok_user.get('display_name', '')
                        existing_user.avatar_url = tiktok_user.get('avatar_url', '')
                        existing_user.follower_count = tiktok_user.get('follower_count', 0)
                        existing_user.following_count = tiktok_user.get('following_count', 0)
                        existing_user.likes_count = tiktok_user.get('likes_count', 0)
                        existing_user.video_count = tiktok_user.get('video_count', 0)
                        existing_user.access_token = token_data['access_token']
                        existing_user.refresh_token = token_data.get('refresh_token')
                        existing_user.token_expires_at = expires_at
                        existing_user.last_login = datetime.utcnow()
                        user = existing_user
                    else:
                        logger.info("Creating new user")
                        # Create new user
                        user = User(
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
                            last_login=datetime.utcnow()
                        )
                        db.session.add(user)
                        logger.info("Added new user to session")
                    
                    try:
                        db.session.commit()
                        logger.info(f"Successfully committed user to database. User ID: {user.id}")
                        
                        # Store user ID in session
                        session['user_id'] = user.id
                        logger.info(f"Stored user_id {user.id} in session")
                        
                        # Verify user was saved
                        verification_user = User.query.get(user.id)
                        if verification_user:
                            logger.info(f"Verified user exists in database: {verification_user.username}")
                        else:
                            logger.error("User not found in database after commit!")
                            
                    except Exception as commit_error:
                        logger.error(f"Database commit failed: {commit_error}")
                        db.session.rollback()
                        raise commit_error
                        
                else:
                    logger.warning(f"Invalid TikTok user data response: {user_data}")
                    
                    # If user.info.basic scope not authorized, create minimal user record
                    if 'error' in user_data and user_data['error'].get('code') == 'scope_not_authorized':
                        logger.info("Creating minimal user record without profile info due to scope not authorized")
                        
                        # Generate a unique identifier from the access token
                        import hashlib
                        token_hash = hashlib.md5(token_data['access_token'].encode()).hexdigest()[:12]
                        
                        # Create minimal user record
                        minimal_user = User(
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
                            last_login=datetime.utcnow()
                        )
                        
                        try:
                            db.session.add(minimal_user)
                            db.session.commit()
                            session['user_id'] = minimal_user.id
                            logger.info(f"Created minimal user record with ID: {minimal_user.id}")
                        except Exception as commit_error:
                            logger.error(f"Failed to create minimal user: {commit_error}")
                            db.session.rollback()
                    
            except Exception as e:
                logger.error(f"Error fetching/saving user info: {str(e)}")
                import traceback
                logger.error(traceback.format_exc())
                # Continue anyway - user can still use the app
            
            return redirect(url_for('dashboard'))
        else:
            return jsonify({'error': 'Failed to obtain access token', 'details': token_data}), 400
            
    except Exception as e:
        return jsonify({'error': 'Token exchange failed', 'message': str(e)}), 500


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


@app.route('/api/user/info')
@login_required
def get_user_info():
    user_id = session.get('user_id')
    access_token = session.get('tiktok_access_token')
    
    # First try to get fresh data from TikTok API
    if access_token:
        headers = {
            'Authorization': f'Bearer {access_token}'
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
                if user_id:
                    user = User.query.get(user_id)
                    if user:
                        user.username = tiktok_user.get('username', user.username)
                        user.display_name = tiktok_user.get('display_name', user.display_name)
                        user.avatar_url = tiktok_user.get('avatar_url', user.avatar_url)
                        user.follower_count = tiktok_user.get('follower_count', user.follower_count)
                        user.following_count = tiktok_user.get('following_count', user.following_count)
                        user.likes_count = tiktok_user.get('likes_count', user.likes_count)
                        user.video_count = tiktok_user.get('video_count', user.video_count)
                        db.session.commit()
                
                return jsonify(api_data)
                
        except Exception as e:
            logger.warning(f"TikTok API failed, falling back to database: {e}")
    
    # Fallback to local database data
    if user_id:
        user = User.query.get(user_id)
        if user:
            # Return data in TikTok API format
            return jsonify({
                'data': {
                    'user': {
                        'open_id': user.tiktok_user_id,
                        'union_id': user.tiktok_user_id,
                        'username': user.username or 'N/A',
                        'display_name': user.display_name or 'User',
                        'avatar_url': user.avatar_url or '',
                        'follower_count': user.follower_count or 0,
                        'following_count': user.following_count or 0,
                        'likes_count': user.likes_count or 0,
                        'video_count': user.video_count or 0
                    }
                }
            })
    
    # Final fallback if no user data available
    return jsonify({'error': 'User information not available'}), 404


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
    access_token = session.get('tiktok_access_token')
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json; charset=UTF-8'
    }
    
    data = request.get_json()
    
    # Prepare post info
    post_info = {
        'title': data.get('title', ''),
        'privacy_level': data.get('privacy_level', 'SELF_ONLY'),  # Default to private for unaudited apps
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
    
    try:
        response = requests.post(
            f'{TIKTOK_BASE_URL}/post/publish/video/init/',
            headers=headers,
            json=request_body
        )
        return jsonify(response.json())
    except Exception as e:
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
    upload_url = data.get('upload_url')
    video_path = data.get('video_path')
    
    if not upload_url or not video_path:
        return jsonify({'error': 'Missing upload_url or video_path'}), 400
    
    try:
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
            
        headers = {
            'Content-Type': 'video/mp4',
            'Content-Range': f'bytes 0-{len(video_data)-1}/{len(video_data)}'
        }
        
        response = requests.put(upload_url, data=video_data, headers=headers)
        
        return jsonify({
            'success': response.status_code == 200,
            'status_code': response.status_code
        })
    except Exception as e:
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
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
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
            session['user_id'] = user.id
            
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
    user_id = session.get('user_id')
    
    # If user_id not in session, try to get it from the database
    if not user_id:
        access_token = session.get('tiktok_access_token')
        if access_token:
            # Try to find user by access token
            user = User.query.filter_by(access_token=access_token).first()
            if user:
                user_id = user.id
                session['user_id'] = user_id  # Store in session for future requests
            else:
                # If no user found, try to fetch from TikTok API and create/update user
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
                        user = User.query.filter_by(tiktok_user_id=tiktok_user['open_id']).first()
                        
                        if user:
                            user_id = user.id
                            session['user_id'] = user_id
                        else:
                            return jsonify({'error': 'User not registered. Please logout and login again.'}), 400
                except Exception as e:
                    logger.error(f"Failed to fetch user info: {e}")
    
    if not user_id:
        return jsonify({'error': 'User not found. Please logout and login again.'}), 400
    
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['title', 'scheduled_time']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    try:
        # Parse scheduled time
        scheduled_time = datetime.fromisoformat(data['scheduled_time'].replace('Z', '+00:00'))
        
        # Create scheduled post record
        scheduled_post = ScheduledPost(
            user_id=user_id,
            title=data['title'],
            description=data.get('description', ''),
            video_url=data.get('video_url'),
            video_path=data.get('video_path'),
            privacy_level=data.get('privacy_level', 'SELF_ONLY'),
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
    user_id = session.get('user_id')
    
    # If user_id not in session, try to get it from the database
    if not user_id:
        access_token = session.get('tiktok_access_token')
        if access_token:
            user = User.query.filter_by(access_token=access_token).first()
            if user:
                user_id = user.id
                session['user_id'] = user_id  # Store in session for future requests
    
    if not user_id:
        return jsonify({'error': 'User not found in session'}), 400
    
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
    user_id = session.get('user_id')
    
    # If user_id not in session, try to get it from the database
    if not user_id:
        access_token = session.get('tiktok_access_token')
        if access_token:
            user = User.query.filter_by(access_token=access_token).first()
            if user:
                user_id = user.id
                session['user_id'] = user_id  # Store in session for future requests
    
    if not user_id:
        return jsonify({'error': 'User not found in session'}), 400
    
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


if __name__ == '__main__':
    # Database is already initialized in init_app() above
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
