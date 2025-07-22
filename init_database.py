#!/usr/bin/env python
"""Initialize database and run migrations"""

import os
from flask_migrate import init, migrate, upgrade
from app import app

def init_database():
    with app.app_context():
        # Initialize Flask-Migrate
        if not os.path.exists('migrations'):
            init()
            print("Initialized Flask-Migrate")
        
        # Create a new migration
        migrate(message='Initial migration with User and ScheduledPost models')
        print("Created migration")
        
        # Apply the migration
        upgrade()
        print("Applied migration - database is ready!")

if __name__ == '__main__':
    init_database()