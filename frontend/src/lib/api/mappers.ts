/**
 * API Response Mappers
 * Extracts market-grade v2 data from existing backend response
 */

export interface MarketState {
    trend_bias: 'bullish' | 'neutral' | 'bearish';
    confidence: number;
    momentum?: string;
    volatility?: string;
}

export interface PriceZones {
    support: { lower: number; upper: number };
    value_area: { lower: number; upper: number };
    resistance: { lower: number; upper: number };
    current_price: number;
}

export interface Scenario {
    id: string;
    type: 'bull' | 'base' | 'bear';
    probability: number;
    description: string;
    trigger_conditions?: string;
    invalidation_level?: string;
    target_zone?: string;
}

export interface RiskAssessment {
    risk_score: number;
    risk_level: 'low' | 'moderate' | 'high';
    [key: string]: any;
}

export interface AnalysisV2Data {
    // Core fields
    ticker: string;
    price: number;
    sentiment: string;
    confidence: number;

    // Market-grade fields
    market_state: MarketState;
    price_zones: PriceZones;
    scenarios: Scenario[];
    risk_assessment: RiskAssessment;

    // Narrative
    narrative: {
        analysis_summary?: string;
        analysis_text: string;
        prediction_summary?: string;
        prediction_text: string;
    };

    // Legacy fields (for backward compat)
    historicalDataMulti?: any;
    dayLow?: number;
    dayHigh?: number;
    currency?: string;
    rsi?: number;
    macd?: { macd: number; signal: number; histogram: number };
    sma?: { 50: number; 200: number };
    insights?: string[];
    risks?: string[];
    references?: any[];
}

/**
 * Map raw backend response to v2 structure
 * Handles missing fields with intelligent fallbacks
 */
export function mapAnalysisToV2(rawData: any): AnalysisV2Data {
    return {
        // Core fields
        ticker: rawData.ticker || '',
        price: rawData.current_price || 0,
        sentiment: rawData.sentiment?.classification || 'Neutral',
        confidence: ((rawData.sentiment?.average_confidence || rawData.sentiment?.confidence || 0) * 100),

        // Market State
        market_state: rawData.market_state || {
            trend_bias: deriveTrendBias(rawData),
            confidence: rawData.confidence || 0,
            momentum: rawData.momentum || 'unknown',
            volatility: rawData.volatility || 'unknown'
        },

        // Price Zones
        price_zones: rawData.price_zones || {
            support: { lower: 0, upper: 0 },
            value_area: { lower: 0, upper: 0 },
            resistance: { lower: 0, upper: 0 },
            current_price: rawData.current_price || 0
        },

        // Scenarios
        scenarios: Array.isArray(rawData.scenarios) ? rawData.scenarios : [],

        // Risk Assessment
        risk_assessment: rawData.risk_assessment || {
            risk_score: 0,
            risk_level: 'unknown'
        },

        // Narrative
        narrative: {
            analysis_summary: rawData.analysis_structured?.summary || '',
            analysis_text: rawData.analysis_structured?.full_text || rawData.analysis || '',
            prediction_summary: rawData.prediction_structured?.summary || '',
            prediction_text: rawData.prediction_structured?.outlook || rawData.prediction || ''
        },

        // Legacy fields
        historicalDataMulti: rawData.historical_data_multi || {},
        dayLow: rawData.day_low || 0,
        dayHigh: rawData.day_high || 0,
        currency: rawData.currency || 'INR',
        rsi: rawData.technical_analysis?.indicators?.rsi?.value || 0,
        macd: rawData.technical_analysis?.indicators?.macd ? {
            macd: rawData.technical_analysis.indicators.macd.macd || 0,
            signal: rawData.technical_analysis.indicators.macd.signal || 0,
            histogram: rawData.technical_analysis.indicators.macd.histogram || 0
        } : undefined,
        sma: rawData.technical_analysis?.indicators?.sma ? {
            50: rawData.technical_analysis.indicators.sma['50'] || 0,
            200: rawData.technical_analysis.indicators.sma['200'] || 0
        } : undefined,
        insights: rawData.key_insights || [],
        risks: rawData.risk_factors || [],
        references: rawData.references || []
    };
}

/**
 * Derive trend bias from sentiment if market_state not available
 */
function deriveTrendBias(data: any): 'bullish' | 'neutral' | 'bearish' {
    const sentiment = data.sentiment?.classification?.toLowerCase();

    if (sentiment === 'bullish' || sentiment === 'positive') {
        return 'bullish';
    }

    if (sentiment === 'bearish' || sentiment === 'negative') {
        return 'bearish';
    }

    return 'neutral';
}

/**
 * Validate that scenarios probabilities sum to ~1.0
 */
export function validateScenarios(scenarios: Scenario[]): boolean {
    if (!scenarios || scenarios.length === 0) return false;

    const totalProb = scenarios.reduce((sum, s) => sum + s.probability, 0);
    return Math.abs(totalProb - 1.0) < 0.01; // Allow 1% tolerance
}

/**
 * Get primary scenario (highest probability)
 */
export function getPrimaryScenario(scenarios: Scenario[]): Scenario | null {
    if (!scenarios || scenarios.length === 0) return null;
    return scenarios.reduce((max, s) => s.probability > max.probability ? s : max, scenarios[0]);
}
