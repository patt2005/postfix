"""Fix missing columns in tiktok_accounts table

Revision ID: fix_missing_columns
Revises: 0050b508c73f
Create Date: 2025-08-22 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from sqlalchemy.engine import reflection

# revision identifiers, used by Alembic.
revision = 'fix_missing_columns'
down_revision = '0050b508c73f'
branch_labels = None
depends_on = None


def upgrade():
    # Get database connection
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Check if user_videos table exists
    tables = inspector.get_table_names()
    if 'user_videos' not in tables:
        op.create_table('user_videos',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('tiktok_account_id', sa.Integer(), nullable=False),
            sa.Column('video_id', sa.String(length=100), nullable=False),
            sa.Column('title', sa.String(length=500), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('create_time', sa.DateTime(), nullable=True),
            sa.Column('duration', sa.Integer(), nullable=True),
            sa.Column('height', sa.Integer(), nullable=True),
            sa.Column('width', sa.Integer(), nullable=True),
            sa.Column('cover_image_url', sa.String(length=500), nullable=True),
            sa.Column('share_url', sa.String(length=500), nullable=True),
            sa.Column('embed_link', sa.String(length=500), nullable=True),
            sa.Column('embed_html', sa.Text(), nullable=True),
            sa.Column('view_count', sa.BigInteger(), nullable=True),
            sa.Column('like_count', sa.BigInteger(), nullable=True),
            sa.Column('comment_count', sa.BigInteger(), nullable=True),
            sa.Column('share_count', sa.BigInteger(), nullable=True),
            sa.Column('is_selected', sa.Boolean(), nullable=True),
            sa.Column('last_updated', sa.DateTime(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['tiktok_account_id'], ['tiktok_accounts.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('video_id')
        )
    
    # Check existing columns in tiktok_accounts
    columns = [col['name'] for col in inspector.get_columns('tiktok_accounts')]
    
    with op.batch_alter_table('tiktok_accounts', schema=None) as batch_op:
        if 'bio' not in columns:
            batch_op.add_column(sa.Column('bio', sa.Text(), nullable=True))
        if 'is_verified' not in columns:
            batch_op.add_column(sa.Column('is_verified', sa.Boolean(), nullable=True))
        if 'last_profile_update' not in columns:
            batch_op.add_column(sa.Column('last_profile_update', sa.DateTime(), nullable=True))


def downgrade():
    # Downgrade is optional
    pass