#!/usr/bin/env python3
"""
Enhanced RAG System Validation Script

This script validates that the enhanced RAG system is properly configured:
1. Database columns exist
2. Services can be imported
3. Dependencies are installed

Run this before starting the backend to ensure everything works.
"""

import sys

def validate_imports():
    """Check that all required modules can be imported."""
    print("🔍 Validating Python imports...")
    
    try:
        import numpy
        print("  ✅ numpy")
    except ImportError:
        print("  ❌ numpy - Run: pip install numpy==1.26.2")
        return False
    
    try:
        from app.services.technical_trend_analyzer import TechnicalTrendAnalyzer
        print("  ✅ TechnicalTrendAnalyzer")
    except ImportError as e:
        print(f"  ❌ TechnicalTrendAnalyzer - {e}")
        return False
    
    try:
        from app.services.prediction_accuracy_tracker import PredictionAccuracyTracker
        print("  ✅ PredictionAccuracyTracker")
    except ImportError as e:
        print(f"  ❌ PredictionAccuracyTracker - {e}")
        return False
    
    try:
        from app.models.analysis_cache import AnalysisCache
        print("  ✅ AnalysisCache model")
    except ImportError as e:
        print(f"  ❌ AnalysisCache - {e}")
        return False
    
    try:
        from app.models.technical_indicator_history import TechnicalIndicatorHistory
        print("  ✅ TechnicalIndicatorHistory model")
    except ImportError as e:
        print(f"  ❌ TechnicalIndicatorHistory - {e}")
        return False
    
    return True

def validate_database():
    """Check database connection and table structure."""
    print("\n🔍 Validating database...")
    
    try:
        from app.core.database import engine
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        
        # Check if analysis_cache table has new columns
        if "analysis_cache" in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('analysis_cache')]
            
            required_columns = [
                'price', 'rsi', 'macd', 'macd_histogram', 'bb_upper',
                'prediction_text', 'prediction_direction', 'confidence'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"  ⚠️  Missing columns in analysis_cache: {', '.join(missing_columns)}")
                print("  ℹ️  Run migration: python migrations/001_enhanced_rag_tracking.py")
                return False
            else:
                print("  ✅ analysis_cache table has all required columns")
        else:
            print("  ⚠️  analysis_cache table doesn't exist")
            return False
        
        # Check if technical_indicator_history exists
        if "technical_indicator_history" in inspector.get_table_names():
            print("  ✅ technical_indicator_history table exists")
        else:
            print("  ⚠️  technical_indicator_history table doesn't exist")
            print("  ℹ️  Run migration: python migrations/001_enhanced_rag_tracking.py")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

def main():
    """Run all validations."""
    print("=" * 60)
    print("🚀 Enhanced RAG System Validation")
    print("=" * 60)
    
    imports_ok = validate_imports()
    database_ok = validate_database()
    
    print("\n" + "=" * 60)
    if imports_ok and database_ok:
        print("✅ All validations passed! System ready.")
        print("=" * 60)
        return 0
    else:
        print("❌ Some validations failed. Fix issues before starting backend.")
        print("=" * 60)
        return 1

if __name__ == "__main__":
    sys.exit(main())
