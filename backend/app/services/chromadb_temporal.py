"""
Dynamic ChromaDB Temporal Retrieval - Enhancement to embeddings.py

Adds intelligent historical analysis retrieval with:
- Temporal decay scoring (recent = higher score)
- Quality scoring (confidence + completeness)
- Smart deduplication (1 per day, keeps best)
- Temporal diversity (max 2 per week)
- Adaptive time windows

Formula: score = (temporal_score * 0.6) + (quality_score * 0.4)
"""

import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict

def retrieve_historical_analyses_dynamic(
    embedding_service,
    ticker: str,
    days_back: int = 45,
    max_analyses: int = 5,
    temporal_decay_lambda: float = 0.05,
    temporal_weight: float = 0.6,
    quality_weight: float = 0.4,
    max_per_week: int = 2
) -> List[Dict[str, Any]]:
    """
    Dynamically retrieve historical analyses with temporal decay + quality scoring.
    
    Algorithm:
    1. Fetch all analyses from last N days
    2. Calculate temporal_score = e^(-λ * days_old)  
    3. Calculate quality_score based on confidence + completeness
    4. combined_score = (temporal * 0.6) + (quality * 0.4)
    5. Deduplicate: Keep best per day
    6. Ensure diversity: Max 2 per week
    7. Return top N by score
    
    Args:
        embedding_service: EmbeddingService instance
        ticker: Stock ticker
        days_back: How far back to search
        max_analyses: Number of analyses to return
        temporal_decay_lambda: Decay rate (higher = faster decay)
        temporal_weight: Weight for recency (0-1)
        quality_weight: Weight for quality (0-1)
        max_per_week: Max analyses per week for diversity
        
    Returns:
        List of top-scored historical analyses
    """
    # Calculate time boundary
    now = datetime.now()
    cutoff_timestamp = int((now - timedelta(days=days_back)).timestamp())
    
    # Fetch all historical analyses for ticker
    filter_metadata = {
        "$and": [
            {"type": {"$eq": "historical_analysis"}},
            {"ticker": {"$eq": ticker}}
        ]
    }
    
    try:
        results = embedding_service.get_documents(
            where=filter_metadata,
            limit=100,  # Fetch more to ensure we have enough after filtering
            collection_type="analysis"
        )
    except:
        return []
    
    if not results or 'ids' not in results:
        return []
    
    # Combine results with metadata
    analyses = []
    for idx in range(len(results['ids'])):
        metadata = results['metadatas'][idx]
        document = results['documents'][idx]
        
        # Parse timestamp
        timestamp_unix = metadata.get('timestamp_unix', 0)
        if timestamp_unix < cutoff_timestamp:
            continue  # Skip old analyses
        
        analyses.append({
            'id': results['ids'][idx],
            'document': document,
            'metadata': metadata,
            'timestamp_unix': timestamp_unix
        })
    
    if not analyses:
        return []
    
    # Calculate scores for each analysis
    now_timestamp = int(now.timestamp())
    
    for analysis in analyses:
        # Temporal score: e^(-λ * days_old)
        days_old = (now_timestamp - analysis['timestamp_unix']) / (24 * 3600)
        temporal_score = math.exp(-temporal_decay_lambda * days_old)
        
        # Quality score: confidence + completeness + reliability
        metadata = analysis['metadata']
        confidence = metadata.get('confidence', 0.5)
        
        # Completeness: check if key fields exist
        completeness_factors = [
            'prediction_direction' in metadata,
            'sentiment_classification' in metadata,
            len(metadata.get('risk_factors', [])) > 0,
            len(metadata.get('key_insights', [])) > 0
        ]
        completeness = sum(completeness_factors) / len(completeness_factors)
        
        # Source reliability (higher for certain sources)
        reliability = metadata.get('reliability', 0.7)
        
        # Combined quality score
        quality_score = (confidence * 0.5) + (completeness * 0.3) + (reliability * 0.2)
        
        # Final combined score
        combined_score = (temporal_score * temporal_weight) + (quality_score * quality_weight)
        
        analysis['temporal_score'] = temporal_score
        analysis['quality_score'] = quality_score
        analysis['combined_score'] = combined_score
    
    # Sort by combined score
    analyses.sort(key=lambda x: x['combined_score'], reverse=True)
    
    # Smart deduplication: Keep best per day
    seen_dates = {}
    unique_analyses = []
    
    for analysis in analyses:
        timestamp = analysis['timestamp_unix']
        date_key = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        
        # Keep first (best) analysis per day
        if date_key not in seen_dates:
            seen_dates[date_key] = True
            unique_analyses.append(analysis)
    
    # Temporal diversity: Max N per week
    if max_per_week > 0:
        week_counts = defaultdict(int)
        diverse_analyses = []
        
        for analysis in unique_analyses:
            timestamp = analysis['timestamp_unix']
            # Get week number
            dt = datetime.fromtimestamp(timestamp)
            week_key = f"{dt.year}-W{dt.isocalendar()[1]}"
            
            if week_counts[week_key] < max_per_week:
                week_counts[week_key] += 1
                diverse_analyses.append(analysis)
        
        unique_analyses = diverse_analyses
    
    # Return top N
    final_analyses = unique_analyses[:max_analyses]
    
    return final_analyses
