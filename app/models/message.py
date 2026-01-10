from datetime import datetime
from app import db

class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Message status
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    is_deleted_by_sender = db.Column(db.Boolean, default=False, nullable=False)
    is_deleted_by_recipient = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        db.Index('idx_message_sender', 'sender_id'),
        db.Index('idx_message_recipient', 'recipient_id'),
        db.Index('idx_message_read', 'is_read'),
        db.Index('idx_message_created', 'created_at'),
    )
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            db.session.commit()
            
            # Clear unread message cache
            from app import cache
            cache.delete(f'user_unread_messages_{self.recipient_id}')
    
    def soft_delete(self, user_id):
        """Soft delete message for specific user"""
        if user_id == self.sender_id:
            self.is_deleted_by_sender = True
        elif user_id == self.recipient_id:
            self.is_deleted_by_recipient = True
        
        db.session.commit()
        
        # Clear unread message cache if recipient deleted
        if user_id == self.recipient_id and not self.is_read:
            from app import cache
            cache.delete(f'user_unread_messages_{self.recipient_id}')
    
    @staticmethod
    def get_inbox(user_id):
        """Get inbox messages for user"""
        return Message.query.filter(
            Message.recipient_id == user_id,
            Message.is_deleted_by_recipient == False
        ).order_by(Message.created_at.desc())
    
    @staticmethod
    def get_sent(user_id):
        """Get sent messages for user"""
        return Message.query.filter(
            Message.sender_id == user_id,
            Message.is_deleted_by_sender == False
        ).order_by(Message.created_at.desc())
    
    def __repr__(self):
        return f'<Message {self.subject} from {self.sender_id} to {self.recipient_id}>'