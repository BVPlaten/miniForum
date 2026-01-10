from datetime import datetime
from app import db

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True, index=True)
    
    # Category hierarchy (2-3 levels max)
    parent = db.relationship('Category', remote_side=[id], backref='subcategories')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    threads = db.relationship('Thread', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_category_parent', 'parent_id'),
        db.Index('idx_category_name', 'name'),
    )
    
    def get_thread_count(self):
        """Get total thread count (cached for performance)"""
        from app import cache
        cache_key = f'category_thread_count_{self.id}'
        count = cache.get(cache_key)
        if count is None:
            count = self.threads.filter_by(is_deleted=False).count()
            cache.set(cache_key, count, timeout=300)  # Cache for 5 minutes
        return count
    
    def get_post_count(self):
        """Get total post count in this category"""
        from app.models import Post, Thread
        from app import cache
        
        cache_key = f'category_post_count_{self.id}'
        count = cache.get(cache_key)
        if count is None:
            count = Post.query.join(Thread).filter(
                Thread.category_id == self.id,
                Post.is_deleted == False,
                Thread.is_deleted == False
            ).count()
            cache.set(cache_key, count, timeout=300)
        return count
    
    def get_last_post(self):
        """Get the most recent post in this category"""
        from app.models import Post, Thread
        return Post.query.join(Thread).filter(
            Thread.category_id == self.id,
            Post.is_deleted == False,
            Thread.is_deleted == False
        ).order_by(Post.created_at.desc()).first()
    
    def __repr__(self):
        return f'<Category {self.name}>'