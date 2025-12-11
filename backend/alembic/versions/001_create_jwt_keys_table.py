"""
Alembic migration: Create jwt_keys table for key rotation.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers
revision = 'create_jwt_keys_table'
down_revision = None  # Update this with your latest migration
branch_labels = None
depends_on = None


def upgrade():
    """Create jwt_keys table"""
    op.create_table(
        'jwt_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_id', sa.String(length=50), nullable=False, comment='Unique identifier'),
        sa.Column('secret_key', sa.Text(), nullable=False, comment='Base64-encoded JWT secret'),
        sa.Column(
            'status',
            sa.Enum('current', 'previous_1', 'previous_2', 'expired', name='keystatus'),
            nullable=False,
            comment='Key lifecycle status'
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='created_at + 72 hours'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_id'),
        comment='JWT signing keys with rotation support'
    )
    
    # Create indexes
    op.create_index('idx_jwt_keys_status', 'jwt_keys', ['status'])
    op.create_index('idx_jwt_keys_expires_at', 'jwt_keys', ['expires_at'])


def downgrade():
    """Drop jwt_keys table"""
    op.drop_index('idx_jwt_keys_expires_at', table_name='jwt_keys')
    op.drop_index('idx_jwt_keys_status', table_name='jwt_keys')
    op.drop_table('jwt_keys')
    
    # Drop the enum type (MySQL)
    op.execute('DROP TYPE IF EXISTS keystatus')
