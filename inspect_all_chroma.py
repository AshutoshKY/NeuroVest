import sys
import os
import chromadb
from chromadb.config import Settings
import json

def inspect_all_analyses(ticker="HAL"):
    print(f"🕵️ Inspecting ALL ChromaDB entries for {ticker}...\n")
    
    # Correct path to backend data
    db_path = os.path.join(os.getcwd(), 'backend', 'data', 'chroma_db')
    
    try:
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        print(f"📂 ChromaDB Path: {db_path}")
        collections = client.list_collections()
        print(f"📚 Available collections: {[c.name for c in collections]}\n")
        
        if "stock_analysis" not in [c.name for c in collections]:
            print("❌ Collection 'stock_analysis' NOT found.")
            return

        collection = client.get_collection("stock_analysis")
        total_count = collection.count()
        print(f"📚 Total documents in 'stock_analysis' collection: {total_count}\n")
        
        # Query for ALL documents for this ticker (no limit)
        print(f"🔎 Querying for ALL documents with type='historical_analysis' and ticker='{ticker}'...\n")
        results = collection.get(
            where={"$and": [{"type": "historical_analysis"}, {"ticker": ticker}]},
            include=["metadatas", "documents"]
        )
        
        if not results['ids']:
            print(f"❌ No historical analysis found for {ticker}.")
            return

        print(f"✅ Found {len(results['ids'])} document(s) for {ticker}.\n")
        print("=" * 80)
        
        # Print all documents
        for idx, (doc_id, meta, doc) in enumerate(zip(results['ids'], results['metadatas'], results['documents']), 1):
            print(f"\n### DOCUMENT {idx}/{len(results['ids'])} ###")
            print(f"ID: {doc_id}\n")
            
            print("=== 📄 METADATA ===")
            print(f"Timestamp: {meta.get('timestamp')}")
            print(f"Sentiment: {meta.get('sentiment_classification')} (Score: {meta.get('sentiment_score')}, Confidence: {meta.get('confidence')})")
            print(f"Price: ₹{meta.get('price')} | Prev Close: ₹{meta.get('previous_close')}")
            print(f"Day High: ₹{meta.get('day_high')} | Day Low: ₹{meta.get('day_low')} | Volume: {meta.get('volume')}")
            print(f"RSI: {meta.get('rsi')} | MACD Trend: {meta.get('macd_trend')} | BB Position: {meta.get('bb_position')}")
            print(f"Prediction Direction: {meta.get('prediction_direction')}\n")
            
            # Parse JSON fields
            if meta.get('risk_factors'):
                risks = json.loads(meta['risk_factors']) if isinstance(meta['risk_factors'], str) else meta['risk_factors']
                print(f"=== ⚠️ RISK FACTORS ({len(risks)}) ===")
                for i, risk in enumerate(risks, 1):
                    print(f"{i}. {risk}")
                print()
            
            if meta.get('key_insights'):
                insights = json.loads(meta['key_insights']) if isinstance(meta['key_insights'], str) else meta['key_insights']
                print(f"=== 💡 KEY INSIGHTS ({len(insights)}) ===")
                for i, insight in enumerate(insights, 1):
                    print(f"{i}. {insight}")
                print()
            
            if meta.get('prediction_summary'):
                print(f"=== 🔮 PREDICTION SUMMARY ===")
                print(meta['prediction_summary'][:300] + "..." if len(meta['prediction_summary']) > 300 else meta['prediction_summary'])
                print()
            
            print("=" * 80)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "HAL"
    inspect_all_analyses(ticker)
