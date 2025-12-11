import sys
from sqlalchemy import create_engine, text

# Hardcoded connection for local reset script (matches docker-compose ports)
# User: stockmarket_user, Pass: secure_password_123, DB: stockmarket_db, Port: 3306 (mapped to host)
DATABASE_URL = "mysql+pymysql://stockmarket_user:secure_password_123@localhost:3306/stockmarket_db"

def reset_sql_table():
    print(f"Connecting to database: {DATABASE_URL}")
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            print("Dropping table 'analysis_cache'...")
            connection.execute(text("DROP TABLE IF EXISTS analysis_cache"))
            connection.commit()
            print("✅ Table 'analysis_cache' dropped successfully.")
            
    except Exception as e:
        print(f"❌ Error dropping table: {e}")
        sys.exit(1)

if __name__ == "__main__":
    reset_sql_table()
