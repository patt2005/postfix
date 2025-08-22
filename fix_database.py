#!/usr/bin/env python3
"""
Fix missing columns in production database
"""

import os
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+psycopg2://', 1)

# Parse database URL
result = urlparse(DATABASE_URL)
username = result.username
password = result.password
database = result.path[1:]
hostname = result.hostname
port = result.port

# Connect to database
conn = psycopg2.connect(
    database=database,
    user=username,
    password=password,
    host=hostname,
    port=port
)

cur = conn.cursor()

print("Connected to database")

# Check and add missing columns to tiktok_accounts
columns_to_add = [
    ("bio", "TEXT"),
    ("is_verified", "BOOLEAN DEFAULT FALSE"),
    ("last_profile_update", "TIMESTAMP")
]

for column_name, column_type in columns_to_add:
    try:
        # Check if column exists
        cur.execute(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='tiktok_accounts' AND column_name='{column_name}'
        """)
        
        if not cur.fetchone():
            # Add column if it doesn't exist
            cur.execute(f"ALTER TABLE tiktok_accounts ADD COLUMN {column_name} {column_type}")
            print(f"Added column {column_name} to tiktok_accounts")
        else:
            print(f"Column {column_name} already exists in tiktok_accounts")
    except Exception as e:
        print(f"Error adding column {column_name}: {e}")
        conn.rollback()
        continue

# Check if user_videos table exists
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_name='user_videos'
""")

if not cur.fetchone():
    # Create user_videos table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_videos (
            id SERIAL PRIMARY KEY,
            tiktok_account_id INTEGER NOT NULL REFERENCES tiktok_accounts(id),
            video_id VARCHAR(100) UNIQUE NOT NULL,
            title VARCHAR(500),
            description TEXT,
            create_time TIMESTAMP,
            duration INTEGER,
            height INTEGER,
            width INTEGER,
            cover_image_url VARCHAR(500),
            share_url VARCHAR(500),
            embed_link VARCHAR(500),
            embed_html TEXT,
            view_count BIGINT DEFAULT 0,
            like_count BIGINT DEFAULT 0,
            comment_count BIGINT DEFAULT 0,
            share_count BIGINT DEFAULT 0,
            is_selected BOOLEAN DEFAULT FALSE,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created user_videos table")
else:
    print("user_videos table already exists")

# Commit changes
conn.commit()
print("Database fixed successfully!")

# Close connection
cur.close()
conn.close()