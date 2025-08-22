from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    tiktok_accounts = db.relationship('TikTokAccount', backref='owner', lazy=True, cascade='all, delete-orphan')
    scheduled_posts = db.relationship('ScheduledPost', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'


class TikTokAccount(db.Model):
    __tablename__ = 'tiktok_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tiktok_user_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(200))
    avatar_url = db.Column(db.String(500))
    bio = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    follower_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    video_count = db.Column(db.Integer, default=0)
    # Token fields as per TikTok API documentation
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    refresh_token_expires_at = db.Column(db.DateTime)
    scope = db.Column(db.String(500))  # Comma-separated list of scopes
    token_type = db.Column(db.String(50), default='Bearer')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    last_profile_update = db.Column(db.DateTime)
    
    # Relationships
    scheduled_posts = db.relationship('ScheduledPost', backref='tiktok_account', lazy=True, cascade='all, delete-orphan')
    videos = db.relationship('UserVideo', backref='account', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TikTokAccount {self.username}>'


class UserVideo(db.Model):
    __tablename__ = 'user_videos'
    
    id = db.Column(db.Integer, primary_key=True)
    tiktok_account_id = db.Column(db.Integer, db.ForeignKey('tiktok_accounts.id'), nullable=False)
    video_id = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    create_time = db.Column(db.DateTime)
    duration = db.Column(db.Integer)  # in seconds
    height = db.Column(db.Integer)
    width = db.Column(db.Integer)
    cover_image_url = db.Column(db.String(500))
    share_url = db.Column(db.String(500))
    embed_link = db.Column(db.String(500))
    embed_html = db.Column(db.Text)
    view_count = db.Column(db.BigInteger, default=0)
    like_count = db.Column(db.BigInteger, default=0)
    comment_count = db.Column(db.BigInteger, default=0)
    share_count = db.Column(db.BigInteger, default=0)
    is_selected = db.Column(db.Boolean, default=False)  # User selected for display
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserVideo {self.video_id}>'


class ScheduledPost(db.Model):
    __tablename__ = 'scheduled_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tiktok_account_id = db.Column(db.Integer, db.ForeignKey('tiktok_accounts.id'), nullable=False)
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    video_url = db.Column(db.String(500))
    video_path = db.Column(db.String(500))
    privacy_level = db.Column(db.String(50), default='PUBLIC_TO_EVERYONE')
    disable_duet = db.Column(db.Boolean, default=False)
    disable_comment = db.Column(db.Boolean, default=False)
    disable_stitch = db.Column(db.Boolean, default=False)
    video_cover_timestamp_ms = db.Column(db.Integer, default=1000)
    scheduled_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='pending')
    error_message = db.Column(db.Text)
    posted_at = db.Column(db.DateTime)
    post_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ScheduledPost {self.id} - {self.status}>'