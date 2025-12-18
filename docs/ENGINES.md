# ENGINE SPECIFICATIONS - Deep Dive

**Comprehensive technical documentation for all 7 core engines in the NeuroVest platform.**

---

## Table of Contents

1. [Signal Engine](#1-signal-engine)
2. [Scenario Engine](#2-scenario-engine)
3. [Risk Scoring Engine](#3-risk-scoring-engine)
4. [Price Engine](#4-price-engine)
5. [Sentiment Engine](#5-sentiment-engine)
6. [Narrative Validator](#6-narrative-validator)
7. [Backtesting Engine](#7-backtesting-engine)

---

## 1. SIGNAL ENGINE

### Purpose
Convert raw OHLCV data into classified market signals using technical indicators.

### Location
- `/app/signal_engine/service.py` - Main orchestrator
- `/app/signal_engine/signals.py` - Classification logic
- `/app/signal_engine/indicators.py` - Technical calculations

### Inputs
```python
{
  "symbol": "RELIANCE.NS",
  "df": pd.DataFrame,  # OHLCV data
  "timeframe": "swing" | "positional" | "intraday"
}
```

### Outputs
```python
{
  "symbol": "RELIANCE",
  "timeframe": "swing",
  "timestamp": "2024-01-15T09:00:00Z",
  "price": PriceContext,
  "trend": TrendData,
  "momentum": MomentumData,
  "volatility": VolatilityData,
  "structure": StructureData,
  "volume": VolumeData,
  "relative_strength": RelativeStrengthData,
  "market_context": MarketContext,
  "signal_summary": SignalSummary
}
```

### Signal Components

#### 1.1 Trend Classification
```python
def classify_trend(df):
    """
    Classifies trend state and strength.
    
    Returns:
        TrendData {
            trend_state: "bullish" | "bearish" | "sideways",
            strength: "strong" | "moderate" | "weak",
            support: float,
            resistance: float
        }
    """
```

**Algorithm**:
- Calculate 50-day and 200-day SMAs
- Price action relative to SMAs
- Swing high/low analysis
- Trend channel identification

**Key Assumptions**:
- Strong trend: Price > SMA200, consistent higher highs
- Weak trend: Choppy price action, frequent SMA crosses
- Sideways: Price oscillating within range

#### 1.2 Momentum Classification
```python
def classify_momentum(df):
    """
    Analyzes momentum strength and direction.
    
    Returns:
        MomentumData {
            momentum_state: "strong" | "moderate" | "weak",
            direction: "bullish" | "bearish" | "neutral",
            roc: float,  # Rate of change
            divergence: bool
        }
    """
```

**Algorithm**:
- Rate of change (ROC) calculation
- MACD histogram analysis
- Price vs volume momentum
- Divergence detection

#### 1.3 Volatility Classification
```python
def classify_volatility(df):
    """
    Measures volatility regime.
    
    Returns:
        VolatilityData {
            volatility_regime: "low" | "normal" | "high" | "extreme",
            atr: float,  # Average True Range
            atr_percent: float,
            expansion: bool
        }
    """
```

**Algorithm**:
- ATR calculation (14-period)
- ATR as % of price
- Volatility regime classification:
  - Low: ATR% < 1.5%
  - Normal: 1.5% - 3%
  - High: 3% - 5%
  - Extreme: > 5%

#### 1.4 Structure Classification
```python
def classify_structure(df):
    """
    Identifies price structure patterns.
    
    Returns:
        StructureData {
            pattern: "higher_highs" | "lower_lows" | "range_bound",
            swing_highs: List[float],
            swing_lows: List[float],
            support_strength: int,
            resistance_strength: int
        }
    """
```

#### 1.5 Volume Classification
```python
def classify_volume(df):
    """
    Analyzes volume patterns.
    
    Returns:
        VolumeData {
            volume_trend: "increasing" | "decreasing" | "stable",
            volume_vs_avg: float,  # Current/Average
            climax: bool,
            divergence: bool
        }
    """
```

### Signal Summary Generation
```python
def generate_signal_summary(trend, momentum, volatility, structure, volume):
    """
    Aggregates all signals into final summary.
    
    Returns:
        SignalSummary {
            directional_bias: "bullish" | "neutral" | "bearish",
            confidence_score: 0.0 - 1.0,
            momentum: "strong" | "moderate" | "weak",
            current_price: float,
            signal_conflicts: List[Dict]
        }
    """
```

**Directional Bias Logic**:
```python
if trend == "bullish" and momentum == "bullish":
    bias = "bullish"
elif trend == "bearish" and momentum == "bearish":
    bias = "bearish"
else:
    bias = "neutral"
```

**Confidence Calculation**:
```python
confidence = base_confidence
if trend.strength == "strong": confidence += 0.2
if no_conflicts: confidence += 0.1
if volatility == "low": confidence += 0.1
confidence = min(0.95, confidence)  # Cap at 95%
```

### Conflict Detection
```python
conflicts = []
if trend == "bullish" and momentum == "bearish":
    conflicts.append({
        "type": "trend_momentum_divergence",
        "severity": "high"
    })
```

### Example Output
```json
{
  "signal_summary": {
    "directional_bias": "bullish",
    "confidence_score": 0.75,
    "momentum": "strong",
    "current_price": 1550.0,
    "signal_conflicts": []
  }
}
```

---

## 2. SCENARIO ENGINE

### Purpose
Generate bounded market scenarios with deterministic probabilities.

### Location
`/app/scenario_engine/generator.py`

### Inputs
```python
{
  "market_state": {
    "trend_bias": "bullish|neutral|bearish",
    "confidence": 0.0-1.0,
    "momentum": "strong|moderate|weak",
    "volatility": "low|normal|high|extreme"
  },
  "price_zones": {
    "support": {"lower": float, "upper": float},
    "value_area": {"lower": float, "upper": float},
    "resistance": {"lower": float, "upper": float},
    "current_price": float
  },
  "signal_conflicts": List[Dict],
  "risk_score": 0.0-1.0
}
```

### Outputs
```python
[
  {
    "id": "bull_continuation_v1_abc123",
    "type": "bull",
    "description": "Bullish continuation toward resistance",
    "probability": 0.675,
    "trigger_conditions": "Hold above 1535 and break 1570",
    "invalidation_level": "Daily close below 1500",
    "target_zone": "1570-1600",
    "derived_from": {
      "trend_bias": "bullish",
      "confidence": 0.75,
      "has_conflicts": false
    }
  },
  ...  // 2-4 total scenarios
]
```

### Probability Calculation Logic

#### Rule 1: Bullish Bias
```python
if trend_bias == "bullish":
    if confidence >= 0.7 and not has_conflicts:
        # High confidence bullish
        bull_prob = 0.675
        base_prob = 0.25
        bear_prob = 0.075
    elif confidence >= 0.5 or has_conflicts:
        # Moderate confidence or conflicts
        bull_prob = 0.45
        base_prob = 0.40
        bear_prob = 0.15
```

#### Rule 2: Bearish Bias
```python
if trend_bias == "bearish":
    # Mirror of bullish logic
    bear_prob = 0.675 or 0.45
    base_prob = 0.25 or 0.40
    bull_prob = 0.075 or 0.15
```

#### Rule 3: Neutral Bias
```python
if trend_bias == "neutral":
    # Balanced probabilities
    base_prob = 0.50
    bull_prob = 0.25
    bear_prob = 0.25
```

### Trigger & Invalidation Generation

**Bull Scenario**:
```python
trigger = f"Hold above {value_lower} and break {resistance_lower}"
invalidation = f"Daily close below {support_lower}"
```

**Base Scenario**:
```python
trigger = f"Trade within {value_lower} - {value_upper}"
invalidation = f"Breakout above {value_upper} or below {value_lower}"
```

**Bear Scenario**:
```python
trigger = f"Break below {value_lower} with momentum"
invalidation = f"Daily close above {resistance_upper}"
```

### Validation
```python
total_prob = sum(s["probability"] for s in scenarios)
if abs(total_prob - 1.0) > 0.001:
    # Normalize
    for s in scenarios:
        s["probability"] /= total_prob
```

### Example Output
```json
[
  {
    "id": "bull_continuation_v1_d5c20017",
    "type": "bull",
    "probability": 0.675,
    "description": "Bullish continuation toward resistance structure",
    "trigger_conditions": "Hold above 1570.00 and break 1570.00",
    "invalidation_level": "Daily close below 1500.00"
  },
  {
    "id": "range_consolidation_v1_9a4cd82c",
    "type": "base",
    "probability": 0.25,
    "description": "Range-bound consolidation within value area",
    "trigger_conditions": "Trade within 1535.00 - 1570.00",
    "invalidation_level": "Breakout above 1570.00 or below 1535.00"
  },
  {
    "id": "bear_reversal_v1_c2c7cf9d",
    "type": "bear",
    "probability": 0.075,
    "description": "Bearish reversal breakdown below support",
    "trigger_conditions": "Break below 1535.00 with momentum",
    "invalidation_level": "Daily close above 1600.00"
  }
]
```

---

## 3. RISK SCORING ENGINE

### Purpose
Aggregate multiple risk factors into normalized 0-100 score.

### Location
`/app/risk_scoring/scoring.py`

### Inputs
```python
{
  "signal": SignalResponse,  # From signal engine
  "market_context": MarketContext,  # Nifty, VIX
  "rs_vs_sector": float,  # Relative strength (0.5-1.5)
  "sentiment_score": float  # -1 to +1
}
```

### Output
```python
{
  "risk_score": 0-100,  # Total
  "risk_level": "low" | "moderate" | "high",
  "trend_risk": 0-25,
  "volatility_risk": 0-20,
  "market_risk": 0-15,
  "sector_risk": 0-15,
  "conflict_risk": 0-15,
  "news_risk": 0-10,
  "conflicts": List[Dict],
  "notes": str
}
```

### Risk Component Breakdown

#### 3.1 Trend Risk (0-25)
```python
if signal.trend.strength == "weak":
    trend_risk = 25
elif signal.trend.strength == "moderate":
    trend_risk = 12
else:  # strong
    trend_risk = 0

# Additional: Sideways adds risk
if signal.trend.trend_state == "sideways":
    trend_risk = min(trend_risk + 10, 25)
```

#### 3.2 Volatility Risk (0-20)
```python
volatility_scores = {
    "low": 0,
    "normal": 5,
    "high": 15,
    "extreme": 20
}
volatility_risk = volatility_scores[signal.volatility.volatility_regime]
```

#### 3.3 Market Risk (0-15)
```python
market_risk = 0

# VIX component
if market_context.vix_regime == "panic":
    market_risk += 10
elif market_context.vix_regime == "elevated":
    market_risk += 6
elif market_context.vix_regime == "normal":
    market_risk += 2

# Market trend component
if market_context.nifty_trend == "bearish":
    market_risk = min(market_risk + 5, 15)
```

#### 3.4 Sector Risk (0-15)
```python
if rs_vs_sector < 0.8:
    sector_risk = 15  # Strong underperformance
elif rs_vs_sector < 0.9:
    sector_risk = 10  # Moderate underperformance
elif rs_vs_sector < 1.0:
    sector_risk = 5   # Slight underperformance
else:
    sector_risk = 0
```

#### 3.5 Signal Conflicts (0-15)
```python
conflicts = detect_signal_conflicts(signal)
conflict_risk = len(conflicts) * 5  # 5 points per conflict
conflict_risk = min(conflict_risk, 15)
```

#### 3.6 News/Sentiment Risk (0-10)
```python
if sentiment_score < -0.3:
    news_risk = 10  # Strongly negative
elif sentiment_score < -0.1:
    news_risk = 6   # Moderately negative
elif sentiment_score < 0.1:
    news_risk = 3   # Neutral/uncertain
else:
    news_risk = 0
```

### Risk Level Classification
```python
total_risk = (
    trend_risk +
    volatility_risk +
    market_risk +
    sector_risk +
    conflict_risk +
    news_risk
)

if total_risk <= 30:
    risk_level = "low"
elif total_risk <= 60:
    risk_level = "moderate"
else:
    risk_level = "high"
```

### Example Output
```json
{
  "risk_score": 35,
  "risk_level": "moderate",
  "trend_risk": 0,
  "volatility_risk": 15,
  "market_risk": 8,
  "sector_risk": 5,
  "conflict_risk": 5,
  "news_risk": 2,
  "conflicts": [
    {"type": "volume_divergence", "severity": "low"}
  ],
  "notes": "Moderate risk. Consider position sizing and stop-loss carefully."
}
```

---

## 4. PRICE ENGINE

### Purpose
Calculate support/resistance zones and value areas.

### Location
`/app/price_engine/ranges.py`

### Inputs
```python
{
  "df": pd.DataFrame,  # OHLCV data
  "lookback": int  # Default 50
}
```

### Outputs
```python
{
  "support": {"lower": 1500.0, "upper": 1535.0},
  "value_area": {"lower": 1535.0, "upper": 1570.0},
  "resistance": {"lower": 1570.0, "upper": 1600.0},
  "current_price": 1550.0
}
```

### Calculation Logic

#### 4.1 Support Identification
```python
# Find swing lows in recent data
swing_lows = identify_swing_lows(df, window=5)

# Cluster nearby lows
support_zone = cluster_price_levels(swing_lows, threshold=2%)

support = {
    "lower": min(support_zone),
    "upper": max(support_zone)
}
```

#### 4.2 Resistance Identification
```python
# Find swing highs
swing_highs = identify_swing_highs(df, window=5)

# Cluster
resistance_zone = cluster_price_levels(swing_highs, threshold=2%)

resistance = {
    "lower": min(resistance_zone),
    "upper": max(resistance_zone)
}
```

#### 4.3 Value Area
```python
# Price range where majority of volume occurred
value_lower = np.percentile(df['Close'], 40)
value_upper = np.percentile(df['Close'], 60)

value_area = {
    "lower": value_lower,
    "upper": value_upper
}
```

### Usage in System
- **Scenario Engine**: Triggers reference these zones
- **LLM Context**: Price bounds for narrative
- **Validation**: Ensures targets stay within bounds

---

## 5. SENTIMENT ENGINE

### Purpose
Aggregate news sentiment from multiple sources.

### Location
`/app/services/sentiment.py`

### Inputs
```python
{
  "articles": [
    {
      "title": "...",
      "content": "...",
      "source": "Economic Times",
      "published": "2024-01-15T08:00:00Z"
    },
    ...
  ]
}
```

### Outputs
```python
{
  "score": 0.35,  # -1 to +1
  "classification": "positive",
  "sentiment_count": {
    "positive": 5,
    "negative": 1,
    "neutral": 2
  },
  "average_confidence": 0.78,
  "trend": "improving"
}
```

### Sentiment Scoring

#### 5.1 Article-Level Sentiment
```python
# Using NLP model or keyword-based
sentiment_score = analyze_sentiment(article.content)
# Returns: -1 (very negative) to +1 (very positive)
```

#### 5.2 Aggregation
```python
aggregate_sentiment = {
    "score": np.mean([s["score"] for s in sentiments]),
    "classification": classify(score),
    "sentiment_count": count_by_class(sentiments)
}
```

#### 5.3 Integration with Risk Engine
```python
# From risk_scoring/scoring.py
news_risk = 0
if sentiment_score < -0.3:
    news_risk = 10  # Strongly negative
```

---

## 6. NARRATIVE VALIDATOR

### Purpose
Enforce LLM output constraints to prevent drift.

### Location
`/app/validators/narrative_validator.py`

### Inputs
```python
{
  "narrative": {
    "analysis_summary": "...",
    "analysis_text": "...",
    "prediction_summary": "...",
    "prediction_text": "..."
  },
  "structured_state": {
    "market_state": {...},
    "price_zones": {...},
    "scenarios": [...]
  }
}
```

### Output
```python
{
  "is_valid": bool,
  "errors": List[str],
  "warnings": List[str]
}
```

### Validation Rules

#### 6.1 Forbidden Terms
```python
FORBIDDEN_INDICATORS = [
    "ema", "sma", "rsi", "macd", "adx", "stochastic",
    "fibonacci", "bollinger", "ichimoku"
]

FORBIDDEN_FUNDAMENTALS = [
    "p/e", "eps", "earnings", "revenue", "profit"
]

FORBIDDEN_ADVICE = [
    "buy", "sell", "hold", "invest", "recommend"
]
```

#### 6.2 Price Zone Validation
```python
# Extract all price mentions
prices = extract_prices(narrative)

# Check against zones
for price in prices:
    if not (support.lower <= price <= resistance.upper):
        errors.append(f"Price {price} outside valid zones")
```

#### 6.3 Probability Matching
```python
# Ensure narrative mentions match scenarios
narrative_probs = extract_probabilities(narrative)
scenario_probs = [s["probability"] for s in scenarios]

if not probabilities_match(narrative_probs, scenario_probs):
    errors.append("Probability mismatch")
```

#### 6.4 Tone Matching
```python
confidence = market_state["confidence"]

if confidence < 0.5 and tone_is_decisive(narrative):
    warnings.append("High-conviction tone despite low confidence")
```

### Example Validation
```json
{
  "is_valid": false,
  "errors": [
    "Forbidden terms found: ema, rsi",
    "Price reference ₹1680 outside resistance zone (₹1600)"
  ],
  "warnings": [
    "Probability 70% mentioned, scenarios show 67.5%"
  ]
}
```

---

## 7. BACKTESTING ENGINE

### Purpose
Track scenario outcomes for performance calibration.

### Location
`/app/backtesting/snapshot.py`

### Core Functions

#### 7.1 Store Snapshot
```python
def store_snapshot(
    ticker: str,
    market_state: Dict,
    price_zones: Dict,
    scenarios: List[Dict],
    signal_conflicts: List,
    risk_score: float,
    current_price: float
) -> str:
    """
    Store complete state when scenarios generated.
    Returns snapshot_id for tracking.
    """
```

#### 7.2 Update Outcome
```python
def update_outcome(
    snapshot_id: str,
    ticker: str,
    activated_scenario_id: Optional[str],
    activation_time: str,
    max_favorable_excursion: float,
    max_adverse_excursion: float,
    final_price: float,
    days_elapsed: int
) -> bool:
    """
    Update snapshot with realized outcome.
    """
```

#### 7.3 Analyze Performance
```python
def analyze_scenario_performance(
    ticker: str,
    lookback_days: int = 30
) -> Dict:
    """
    Calculate:
    - Activation rates by scenario type
    - Prediction accuracy
    - Calibration metrics
    - Recommendations for tuning
    """
```

### Performance Metrics

```json
{
  "ticker": "RELIANCE",
  "lookback_days": 30,
  "total_snapshots": 20,
  "activation_rates": {
    "bull": 0.60,  // 60% of time bull activated
    "base": 0.30,
    "bear": 0.10
  },
  "avg_predicted_probabilities": {
    "bull": 0.65,  // Average predicted
    "base": 0.25,
    "bear": 0.10
  },
  "accuracy_by_type": {
    "bull": 0.83,  // 83% accurate when predicting bull
    "base": 0.50,
    "bear": 1.0
  },
  "overall_accuracy": 0.75,
  "recommendations": [
    "✅ Bull scenarios well-calibrated",
    "⚠️ Base scenarios over-predicting (reduce probability)",
    "✅ Bear scenarios performing well"
  ]
}
```

### Calibration Example

**Initial State**:
- Predicted bull: 65%
- Actual bull activation: 45%
- Conclusion: Over-predicting bullish outcomes

**Adjustment**:
```python
# In scenario_engine/generator.py
# Reduce bull probability from 0.675 to 0.55
# Increase base from 0.25 to 0.35
```

---

## SUMMARY

| Engine | Deterministic | Backtestable | Purpose |
|--------|--------------|--------------|---------|
| **Signal** | ✅ Yes | Indirect | Classify market state |
| **Scenario** | ✅ Yes | ✅ Yes | Generate probabilities |
| **Risk** | ✅ Yes | Indirect | Aggregate risk factors |
| **Price** | ✅ Yes | N/A | Define valid zones |
| **Sentiment** | Partial | Indirect | Quantify news impact |
| **Validator** | ✅ Yes | N/A | Enforce constraints |
| **Backtesting** | N/A | ✅ Yes | Track & calibrate |

**All engines work together to create a market-grade system that is repeatable, explainable, and continuously improving.**
