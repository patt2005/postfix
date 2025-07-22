from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    tiktok_user_id = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(200))
    avatar_url = db.Column(db.String(500))
    follower_count = db.Column(db.Integer, default=0)
    following_count = db.Column(db.Integer, default=0)
    likes_count = db.Column(db.Integer, default=0)
    video_count = db.Column(db.Integer, default=0)
    access_token = db.Column(db.Text)
    refresh_token = db.Column(db.Text)
    token_expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    scheduled_posts = db.relationship('ScheduledPost', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<User {self.username}>'


class ScheduledPost(db.Model):
    __tablename__ = 'scheduled_posts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    video_url = db.Column(db.String(500))
    video_path = db.Column(db.String(500))
    privacy_level = db.Column(db.String(50), default='SELF_ONLY')
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