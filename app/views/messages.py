from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Message, User
from app.forms import MessageForm
from sqlalchemy import or_, and_

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

@messages_bp.route('/inbox')
@login_required
def inbox():
    """Show user's inbox"""
    page = request.args.get('page', 1, type=int)
    
    messages = Message.get_inbox(current_user.id).paginate(
        page=page,
        per_page=current_app.config['MESSAGES_PER_PAGE'],
        error_out=False
    )
    
    return render_template('messages/inbox.html',
                         messages=messages,
                         title='Posteingang')

@messages_bp.route('/sent')
@login_required
def sent():
    """Show user's sent messages"""
    page = request.args.get('page', 1, type=int)
    
    messages = Message.get_sent(current_user.id).paginate(
        page=page,
        per_page=current_app.config['MESSAGES_PER_PAGE'],
        error_out=False
    )
    
    return render_template('messages/sent.html',
                         messages=messages,
                         title='Gesendete Nachrichten')

@messages_bp.route('/compose', methods=['GET', 'POST'])
@login_required
def compose():
    """Compose a new message"""
    form = MessageForm(current_user.id)
    
    if form.validate_on_submit():
        message = Message(
            subject=form.subject.data,
            content=form.content.data,
            sender_id=current_user.id,
            recipient_id=form.recipient.data
        )
        db.session.add(message)
        db.session.commit()
        
        # Clear unread message cache for recipient
        from app import cache
        cache.delete(f'user_unread_messages_{form.recipient.data}')
        
        flash('Nachricht erfolgreich gesendet!', 'success')
        return redirect(url_for('messages.inbox'))
    
    return render_template('messages/compose.html',
                         form=form,
                         title='Nachricht verfassen')

@messages_bp.route('/message/<int:message_id>')
@login_required
def view_message(message_id):
    """View a specific message"""
    message = Message.query.get_or_404(message_id)
    
    # Check if user is sender or recipient
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        flash('Sie haben keine Berechtigung, diese Nachricht zu sehen.', 'error')
        return redirect(url_for('messages.inbox'))
    
    # Check if message is deleted for this user
    if (message.sender_id == current_user.id and message.is_deleted_by_sender) or \
       (message.recipient_id == current_user.id and message.is_deleted_by_recipient):
        flash('Diese Nachricht wurde gelöscht.', 'error')
        return redirect(url_for('messages.inbox'))
    
    # Mark as read if recipient is viewing
    if message.recipient_id == current_user.id and not message.is_read:
        message.mark_as_read()
    
    return render_template('messages/view_message.html',
                         message=message,
                         title=message.subject)

@messages_bp.route('/message/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    """Delete a message"""
    message = Message.query.get_or_404(message_id)
    
    # Check if user is sender or recipient
    if message.sender_id != current_user.id and message.recipient_id != current_user.id:
        flash('Sie haben keine Berechtigung, diese Nachricht zu löschen.', 'error')
        return redirect(url_for('messages.inbox'))
    
    # Soft delete for the user
    message.soft_delete(current_user.id)
    flash('Nachricht erfolgreich gelöscht.', 'success')
    
    return redirect(url_for('messages.inbox'))

@messages_bp.route('/message/<int:message_id>/reply', methods=['GET', 'POST'])
@login_required
def reply(message_id):
    """Reply to a message"""
    original_message = Message.query.get_or_404(message_id)
    
    # Check if user is recipient
    if original_message.recipient_id != current_user.id:
        flash('Sie können nur auf empfangene Nachrichten antworten.', 'error')
        return redirect(url_for('messages.inbox'))
    
    # Pre-fill form
    form = MessageForm(current_user.id)
    form.recipient.data = original_message.sender_id
    form.subject.data = f"Re: {original_message.subject}"
    
    if form.validate_on_submit():
        message = Message(
            subject=form.subject.data,
            content=form.content.data,
            sender_id=current_user.id,
            recipient_id=form.recipient.data
        )
        db.session.add(message)
        db.session.commit()
        
        # Clear unread message cache for recipient
        from app import cache
        cache.delete(f'user_unread_messages_{form.recipient.data}')
        
        flash('Antwort erfolgreich gesendet!', 'success')
        return redirect(url_for('messages.inbox'))
    
    return render_template('messages/compose.html',
                         form=form,
                         title='Antwort verfassen',
                         reply_to=original_message)

@messages_bp.route('/unread_count')
@login_required
def unread_count():
    """Get unread message count (AJAX endpoint)"""
    count = current_user.get_unread_message_count()
    return {'unread_count': count}