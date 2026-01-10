from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from app import db, cache
from app.models import Category, Thread, Post, User
from app.forms import ThreadForm, PostForm, SearchForm
from sqlalchemy import or_, and_

forum_bp = Blueprint('forum', __name__)

@forum_bp.route('/')
def index():
    """Forum index page - show all categories"""
    categories = Category.query.filter_by(parent_id=None).all()
    return render_template('forum/index.html', categories=categories, title='Forum')

@forum_bp.route('/category/<int:category_id>')
def category(category_id):
    """Show threads in a category"""
    category = Category.query.get_or_404(category_id)
    page = request.args.get('page', 1, type=int)
    
    # Get threads with pagination
    threads_query = Thread.query.filter_by(
        category_id=category_id, 
        is_deleted=False
    ).order_by(
        Thread.is_pinned.desc(),
        Thread.updated_at.desc()
    )
    
    threads = threads_query.paginate(
        page=page, 
        per_page=current_app.config['THREADS_PER_PAGE'],
        error_out=False
    )
    
    return render_template('forum/category.html', 
                         category=category, 
                         threads=threads,
                         title=category.name)

@forum_bp.route('/category/<int:category_id>/new_thread', methods=['GET', 'POST'])
@login_required
def new_thread(category_id):
    """Create a new thread in a category"""
    category = Category.query.get_or_404(category_id)
    
    if category.is_locked:
        flash('Diese Kategorie ist gesperrt.', 'error')
        return redirect(url_for('forum.category', category_id=category_id))
    
    form = ThreadForm()
    if form.validate_on_submit():
        # Create new thread
        thread = Thread(
            title=form.title.data,
            category_id=category_id,
            author_id=current_user.id
        )
        db.session.add(thread)
        db.session.flush()  # Get thread ID
        
        # Create first post
        post = Post(
            content=form.content.data,
            thread_id=thread.id,
            author_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        
        # Clear category cache
        cache.delete(f'category_thread_count_{category_id}')
        
        flash('Thread erfolgreich erstellt!', 'success')
        return redirect(url_for('forum.thread', thread_id=thread.id))
    
    return render_template('forum/new_thread.html', 
                         category=category, 
                         form=form,
                         title='Neuer Thread')

@forum_bp.route('/thread/<int:thread_id>')
def thread(thread_id):
    """Show a thread with all posts"""
    thread = Thread.query.get_or_404(thread_id)
    
    if thread.is_deleted:
        flash('Dieser Thread wurde gelöscht.', 'error')
        return redirect(url_for('forum.category', category_id=thread.category_id))
    
    # Increment view count
    thread.increment_view_count()
    
    page = request.args.get('page', 1, type=int)
    
    # Get posts with pagination
    posts_query = Post.query.filter_by(
        thread_id=thread_id,
        is_deleted=False,
        parent_id=None  # Only top-level posts
    ).order_by(Post.created_at.asc())
    
    posts = posts_query.paginate(
        page=page,
        per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False
    )
    
    # Get replies for each post (for threaded view)
    post_replies = {}
    for post in posts.items:
        replies = Post.query.filter_by(
            parent_id=post.id,
            is_deleted=False
        ).order_by(Post.created_at.asc()).all()
        post_replies[post.id] = replies
    
    form = PostForm()
    
    return render_template('forum/thread.html',
                         thread=thread,
                         posts=posts,
                         post_replies=post_replies,
                         form=form,
                         title=thread.title)

@forum_bp.route('/thread/<int:thread_id>/reply', methods=['POST'])
@login_required
def reply(thread_id):
    """Reply to a thread"""
    thread = Thread.query.get_or_404(thread_id)
    
    if thread.is_locked:
        flash('Dieser Thread ist gesperrt.', 'error')
        return redirect(url_for('forum.thread', thread_id=thread_id))
    
    if thread.is_deleted:
        flash('Dieser Thread wurde gelöscht.', 'error')
        return redirect(url_for('forum.index'))
    
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            content=form.content.data,
            thread_id=thread_id,
            author_id=current_user.id
        )
        db.session.add(post)
        db.session.commit()
        
        # Clear caches
        cache.delete(f'thread_post_count_{thread_id}')
        cache.delete(f'user_post_count_{current_user.id}')
        cache.delete(f'category_post_count_{thread.category_id}')
        
        flash('Antwort erfolgreich gepostet!', 'success')
        return redirect(url_for('forum.thread', thread_id=thread_id))
    
    return redirect(url_for('forum.thread', thread_id=thread_id))

@forum_bp.route('/post/<int:post_id>/reply', methods=['POST'])
@login_required
def reply_to_post(post_id):
    """Reply to a specific post (threaded reply)"""
    parent_post = Post.query.get_or_404(post_id)
    thread = Thread.query.get_or_404(parent_post.thread_id)
    
    if thread.is_locked:
        flash('Dieser Thread ist gesperrt.', 'error')
        return redirect(url_for('forum.thread', thread_id=thread.id))
    
    if thread.is_deleted or parent_post.is_deleted:
        flash('Dieser Beitrag wurde gelöscht.', 'error')
        return redirect(url_for('forum.thread', thread_id=thread.id))
    
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            content=form.content.data,
            thread_id=thread.id,
            author_id=current_user.id,
            parent_id=post_id
        )
        db.session.add(post)
        db.session.commit()
        
        flash('Antwort erfolgreich gepostet!', 'success')
    
    return redirect(url_for('forum.thread', thread_id=thread.id))

@forum_bp.route('/search', methods=['GET', 'POST'])
def search():
    """Search forum content"""
    form = SearchForm()
    results = None
    
    if form.validate_on_submit():
        query = form.query.data
        page = request.args.get('page', 1, type=int)
        
        # Search in thread titles and post content
        threads = Thread.query.join(Post).filter(
            Thread.is_deleted == False,
            Post.is_deleted == False,
            or_(
                Thread.title.contains(query),
                Post.content.contains(query)
            )
        ).distinct().paginate(
            page=page,
            per_page=current_app.config['THREADS_PER_PAGE'],
            error_out=False
        )
        
        results = threads
    
    return render_template('forum/search.html',
                         form=form,
                         results=results,
                         title='Suche')

@forum_bp.route('/user/<username>')
def user_profile(username):
    """Show user profile"""
    user = User.query.filter_by(username=username).first_or_404()
    
    if not user.is_active:
        flash('Dieser Benutzer ist deaktiviert.', 'error')
        return redirect(url_for('forum.index'))
    
    # Get user's recent activity
    recent_posts = Post.query.filter_by(
        author_id=user.id,
        is_deleted=False
    ).order_by(Post.created_at.desc()).limit(10).all()
    
    recent_threads = Thread.query.filter_by(
        author_id=user.id,
        is_deleted=False
    ).order_by(Thread.created_at.desc()).limit(5).all()
    
    return render_template('forum/user_profile.html',
                         user=user,
                         recent_posts=recent_posts,
                         recent_threads=recent_threads,
                         title=f'Profil: {user.username}')