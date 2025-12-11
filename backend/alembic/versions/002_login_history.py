"""add login history and session tracking

Revision ID: 002_login_history
Revises: 001_create_jwt_keys_table
Create Date: 2025-12-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_login_history'
down_revision = '001_create_jwt_keys_table'
branch_labels = None
depends_on = None


def upgrade():
    # Create login_history table
    op.create_table(
        'login_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('login_time', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('logout_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('os', sa.String(length=100), nullable=True),
        sa.Column('browser', sa.String(length=100), nullable=True),
        sa.Column('device_name', sa.String(length=150), nullable=True),
        sa.Column('location_city', sa.String(length=100), nullable=True),
        sa.Column('location_region', sa.String(length=100), nullable=True),
        sa.Column('location_country', sa.String(length=100), nullable=True),
        sa.Column('location_lat', sa.Float(), nullable=True),
        sa.Column('location_lon', sa.Float(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('device_token', sa.String(length=255), nullable=True),
        sa.Column('login_success', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('failure_reason', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_login_history_id', 'login_history', ['id'])
    op.create_index('ix_login_history_user_id', 'login_history', ['user_id'])
    op.create_index('ix_login_history_login_time', 'login_history', ['login_time'])
    op.create_index('ix_login_history_session_id', 'login_history', ['session_id'])
    
    # Add new columns to refresh_tokens table
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_used_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True))
        batch_op.add_column(sa.Column('ip_address', sa.String(length=45), nullable=True))
        batch_op.add_column(sa.Column('device_type', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('os', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('browser', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('device_name', sa.String(length=150), nullable=True))


def downgrade():
    # Remove columns from refresh_tokens table
    with op.batch_alter_table('refresh_tokens', schema=None) as batch_op:
        batch_op.drop_column('device_name')
        batch_op.drop_column('browser')
        batch_op.drop_column('os')
        batch_op.drop_column('device_type')
        batch_op.drop_column('ip_address')
        batch_op.drop_column('last_used_at')
    
    # Drop login_history table
    op.drop_index('ix_login_history_session_id', table_name='login_history')
    op.drop_index('ix_login_history_login_time', table_name='login_history')
    op.drop_index('ix_login_history_user_id', table_name='login_history')
    op.drop_index('ix_login_history_id', table_name='login_history')
    op.drop_table('login_history')
