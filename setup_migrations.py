#!/usr/bin/env python
"""Setup Flask-Migrate for the first time"""

import os
import subprocess

def setup_migrations():
    # Check if migrations folder already exists
    if os.path.exists('migrations'):
        print("Migrations folder already exists. Skipping initialization.")
        return
    
    print("Initializing Flask-Migrate...")
    
    # Initialize migrations
    subprocess.run(['flask', 'db', 'init'], check=True)
    print("✓ Initialized Flask-Migrate")
    
    # Create initial migration
    subprocess.run(['flask', 'db', 'migrate', '-m', 'Initial migration with User and ScheduledPost models'], check=True)
    print("✓ Created initial migration")
    
    # Apply migration
    subprocess.run(['flask', 'db', 'upgrade'], check=True)
    print("✓ Applied migration - database is ready!")

if __name__ == '__main__':
    setup_migrations()