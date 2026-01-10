from datetime import datetime
from app import db

class Post(db.Model):
    __tablename__ = 'posts'
    
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    thread_id = db.Column(db.Integer, db.ForeignKey('threads.id'), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Post hierarchy (for threaded replies)
    parent_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=True, index=True)
    
    # Image upload preparation
    has_image = db.Column(db.Boolean, default=False, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    
    # Geo-coordinates for future map integration
    latitude = db.Column(db.DECIMAL(10, 8), nullable=True)
    longitude = db.Column(db.DECIMAL(11, 8), nullable=True)
    
    # Post status
    is_deleted = db.Column(db.Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    parent = db.relationship('Post', remote_side=[id], backref='replies')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_post_thread', 'thread_id'),
        db.Index('idx_post_author', 'author_id'),
        db.Index('idx_post_parent', 'parent_id'),
        db.Index('idx_post_deleted', 'is_deleted'),
        db.Index('idx_post_created', 'created_at'),
    )
    
    def soft_delete(self):
        """Soft delete post"""
        self.is_deleted = True
        db.session.commit()
        
        # Clear relevant caches
        from app import cache
        cache.delete(f'thread_post_count_{self.thread_id}')
        cache.delete(f'user_post_count_{self.author_id}')
        cache.delete(f'category_post_count_{self.thread.category_id}')
    
    def get_reply_depth(self):
        """Get the depth of this post in the reply tree"""
        depth = 0
        current = self.parent
        while current:
            depth += 1
            current = current.parent
        return depth
    
    def __repr__(self):
        return f'<Post {self.id} in Thread {self.thread_id}>'