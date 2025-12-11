import chromadb
import os
import shutil

def reset_chroma():
    # Path relative to project root (where script is run)
    # Docker maps ./backend/data to /app/data, so we must target backend/data
    db_path = os.path.join(os.getcwd(), 'backend', 'data', 'chroma_db')
    print(f"Connecting to ChromaDB at {db_path}...")
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        collection_name = "stock_analysis"
        
        # List collections to verify
        collections = client.list_collections()
        names = [c.name for c in collections]
        print(f"Existing collections: {names}")
        
        if not names:
            print("ℹ️ Database is already empty.")
            return

        for name in names:
            try:
                client.delete_collection(name)
                print(f"✅ Successfully deleted collection '{name}'")
            except Exception as e:
                print(f"❌ Error deleting collection '{name}': {e}")
            
    except Exception as e:
        print(f"❌ Error resetting ChromaDB: {e}")

if __name__ == "__main__":
    reset_chroma()
