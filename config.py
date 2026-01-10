import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///forum.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True in development for query logging
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'app/static/uploads')
    MAX_CONTENT_LENGTH = 500 * 1024  # 500KB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Session configuration (client-side sessions)
    SESSION_TYPE = 'filesystem'
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    
    # Performance
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = "memory://"
    RATELIMIT_STRATEGY = "moving-window"
    
    # Pagination
    POSTS_PER_PAGE = 15
    THREADS_PER_PAGE = 20
    MESSAGES_PER_PAGE = 20
    
    # Application settings
    FORUM_NAME = 'miniForum'
    FORUM_DESCRIPTION = 'Eine ressourcenschonende Forum-Anwendung'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True  # Log all database queries
    CACHE_TYPE = 'NullCache'  # Disable caching in development
    SESSION_COOKIE_SECURE = False
    
    # Development rate limits (more generous)
    RATELIMIT_DEFAULT = "100 per minute"
    RATELIMIT_STORAGE_URL = "memory://"

class ProductionConfig(Config):
    """Production configuration for OpenWRT"""
    DEBUG = False
    TESTING = False
    
    # Use environment variable for secret key in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # SQLite optimization for embedded systems
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///forum.db?cache=shared&mode=rwc'
    
    # Stricter rate limiting for production
    RATELIMIT_DEFAULT = "30 per minute"
    RATELIMIT_LOGIN = "5 per minute"
    RATELIMIT_REGISTER = "3 per hour"
    
    # Session security
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    SESSION_COOKIE_HTTPONLY = True
    
    # Production caching
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 600  # 10 minutes
    
    # Logging
    LOG_LEVEL = 'WARNING'  # Minimal logging for resource conservation
    
    # Gunicorn settings (will be used in deployment)
    GUNICORN_WORKERS = 2  # Minimal workers for embedded systems
    GUNICORN_THREADS = 1  # Single thread per worker
    GUNICORN_WORKER_CLASS = 'sync'  # Simple sync worker for low memory
    GUNICORN_WORKER_TIMEOUT = 30
    GUNICORN_MAX_REQUESTS = 1000  # Restart workers after 1000 requests
    GUNICORN_MAX_REQUESTS_JITTER = 50

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    CACHE_TYPE = 'NullCache'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}