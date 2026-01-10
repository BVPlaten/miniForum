#!/usr/bin/env python3
"""
miniForum - Flask Application Runner
Optimized for embedded systems and OpenWRT routers
"""

import os
from app import create_app, db
from app.models import User, Category, Thread, Post, Message

# Determine configuration from environment
config_name = os.environ.get('FLASK_CONFIG') or 'development'

# Create application instance
app = create_app(config_name)

@app.shell_context_processor
def make_shell_context():
    """Make models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Thread': Thread,
        'Post': Post,
        'Message': Message
    }

def setup_database():
    """Initialize database with sample data"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if we already have data
        if Category.query.first() is None:
            print("Setting up sample data...")
            
            # Create sample categories
            cat_general = Category(name='Allgemein', description='Allgemeine Diskussionen')
            cat_tech = Category(name='Technik', description='Technische Themen')
            
            db.session.add(cat_general)
            db.session.add(cat_tech)
            db.session.commit()
            
            print("Sample categories created!")
            print("Forum is ready to use.")
        else:
            print("Database already initialized.")

if __name__ == '__main__':
    # Initialize database if needed
    setup_database()
    
    # Run the application
    if config_name == 'development':
        # Development server with debug mode
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
    else:
        # Production server (should use Gunicorn instead)
        print("WARNING: Running production config with development server!")
        print("Use Gunicorn for production: gunicorn -c deploy/openwrt/gunicorn.conf.py run:app")
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False
        )