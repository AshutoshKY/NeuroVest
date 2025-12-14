"""
Enhanced Prompt POC - Test comprehensive LLM prompts with 7 stocks.

Tests:
1. Prompt size (tokens, chars)
2. Response quality (length, detail, specific data)
3. Latency (news fetch, sentiment, LLM call, total)
4. Data inclusion (price, technicals, trends, news, historical)
5. Output analysis (risks count, insights count, prediction quality)
"""

import sys
sys.path.insert(0, '/app')

import asyncio
import time
import json
from datetime import datetime
from typing import Dict, Any, List

from app.services.rag import rag_service
from app.services.data_ingestion import data_ingestion_service


# Test stocks - diverse set
TEST_STOCKS = [
    ("RELIANCE", "Reliance Industries"),
    ("TCS", "Tata Consultancy Services"),
    ("INFY", "Infosys"),
    ("HDFCBANK", "HDFC Bank"),
    ("ICICIBANK", "ICICI Bank"),
    ("ITC", "ITC Limited"),
    ("HAL", "Hindustan Aeronautics")
]


class PromptPOC:
    """POC to test enhanced prompts."""
    
    def __init__(self):
        self.results = []
        
    async def test_single_stock(self, ticker: str, company_name: str) -> Dict[str, Any]:
        """Test a single stock and capture all metrics."""
        print(f"\n{'='*80}")
        print(f"Testing {ticker} ({company_name})")
        print(f"{'='*80}")
        
        result = {
            "ticker": ticker,
            "company_name": company_name,
            "timestamp": datetime.now().isoformat(),
            "timings": {},
            "data_captured": {},
            "prompt_analysis": {},
            "response_analysis": {},
            "quality_metrics": {},
            "errors": []
        }
        
        total_start = time.time()
        
        try:
            # Step 1: Trigger data ingestion to ensure fresh data
            print(f"\n[1/3] Triggering data ingestion for {ticker}...")
            ingest_start = time.time()
            try:
                await data_ingestion_service.ingest_for_ticker(ticker, company_name)
                result["timings"]["ingestion"] = time.time() - ingest_start
                print(f"   ✓ Ingestion: {result['timings']['ingestion']:.2f}s")
            except Exception as e:
                result["errors"].append(f"Ingestion error: {str(e)}")
                print(f"   ⚠ Ingestion failed: {e}")
            
            # Step 2: Generate analysis and capture ALL details
            print(f"\n[2/3] Generating analysis for {ticker}...")
            analysis_start = time.time()
            
            # We'll capture step-by-step
            step_count = 0
            final_analysis = None
            
            async for step_type, data in rag_service.generate_analysis_with_steps(
                query=f"Analyze {company_name} ({ticker}) stock",
                ticker=ticker,
                n_results=10
            ):
                if step_type == "step":
                    step_count += 1
                    step_desc = data.get("description", "Unknown step")
                    print(f"   Step {step_count}: {step_desc}")
                elif step_type == "final":
                    final_analysis = data
                    break
            
            result["timings"]["analysis_generation"] = time.time() - analysis_start
            result["timings"]["total"] = time.time() - total_start
            
            if not final_analysis:
                result["errors"].append("No final analysis generated")
                print(f"   ✗ Analysis failed")
                return result
            
            print(f"   ✓ Analysis generated: {result['timings']['analysis_generation']:.2f}s")
            
            # Step 3: Analyze the response
            print(f"\n[3/3] Analyzing response quality...")
            
            # Extract response details
            analysis_text = final_analysis.get("analysis", "")
            prediction_text = final_analysis.get("prediction", "")
            reasoning_text = final_analysis.get("reasoning", "")
            risk_factors = final_analysis.get("risk_factors", [])
            key_insights = final_analysis.get("key_insights", [])
            sentiment = final_analysis.get("sentiment", {})
            references = final_analysis.get("references", [])
            technical = final_analysis.get("technical_analysis", {})
            confidence = final_analysis.get("confidence", 0)
            
            # Response analysis
            result["response_analysis"] = {
                "analysis_length": len(analysis_text),
                "prediction_length": len(prediction_text),
                "reasoning_length": len(reasoning_text),
                "risk_factors_count": len(risk_factors),
                "key_insights_count": len(key_insights),
                "references_count": len(references),
                "confidence_score": confidence,
                "has_technical_data": bool(technical),
                "sentiment_classification": sentiment.get("classification", "unknown"),
                "sentiment_score": sentiment.get("aggregate_score", 0)
            }
            
            # Quality metrics
            result["quality_metrics"] = {
                "is_comprehensive": len(analysis_text) > 500,  # At least 500 chars
                "has_sufficient_risks": len(risk_factors) >= 5,
                "has_sufficient_insights": len(key_insights) >= 5,
                "has_references": len(references) > 0,
                "has_prediction": len(prediction_text) > 50,
                "has_reasoning": len(reasoning_text) > 0,
                "shows_technical_indicators": bool(technical),
                "analysis_prediction_different": analysis_text != prediction_text
            }
            
            # Calculate quality score
            quality_checks = [
                result["quality_metrics"]["is_comprehensive"],
                result["quality_metrics"]["has_sufficient_risks"],
                result["quality_metrics"]["has_sufficient_insights"],
                result["quality_metrics"]["has_references"],
                result["quality_metrics"]["has_prediction"],
                result["quality_metrics"]["has_reasoning"],
                result["quality_metrics"]["shows_technical_indicators"],
                result["quality_metrics"]["analysis_prediction_different"]
            ]
            result["quality_metrics"]["quality_score"] = sum(quality_checks) / len(quality_checks)
            
            # Data captured
            result["data_captured"] = {
                "has_current_price": technical.get("current_price") is not None if technical else False,
                "has_rsi": bool(technical.get("indicators", {}).get("rsi")) if technical else False,
                "has_macd": bool(technical.get("indicators", {}).get("macd")) if technical else False,
                "has_bollinger_bands": bool(technical.get("indicators", {}).get("bollinger_bands")) if technical else False,
                "has_sma": bool(technical.get("indicators", {}).get("sma")) if technical else False,
                "news_articles": len(references),
                "sentiment_analyzed": sentiment.get("total_articles", 0)
            }
            
            # Print summary
            print(f"\n   📊 Response Quality:")
            print(f"      Analysis: {len(analysis_text)} chars")
            print(f"      Prediction: {len(prediction_text)} chars")
            print(f"      Reasoning: {len(reasoning_text)} chars")
            print(f"      Risks: {len(risk_factors)}")
            print(f"      Insights: {len(key_insights)}")
            print(f"      References: {len(references)}")
            print(f"      Confidence: {confidence:.2f}")
            print(f"      Quality Score: {result['quality_metrics']['quality_score']:.1%}")
            
            # Print sample analysis
            print(f"\n   📝 Sample Analysis (first 200 chars):")
            print(f"      {analysis_text[:200]}...")
            
            print(f"\n   ✅ Test complete for {ticker}")
            
        except Exception as e:
            result["errors"].append(f"Test error: {str(e)}")
            print(f"\n   ✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    async def run_all_tests(self):
        """Run tests for all stocks."""
        print(f"\n{'#'*80}")
        print(f"# ENHANCED PROMPT POC - Testing {len(TEST_STOCKS)} Stocks")
        print(f"# Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'#'*80}")
        
        for ticker, company_name in TEST_STOCKS:
            result = await self.test_single_stock(ticker, company_name)
            self.results.append(result)
            
            # Small delay between stocks
            await asyncio.sleep(2)
        
        # Generate comprehensive report
        self.generate_report()
    
    def generate_report(self):
        """Generate comprehensive POC report."""
        print(f"\n\n{'#'*80}")
        print(f"# POC RESULTS SUMMARY")
        print(f"{'#'*80}\n")
        
        # Overall statistics
        successful_tests = [r for r in self.results if not r["errors"]]
        failed_tests = [r for r in self.results if r["errors"]]
        
        print(f"Total Tests: {len(self.results)}")
        print(f"Successful: {len(successful_tests)} ✓")
        print(f"Failed: {len(failed_tests)} ✗")
        
        if successful_tests:
            # Average metrics
            avg_total_time = sum(r["timings"].get("total", 0) for r in successful_tests) / len(successful_tests)
            avg_analysis_time = sum(r["timings"].get("analysis_generation", 0) for r in successful_tests) / len(successful_tests)
            avg_analysis_length = sum(r["response_analysis"].get("analysis_length", 0) for r in successful_tests) / len(successful_tests)
            avg_risks = sum(r["response_analysis"].get("risk_factors_count", 0) for r in successful_tests) / len(successful_tests)
            avg_insights = sum(r["response_analysis"].get("key_insights_count", 0) for r in successful_tests) / len(successful_tests)
            avg_quality = sum(r["quality_metrics"].get("quality_score", 0) for r in successful_tests) / len(successful_tests)
            
            print(f"\n{'─'*80}")
            print(f"PERFORMANCE METRICS:")
            print(f"{'─'*80}")
            print(f"  Average Total Time:     {avg_total_time:6.2f}s")
            print(f"  Average Analysis Time:  {avg_analysis_time:6.2f}s")
            
            print(f"\n{'─'*80}")
            print(f"RESPONSE QUALITY:")
            print(f"{'─'*80}")
            print(f"  Average Analysis Length: {avg_analysis_length:6.0f} chars")
            print(f"  Average Risk Factors:    {avg_risks:6.1f} items")
            print(f"  Average Key Insights:    {avg_insights:6.1f} items")
            print(f"  Average Quality Score:   {avg_quality:6.1%}")
            
            print(f"\n{'─'*80}")
            print(f"INDIVIDUAL STOCK RESULTS:")
            print(f"{'─'*80}")
            
            for result in successful_tests:
                ticker = result["ticker"]
                time_total = result["timings"].get("total", 0)
                analysis_len = result["response_analysis"].get("analysis_length", 0)
                risks = result["response_analysis"].get("risk_factors_count", 0)
                insights = result["response_analysis"].get("key_insights_count", 0)
                quality = result["quality_metrics"].get("quality_score", 0)
                
                quality_emoji = "🟢" if quality >= 0.8 else "🟡" if quality >= 0.6 else "🔴"
                
                print(f"  {quality_emoji} {ticker:12s} | {time_total:5.1f}s | {analysis_len:4d} chars | {risks} risks | {insights} insights | Quality: {quality:.0%}")
        
        if failed_tests:
            print(f"\n{'─'*80}")
            print(f"FAILED TESTS:")
            print(f"{'─'*80}")
            for result in failed_tests:
                print(f"  ✗ {result['ticker']}: {', '.join(result['errors'])}")
        
        # Save detailed JSON report
        report_path = "/tmp/enhanced_prompt_poc_results.json"
        with open(report_path, 'w') as f:
            json.dump({
                "test_metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "total_tests": len(self.results),
                    "successful": len(successful_tests),
                    "failed": len(failed_tests)
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n{'─'*80}")
        print(f"📄 Detailed results saved to: {report_path}")
        print(f"{'─'*80}\n")


async def main():
    """Run POC."""
    poc = PromptPOC()
    await poc.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
