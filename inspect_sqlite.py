import sqlite3
import os

def inspect_sqlite():
    db_path = os.path.join(os.getcwd(), 'backend', 'data', 'chroma_db', 'chroma.sqlite3')
    print(f"Connecting to SQLite at {db_path}...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("\n📊 SQLite Tables:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for t in tables:
            print(f"• {t[0]}")
            
        print("\n📊 SQLite Collection Inspection:")
        print("-" * 30)
        
        # List collections
        cursor.execute("SELECT name, id FROM collections")
        collections = cursor.fetchall()
        
        if not collections:
            print("❌ No collections found in 'collections' table.")
        else:
            for name, col_id in collections:
                # Count embeddings for this collection
                cursor.execute("SELECT count(*) FROM embeddings WHERE collection_id = ?", (col_id,))
                count = cursor.fetchone()[0]
                print(f"• {name} (ID: {col_id}): {count} embeddings")
                
        print("-" * 30)
        conn.close()
            
    except Exception as e:
        print(f"❌ Error inspecting SQLite: {e}")

if __name__ == "__main__":
    inspect_sqlite()
