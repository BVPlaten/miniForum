from datetime import datetime
from app import db

class Thread(db.Model):
    __tablename__ = 'threads'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Thread status
    is_pinned = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # View counter
    view_count = db.Column(db.Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    posts = db.relationship('Post', backref='thread', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_thread_category', 'category_id'),
        db.Index('idx_thread_author', 'author_id'),
        db.Index('idx_thread_pinned', 'is_pinned'),
        db.Index('idx_thread_deleted', 'is_deleted'),
        db.Index('idx_thread_created', 'created_at'),
    )
    
    def get_post_count(self):
        """Get total post count (cached)"""
        from app import cache
        cache_key = f'thread_post_count_{self.id}'
        count = cache.get(cache_key)
        if count is None:
            count = self.posts.filter_by(is_deleted=False).count()
            cache.set(cache_key, count, timeout=300)  # Cache for 5 minutes
        return count
    
    def get_last_post(self):
        """Get the most recent post in this thread"""
        return self.posts.filter_by(is_deleted=False).order_by(Post.created_at.desc()).first()
    
    def increment_view_count(self):
        """Increment view count (thread-safe)"""
        self.view_count += 1
        db.session.commit()
    
    def soft_delete(self):
        """Soft delete thread and all its posts"""
        self.is_deleted = True
        for post in self.posts:
            post.is_deleted = True
        db.session.commit()
        
        # Clear relevant caches
        from app import cache
        cache.delete(f'category_thread_count_{self.category_id}')
        cache.delete(f'category_post_count_{self.category_id}')
        cache.delete(f'user_thread_count_{self.author_id}')
    
    def __repr__(self):
        return f'<Thread {self.title}>'