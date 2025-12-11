"""
Test sentiment analysis accuracy against labeled dataset.
"""
import sys
import os
sys.path.insert(0, '/app')

import pandas as pd
from app.services.sentiment import sentiment_service
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix


def load_ground_truth():
    """Load manually labeled dataset."""
    return pd.read_csv('/app/app/tests/data/sentiment_ground_truth.csv')


def test_sentiment_accuracy():
    """Test overall sentiment classification accuracy."""
    print("\n" + "="*60)
    print("SENTIMENT ANALYSIS ACCURACY TEST")
    print("="*60)
    
    # Load ground truth
    df = load_ground_truth()
    print(f"\nLoaded {len(df)} ground truth samples")
    
    # Get predictions
    predictions = []
    confidences = []
    
    print("\nAnalyzing articles...")
    for i, text in enumerate(df['article_text'], 1):
        print(f"  [{i}/{len(df)}] Processing...", end='\r')
        result = sentiment_service.analyze_sentiment(text, ticker=df.iloc[i-1]['ticker'])
        predictions.append(result['classification'].lower())
        confidences.append(result['confidence'])
    
    print(f"\n  ✓ Completed {len(predictions)} predictions")
    
    # Calculate metrics
    true_labels = df['true_sentiment'].tolist()
    accuracy = accuracy_score(true_labels, predictions)
    precision, recall, f1, _ = precision_recall_fscore_support(
        true_labels, 
        predictions,
        labels=['bullish', 'neutral', 'bearish'],
        average='weighted',
        zero_division=0
    )
    
    # Confusion matrix
    cm = confusion_matrix(
        true_labels, 
        predictions,
        labels=['bullish', 'neutral', 'bearish']
    )
    
    print(f"\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"\n📊 Overall Metrics:")
    print(f"   Accuracy:  {accuracy:.2%}")
    print(f"   Precision: {precision:.2%}")
    print(f"   Recall:    {recall:.2%}")
    print(f"   F1-Score:  {f1:.2%}")
    
    print(f"\n📈 Confusion Matrix:")
    print(f"                Predicted")
    print(f"              Bullish  Neutral  Bearish")
    print(f"   Bullish    {cm[0][0]:6}   {cm[0][1]:6}   {cm[0][2]:6}")
    print(f"   Neutral    {cm[1][0]:6}   {cm[1][1]:6}   {cm[1][2]:6}")
    print(f"   Bearish    {cm[2][0]:6}   {cm[2][1]:6}   {cm[2][2]:6}")
    
    # Confidence analysis
    avg_confidence = sum(confidences) / len(confidences)
    high_conf_count = sum(1 for c in confidences if c >= 0.7)
    
    print(f"\n🎯 Confidence Analysis:")
    print(f"   Average Confidence: {avg_confidence:.2%}")
    print(f"   High Confidence (≥0.7): {high_conf_count}/{len(confidences)} ({high_conf_count/len(confidences):.0%})")
    
    # Sample predictions
    print(f"\n📝 Sample Predictions:")
    for i in range(min(5, len(df))):
        status = "✓" if predictions[i] == true_labels[i] else "✗"
        print(f"   {status} True: {true_labels[i]:8} | Predicted: {predictions[i]:8} | Confidence: {confidences[i]:.2%}")
        print(f"      '{df.iloc[i]['article_text'][:80]}...'")
    
    # Assessment
    print(f"\n" + "="*60)
    if accuracy >= 0.70:
        print("✅ PASS: Sentiment accuracy meets threshold (≥70%)")
    else:
        print(f"❌ FAIL: Sentiment accuracy {accuracy:.2%} below threshold 70%")
    print("="*60 + "\n")
    
    return {
        'accuracy': accuracy,
        'precision': precision,
        'recall': recall,
        'f1': f1,
        'avg_confidence': avg_confidence
    }


if __name__ == "__main__":
    test_sentiment_accuracy()
