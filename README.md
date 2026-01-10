# MiniForum - Resource-Efficient Forum Web Application for Embedded Systems

A lightweight forum application specifically optimized for extremely resource-constrained hardware like OpenWRT routers. The application runs with less than 50MB RAM and supports 10-20 concurrent users.

## Introduction

MiniForum is a simple communication platform designed for deployment on OpenWRT routers that have the LAMP package available. It provides basic forum functionality with minimal resource consumption, making it ideal for embedded systems and community networks.

## Design Philosophy and Architecture

### KISS Principle (Keep It Simple, Stupid)
The application follows the KISS principle for maximum efficiency:
- Minimal code overhead
- No unnecessary dependencies
- Clear separation of concerns
- Easy maintainability

### Resource Optimization for OpenWRT
- **SQLite instead of MySQL**: No separate process (~250KB vs several MB)
- **Flask instead of Django**: 50KB vs 20MB overhead
- **Client-side sessions** instead of server-side storage
- **Aggressive caching** for database relief
- **Soft-delete** instead of hard-delete (performance & data integrity)

### Modular Architecture
- Flask Blueprints for clear separation of functionalities
- MVC pattern (Model-View-Controller)
- Reusable components
- Extensibility for future features

## File Structure and Responsibilities

### Root Directory
- `config.py` - Central configuration (Development/Production)
- `requirements.txt` - Python dependencies
- `run.py` - Application entry point
- `README.md` - This documentation file

### app/ (Main Application)
- `__init__.py` - Flask app factory & extension initialization
- `models/` - Database models (SQLAlchemy ORM)
- `views/` - Flask blueprints (controllers)
- `templates/` - Jinja2 templates (views)
- `static/` - CSS, minimal JS, icons, uploads
- `utils/` - Helper functions and decorators

### Model Files (app/models/)
- `__init__.py` - Model imports and exports
- `user.py` - User management and authentication
- `category.py` - Forum categories and hierarchy
- `thread.py` - Discussion topics (threads)
- `post.py` - Posts and replies
- `message.py` - Private messages

## Detailed File Explanations

### config.py
**Purpose**: Central configuration management for all environments

**Design Decisions**:
- Three environments: Development, Production, Testing
- Environment variables for sensitive data (SECRET_KEY, DATABASE_URL)
- SQLite optimization for OpenWRT: cache=shared&mode=rwc
- Different rate limits: Development (100/min) vs Production (30/min)
- Gunicorn settings specifically for embedded systems:
  - Only 2 workers (instead of 4-8 on normal servers)
  - 1 thread per worker (less memory)
  - sync worker (simple, reliable)
  - Worker restart after 1000 requests (memory cleanup)

**Performance Optimizations**:
- CACHE_TYPE = 'SimpleCache' (memory-based, no Redis needed)
- CACHE_DEFAULT_TIMEOUT = 600 seconds (10 minutes)
- SESSION_TYPE = 'filesystem' (no server storage)
- Minimal logging in Production (LOG_LEVEL = 'WARNING')

**Security**:
- CSRF protection enabled (WTF_CSRF_ENABLED = True)
- Secure cookies in Production (SESSION_COOKIE_SECURE = True)
- HttpOnly cookies (SESSION_COOKIE_HTTPONLY = True)

### app/__init__.py
**Purpose**: Flask application factory and extension initialization

**Design Decisions**:
- Factory pattern for flexible app creation
- Lazy loading of extensions
- Blueprint registration for modular structure
- Performance monitoring for slow queries (>100ms)

**Performance Features**:
- Slow query logging in Development
- Cache initialization for all models
- Rate limiter for all endpoints
- Session management with minimal overhead

**Security**:
- Error handlers for 404/500
- Database rollback on errors
- Login manager configuration

### app/models/user.py
**Purpose**: User management, authentication, profiles

**Design Decisions**:
- UserMixin from Flask-Login for session management
- Bcrypt for password hashing (secure, OpenWRT-compatible)
- Geo-coordinates (latitude, longitude) for future map integration
- Avatar field for profile pictures (optional)
- Soft-delete instead of hard-delete (performance & recovery)

**Performance Optimizations**:
- Aggressive caching of all count methods:
  - get_post_count() - 10 minute cache
  - get_thread_count() - 10 minute cache
  - get_unread_message_count() - 1 minute cache
- Database indexes on username, email, is_active

**Security**:
- Bcrypt with salt for passwords
- Unique constraints on username and email
- is_active flag for account deactivation

**Future-Proofing**:
- latitude/longitude as DECIMAL(10,8) / DECIMAL(11,8)
- avatar_path for profile picture upload
- bio field for user descriptions

### app/models/category.py
**Purpose**: Forum categories and hierarchy management

**Design Decisions**:
- Self-referential relationship for subcategories
- Maximum 2-3 levels (performance & usability)
- Lazy loading for threads (memory-efficient)
- Cascade delete for clean deletion

**Performance Optimizations**:
- Caching of thread and post counts (5 minutes)
- Indexes on parent_id and name
- get_last_post() for "latest posts" display

**Future-Proofing**:
- description field for category descriptions
- Extensible for more metadata

### app/models/thread.py
**Purpose**: Discussion topics (threads) with status management

**Design Decisions**:
- is_pinned, is_locked, is_deleted flags
- view_count for popularity tracking
- Soft-delete for all posts in thread
- Cascade delete for clean database

**Performance Optimizations**:
- Caching of post count (5 minutes)
- Indexes on all status fields
- get_last_post() for quick "last post" display
- increment_view_count() for thread-safety

**Security**:
- is_locked prevents further replies
- is_deleted flag instead of hard-delete

**Future-Proofing**:
- view_count can be used for "popular threads"
- updated_at for "active threads" sorting

### app/models/post.py
**Purpose**: Posts and replies in threads

**Design Decisions**:
- Threaded reply system (parent_id for hierarchy)
- **Image upload preparation**: has_image and image_path fields
- **Geo-coordinates**: latitude/longitude for map integration
- Soft-delete with cache cleanup
- Max 500KB image size (configurable)

**Performance Optimizations**:
- get_reply_depth() for nested display
- Indexes on thread_id, author_id, parent_id
- Soft-delete instead of hard-delete (performance)

**Security**:
- Content as text (no HTML, XSS prevention via Jinja2)
- Image upload type checking (ALLOWED_EXTENSIONS)

**Future-Proofing**:
- has_image flag for quick checking
- image_path for filesystem storage
- latitude/longitude for geo-tagging
- parent_id for threaded discussions

### app/models/message.py
**Purpose**: Private messages between users

**Design Decisions**:
- is_read flag for unread status
- Separate delete flags per user (is_deleted_by_sender/recipient)
- Static methods for Inbox/Sent queries
- Cache management on status changes

**Performance Optimizations**:
- get_inbox() and get_sent() with filters
- Indexes on sender_id, recipient_id, is_read
- mark_as_read() with cache cleanup

**Security**:
- Only sender/recipient can view messages
- Soft-delete for both parties independently

**Future-Proofing**:
- subject field for message subjects
- content for message text

## Installation and Setup

### Prerequisites
- Python 3.7 or higher
- SQLite3 (included in Python)
- ~50MB free memory
- OpenWRT router (optional, for optimal use)

### Quick Installation (Development)
```bash
# Clone repository
git clone <repository-url>
cd miniForum

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from app import db, create_app; db.create_all(app=create_app())"

# Start application
python run.py

# Open in browser
http://localhost:5000
```

### Production Installation (OpenWRT)
```bash
# Connect to OpenWRT router
ssh root@192.168.1.1

# Install Python and SQLite
opkg update
opkg install python3 python3-pip sqlite3

# Copy application
scp -r miniForum/ root@192.168.1.1:/opt/

# Install dependencies
cd /opt/miniForum
pip3 install -r requirements.txt

# Initialize database
python3 -c "from app import db, create_app; db.create_all(app=create_app('production'))"

# Set up as service (see deploy/openwrt/miniForum.init)

# Configure Apache (see deploy/openwrt/apache.conf)

# Start service
/etc/init.d/miniForum start
```

### Database Initialization
For Development:
```bash
python -c "from app import db, create_app; db.create_all(app=create_app())"
```

For Production:
```bash
python -c "from app import db, create_app; db.create_all(app=create_app('production'))"
```

Create first admin user:
```bash
python -c "
from app import create_app
from app.models import User
from app import db

app = create_app()
with app.app_context():
    user = User(username='admin', email='admin@example.com')
    user.set_password('admin123')
    user.is_admin = True
    db.session.add(user)
    db.session.commit()
    print('Admin user created!')
"
```

### Starting the Application
Development (with debug mode and hot-reload):
```bash
python run.py
```

Production (with Gunicorn):
```bash
gunicorn -c deploy/openwrt/gunicorn.conf.py run:app
```

Or with systemd service:
```bash
systemctl start miniForum
```

## Configuration

### Environment Variables
- `SECRET_KEY` - Secret key for sessions (Production!)
- `DATABASE_URL` - Database URL (optional)
- `FLASK_ENV` - 'development' or 'production'
- `FLASK_CONFIG` - 'development', 'production', 'testing'

### Important Configuration Parameters (config.py)
- `POSTS_PER_PAGE` - Posts per page (default: 15)
- `THREADS_PER_PAGE` - Threads per page (default: 20)
- `MESSAGES_PER_PAGE` - Messages per page (default: 20)
- `MAX_CONTENT_LENGTH` - Max upload size (default: 500KB)
- `CACHE_DEFAULT_TIMEOUT` - Cache duration in seconds (default: 300)

### OpenWRT-Specific Settings
- `GUNICORN_WORKERS` - Number of worker processes (default: 2)
- `GUNICORN_THREADS` - Threads per worker (default: 1)
- `GUNICORN_MAX_REQUESTS` - Worker restart after requests (default: 1000)

## Maintenance and Troubleshooting

### Database Backup
```bash
sqlite3 forum.db ".backup 'forum_backup.db'"
```

### Clear Cache
For display issues or after data changes:
```bash
python -c "from app import cache; cache.clear()"
```

### Check Logs
Development: Output to console
Production: `/var/log/miniForum.log`

### Common Issues

**Problem**: "Database is locked" error
**Solution**: Enable SQLite WAL mode or reduce Gunicorn workers

**Problem**: Slow response times
**Solution**: Check cache, verify indexes, check memory

**Problem**: High memory usage
**Solution**: Reduce Gunicorn workers, shorten cache timeout

**Problem**: Image upload not working
**Solution**: Check upload directory, verify write permissions, check file size

## Performance Monitoring

### Check Memory Usage
```bash
ps aux | grep python
```

### Measure Response Times
```bash
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/
```

### Database Performance
In Development: `SQLALCHEMY_ECHO = True`
Slow queries are automatically logged (>100ms)

### Cache Effectiveness
Check cache hits in logs
Compare response times

## Future Extensions

The application is already prepared for:

### Map Integration
- Geo-coordinates in User and Post models
- latitude/longitude fields (DECIMAL(10,8) / DECIMAL(11,8))
- API endpoints can be easily added

### Image Upload
- has_image and image_path fields in Post model
- Upload infrastructure already implemented
- 500KB limit configurable
- Thumbnail generation prepared (Pillow)

### Mobile App API
- Blueprint structure allows simple API extension
- REST-like endpoints can be added
- Authentication already implemented

### Advanced Search
- SQLite FTS5 (Full-Text Search) can be enabled
- Search indexes already defined
- Performance-tested for small to medium forums

## Security Notes

### Production Deployment
- Change SECRET_KEY!
- Use HTTPS (SESSION_COOKIE_SECURE = True)
- Create regular backups
- Check logs for suspicious activity
- Adjust rate limits as needed

### Passwords
- Bcrypt with salt (secure)
- Minimum length: 8 characters recommended
- Enforce regular password changes (optional)

### User Rights
- Admin flag only for trusted users
- is_active flag for account suspension
- Enable IP logging if needed

## Resources and Specifications

### Minimum System Requirements
- CPU: 400 MHz Single-Core
- RAM: 64MB (50MB for application)
- Storage: 100MB free space
- OS: Linux with Python 3.7+

### Recommended System Requirements
- CPU: 580 MHz Dual-Core (OpenWRT router)
- RAM: 128MB
- Storage: 256MB free space
- OS: OpenWRT 19.07+

### Performance Targets
- Memory usage: <50MB for Python processes
- Response times: <200ms for lists, <100ms for assets
- Concurrent users: 10-20 without degradation
- Database queries: <100ms (99% of queries)

## Support and Further Help

For questions or problems:
- Read README.md thoroughly
- Check configuration
- Analyze logs
- Clear cache for display issues

Documentation: This file (README.md)
Configuration: config.py
Examples: deploy/openwrt/

## License and Credits

This is an open-source application for resource-efficient forums.
Optimized for OpenWRT and embedded systems.

Developed with Flask, SQLAlchemy, SQLite for minimal resource usage.

---

**End of Documentation**--------------------------------
