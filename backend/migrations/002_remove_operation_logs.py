"""
Database migration script: Remove operation_logs and data_source_status tables.
These tables are no longer needed as we're simplifying the monitoring system.
"""

from sqlalchemy import text
from app.core.database import engine

def upgrade():
    """Remove operation logging tables."""
    with engine.begin() as connection:
        print("Dropping table 'operation_logs'...")
        connection.execute(text("DROP TABLE IF EXISTS operation_logs"))
        print("✅ Table 'operation_logs' dropped successfully.")
        
        print("Dropping table 'data_source_status'...")
        connection.execute(text("DROP TABLE IF EXISTS data_source_status"))
        print("✅ Table 'data_source_status' dropped successfully.")

def downgrade():
    """Recreate operation logging tables if needed."""
    print("⚠️  Downgrade not implemented - tables would need manual recreation")
    print("⚠️  Refer to app/models/operation_log.py in git history for schema")

if __name__ == "__main__":
    print("=" * 80)
    print("MIGRATION: Remove Operation Logging Tables")
    print("=" * 80)
    upgrade()
    print("=" * 80)
    print("✅ Migration complete!")
    print("=" * 80)
