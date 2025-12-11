import chromadb
import os

def inspect_counts():
    # Correct path to backend data
    db_path = os.path.join(os.getcwd(), 'backend', 'data', 'chroma_db')
    print(f"Connecting to ChromaDB at {db_path}...")
    
    try:
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        
        print("\n📊 ChromaDB Collection Counts:")
        print("-" * 30)
        
        total = 0
        for c in collections:
            count = c.count()
            print(f"• {c.name}: {count} documents")
            total += count
            
        print("-" * 30)
        print(f"Total Documents: {total}")
            
    except Exception as e:
        print(f"❌ Error inspecting ChromaDB: {e}")

if __name__ == "__main__":
    inspect_counts()
