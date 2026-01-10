from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import bcrypt

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # User profile fields
    avatar_path = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    
    # Geo-coordinates for future map integration
    latitude = db.Column(db.DECIMAL(10, 8), nullable=True)
    longitude = db.Column(db.DECIMAL(11, 8), nullable=True)
    
    # Account status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    threads = db.relationship('Thread', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    posts = db.relationship('Post', backref='author', lazy='dynamic', cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy='dynamic', cascade='all, delete-orphan')
    received_messages = db.relationship('Message', foreign_keys='Message.recipient_id', backref='recipient', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_user_username', 'username'),
        db.Index('idx_user_email', 'email'),
        db.Index('idx_user_active', 'is_active'),
    )
    
    def set_password(self, password):
        """Hash password using bcrypt"""
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def get_post_count(self):
        """Get total post count (cached)"""
        from app import cache
        cache_key = f'user_post_count_{self.id}'
        count = cache.get(cache_key)
        if count is None:
            from app.models import Post
            count = Post.query.filter_by(author_id=self.id, is_deleted=False).count()
            cache.set(cache_key, count, timeout=600)  # Cache for 10 minutes
        return count
    
    def get_thread_count(self):
        """Get total thread count (cached)"""
        from app import cache
        cache_key = f'user_thread_count_{self.id}'
        count = cache.get(cache_key)
        if count is None:
            from app.models import Thread
            count = Thread.query.filter_by(author_id=self.id, is_deleted=False).count()
            cache.set(cache_key, count, timeout=600)
        return count
    
    def get_unread_message_count(self):
        """Get unread message count (cached)"""
        from app import cache
        cache_key = f'user_unread_messages_{self.id}'
        count = cache.get(cache_key)
        if count is None:
            from app.models import Message
            count = Message.query.filter_by(recipient_id=self.id, is_read=False).count()
            cache.set(cache_key, count, timeout=60)  # Cache for 1 minute
        return count
    
    def update_last_seen(self):
        """Update last seen timestamp"""
        self.last_seen = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))