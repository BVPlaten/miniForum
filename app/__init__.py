from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_session import Session
import os

db = SQLAlchemy()
login_manager = LoginManager()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)
sess = Session()

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(f'config.{config_name.capitalize()}Config')
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    sess.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bitte melden Sie sich an, um diese Seite zu sehen.'
    login_manager.login_message_category = 'info'
    
    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.views.auth import auth_bp
    from app.views.forum import forum_bp
    from app.views.messages import messages_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(forum_bp, url_prefix='/forum')
    app.register_blueprint(messages_bp, url_prefix='/messages')
    
    # Register main routes
    @app.route('/')
    def index():
        from app.views.forum import forum_bp
        return forum_bp.index()
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return 'Seite nicht gefunden', 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return 'Interner Serverfehler', 500
    
    # Performance monitoring
    @app.after_request
    def after_request(response):
        # Log slow queries in development
        if app.config.get('SQLALCHEMY_ECHO'):
            from sqlalchemy import event
            from sqlalchemy.engine import Engine
            import time
            
            @event.listens_for(Engine, "before_cursor_execute")
            def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                conn.info.setdefault('query_start_time', []).append(time.time())
            
            @event.listens_for(Engine, "after_cursor_execute")
            def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
                total = time.time() - conn.info['query_start_time'].pop()
                if total > 0.1:  # Log queries slower than 100ms
                    app.logger.warning(f'Slow query ({total:.3f}s): {statement}')
        
        return response
    
    return app