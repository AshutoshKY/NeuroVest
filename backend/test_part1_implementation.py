"""
Test Script for Part 1 Implementation
Tests Components 1-4: Signal Engine, Pipelines, Price Ranges, Scenarios
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.signal_engine.service import build_full_signal
from app.pipelines.orchestrator import pipeline_orchestrator
from app.price_engine.ranges import calculate_price_ranges
from app.scenario_engine import generate_scenarios


async def test_signal_engine(symbol: str = "RELIANCE.NS"):
    """Test Component 1: Signal Engine"""
    
    print("=" * 80)
    print(f"TEST 1: Signal Engine - {symbol}")
    print("=" * 80)
    
    try:
        signal = await build_full_signal(symbol, timeframe="swing")
        
        print(f"\n✓ Signal Generated Successfully")
        print(f"  Symbol: {signal.symbol}")
        print(f"  Directional Bias: {signal.signal_summary.directional_bias}")
        print(f"  Confidence: {signal.signal_summary.confidence_score}")
        print(f"  Primary Signal: {signal.signal_summary.primary_signal}")
        print(f"  Risk Level: {signal.signal_summary.risk_level}")
        print(f"\n  Trend: {signal.trend.trend_state} ({signal.trend.strength})")
        print(f"  RSI: {signal.momentum.rsi_14:.1f} ({signal.momentum.rsi_regime})")
        print(f"  ATR: {signal.volatility.atr_14:.2f} ({signal.volatility.atr_percent:.2f}%)")
        print(f"  Volume: {signal.volume.today_vs_20d_avg:.2f}x average")
        print(f"\n  Market Context:")
        print(f"    NIFTY: {signal.market_context.nifty_trend} ({signal.market_context.nifty_close:.2f})")
        print(f"    India VIX: {signal.market_context.india_vix:.2f} ({signal.market_context.vix_regime})")
        
        return signal
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_pipelines(symbol: str = "INFY.NS"):
    """Test Component 2: Time Horizon Pipelines"""
    
    print("\n" + "=" * 80)
    print(f"TEST 2: Time Horizon Pipelines - {symbol}")
    print("=" * 80)
    
    # Test swing pipeline
    try:
        print("\n[Swing Pipeline - 3-10 days]")
        swing_signal = await pipeline_orchestrator.execute(symbol, timeframe="swing")
        print(f"✓ Swing: {swing_signal.signal_summary.directional_bias} (confidence: {swing_signal.signal_summary.confidence_score})")
        
        # Show pipeline info
        swing_info = pipeline_orchestrator.get_pipeline_info("swing")
        print(f"  Typical Holding: {swing_info['typical_holding_days']} days")
        print(f"  Data Interval: {swing_info['data_interval']}")
        print(f"  Risk Multiplier: {swing_info['risk_multiplier']}x ATR")
        
    except Exception as e:
        print(f"✗ Swing pipeline error: {e}")
    
    # Test positional pipeline
    try:
        print("\n[Positional Pipeline - 2-8 weeks]")
        positional_signal = await pipeline_orchestrator.execute(symbol, timeframe="positional")
        print(f"✓ Positional: {positional_signal.signal_summary.directional_bias} (confidence: {positional_signal.signal_summary.confidence_score})")
        
        pos_info = pipeline_orchestrator.get_pipeline_info("positional")
        print(f"  Typical Holding: {pos_info['typical_holding_days']} days ({pos_info['typical_holding_days']//7} weeks)")
        print(f"  Data Interval: {pos_info['data_interval']}")
        print(f"  Risk Multiplier: {pos_info['risk_multiplier']}x ATR")
        
    except Exception as e:
        print(f"✗ Positional pipeline error: {e}")


async def test_price_ranges_and_scenarios(signal):
    """Test Components 3-4: Price Ranges and Scenarios"""
    
    if signal is None:
        print("\nSkipping price ranges test (no signal)")
        return
    
    print("\n" + "=" * 80)
    print("TEST 3: Price Range Engine")
    print("=" * 80)
    
    try:
        envelopes = calculate_price_ranges(signal, timeframe_days=7)
        
        print(f"\n✓ Price Ranges Calculated")
        print(f"  Current Price: ₹{signal.price.last_close:.2f}")
        print(f"\n  Base Case: ₹{envelopes.base_case.lower:.2f} - ₹{envelopes.base_case.upper:.2f}")
        print(f"  Bull Case: ₹{envelopes.bull_case.lower:.2f} - ₹{envelopes.bull_case.upper:.2f}")
        print(f"  Bear Case: ₹{envelopes.bear_case.lower:.2f} - ₹{envelopes.bear_case.upper:.2f}")
        print(f"  Invalidation: ₹{envelopes.invalidation_level:.2f}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 80)
    print("TEST 4: Scenario Generator")
    print("=" * 80)
    
    try:
        scenarios = generate_scenarios(signal, envelopes, risk_score=45, timeframe_days=7)
        
        print(f"\n✓ Scenarios Generated")
        for scenario in scenarios.scenarios:
            print(f"\n  {scenario.name} ({scenario.probability*100:.0f}%)")
            print(f"    Range: ₹{scenario.price_range[0]:.2f} - ₹{scenario.price_range[1]:.2f}")
            print(f"    Drivers: {', '.join(scenario.drivers)}")
            print(f"    Invalidation: {scenario.invalidation}")
        
        # Verify probabilities sum to 1.0
        total_prob = sum(s.probability for s in scenarios.scenarios)
        print(f"\n  Probability Check: {total_prob:.2f} (should be 1.00)")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    
    print("\n" + "=" * 100)
    print(" " * 30 + "PART 1 IMPLEMENTATION TEST SUITE")
    print(" " * 25 + "Components 1-4: Signal Engine → Scenarios")
    print("=" * 100)
    
    # Test with RELIANCE
    print("\n" + "-" * 100)
    print("Testing with RELIANCE.NS")
    print("-" * 100)
    signal = await test_signal_engine("RELIANCE.NS")
    await test_price_ranges_and_scenarios(signal)
    
    # Test pipelines with INFY
    await test_pipelines("INFY.NS")
    
    print("\n" + "=" * 100)
    print(" " * 40 + "TESTS COMPLETE")
    print("=" * 100)
    print("\nNext Steps:")
    print("  1. Review output above for any errors")
    print("  2. Test API endpoints: http://localhost:8000/api/signal/{symbol}")
    print("  3. Proceed to Part 2: Components 5-9 (Sentiment, Relative Strength, Risk Scoring, LLM, Validator)")
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
