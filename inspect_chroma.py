import sys
import os
import chromadb
from chromadb.config import Settings
import json

def inspect_chroma_metadata():
    print("🕵️ Inspecting ChromaDB metadata for HAL...")
    
    # Correct path to backend data
    db_path = os.path.join(os.getcwd(), 'backend', 'data', 'chroma_db')
    
    try:
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        print(f"📂 ChromaDB Path: {db_path}")
        collections = client.list_collections()
        print(f"📚 Available collections: {[c.name for c in collections]}")
        
        if "stock_analysis" not in [c.name for c in collections]:
            print("❌ Collection 'stock_analysis' NOT found.")
            return

        collection = client.get_collection("stock_analysis")
        count = collection.count()
        print(f"📚 Total documents in collection: {count}")
        
        # Query for HAL related documents
        print("🔎 Querying for type='historical_analysis' and ticker='HAL'...")
        results = collection.get(
            where={"$and": [{"type": "historical_analysis"}, {"ticker": "HAL"}]},
            limit=1,
            include=["metadatas", "documents"]
        )
        
        if not results['ids']:
            print("❌ No historical analysis found for HAL.")
            return

        print(f"✅ Found {len(results['ids'])} documents for HAL.")
        
        # Print details for the first result
        meta = results['metadatas'][0]
        doc = results['documents'][0]
        
        print("\n=== 📄 RAW METADATA (Stored in DB) ===")
        print(json.dumps(meta, indent=2))
        
        print("\n=== 📝 CONVERTED FORM (Document Content) ===")
        print(doc)
        
        print("\n=== 🔍 JSON FIELD INSPECTION ===")
        if 'risk_factors' in meta:
            print(f"Risk Factors (Parsed): {json.loads(meta['risk_factors'])}")
        if 'key_insights' in meta:
            print(f"Key Insights (Parsed): {json.loads(meta['key_insights'])}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    inspect_chroma_metadata()
