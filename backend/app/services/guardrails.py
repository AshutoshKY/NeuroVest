import re
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

# Forbidden words and phrases that constitute financial advice
FORBIDDEN_PHRASES = [
    "buy", "sell", "purchase", "invest in", "should buy", "should sell",
    "recommend buying", "recommend selling", "advice", "advise",
    "you should", "we recommend", "strong buy", "strong sell",
    "time to buy", "time to sell", "great opportunity to buy"
]

# Allowed informational phrases
ALLOWED_ALTERNATIVES = {
    "buy": "acquire",
    "sell": "divest",
    "you should": "one might consider",
    "we recommend": "the data suggests",
    "strong buy": "strong positive indicators",
    "strong sell": "strong negative indicators"
}

# Compliance disclaimer
DISCLAIMER = """
⚠️ **IMPORTANT DISCLAIMER**

This analysis is provided for **informational and educational purposes only**. It does not constitute financial advice, investment recommendations, or an offer to buy or sell any securities.

**Key Points:**
- This is AI-generated analysis based on publicly available information
- Past performance does not guarantee future results
- Market data and sentiment can change rapidly
- Always conduct your own research and consult with a qualified financial advisor
- Investment decisions should be based on your individual financial situation, goals, and risk tolerance

**Risk Warning:** Trading and investing in securities involves substantial risk of loss. You may lose some or all of your investment.
"""


class GuardrailsService:
    """Service for ensuring compliance and preventing financial advice."""
    
    def __init__(self):
        """Initialize guardrails service."""
        self.forbidden_pattern = self._compile_forbidden_pattern()
    
    def _compile_forbidden_pattern(self) -> re.Pattern:
        """Compile regex pattern for forbidden phrases."""
        # Create case-insensitive pattern
        pattern = "|".join(re.escape(phrase) for phrase in FORBIDDEN_PHRASES)
        return re.compile(pattern, re.IGNORECASE)
    
    def validate_output(self, text: str) -> Dict[str, Any]:
        """
        Validate output text for compliance.
        
        Args:
            text: Text to validate
            
        Returns:
            Dict with is_valid (bool), violations (list), and sanitized_text
        """
        violations = []
        
        logger.debug("🛡️  Validating text with guardrails", extra={
            "operation": "guardrails_validate",
            "text_length": len(text)
        })
        
        # Check for forbidden phrases
        matches = self.forbidden_pattern.findall(text)
        if matches:
            violations.extend([f"Contains forbidden phrase: '{match}'" for match in set(matches)])
        
        # Sanitize text by replacing forbidden phrases
        sanitized_text = text
        replacements_made = 0
        for forbidden, alternative in ALLOWED_ALTERNATIVES.items():
            before = sanitized_text
            sanitized_text = re.sub(
                r'\b' + re.escape(forbidden) + r'\b',
                alternative,
                sanitized_text,
                flags=re.IGNORECASE
            )
            if before != sanitized_text:
                replacements_made += 1
        
        is_valid = len(violations) == 0
        
        result = {
            "is_valid": is_valid,
            "violations": violations,
            "sanitized_text": sanitized_text,
            "original_text": text
        }
        
        
        if violations:
            # NEW: Enhanced logging with exact context
            logger.warning("⚠️  Guardrails violations detected", extra={
                "operation": "guardrails_validate",
                "violations_count": len(violations),
                "violations": violations,
                "flagged_words": list(set(matches)),  # Exact words flagged
                "replacements_made": replacements_made,
                "status": "violations_found"
            })
            
            # NEW: Log detailed context around each violation
            for idx, violation in enumerate(violations, 1):
                # Find the word in the original text and show context
                for match in matches:
                    # Find position of match in text
                    match_pos = text.lower().find(match.lower())
                    if match_pos != -1:
                        # Get 50 chars before and after for context
                        start_pos = max(0, match_pos - 50)
                        end_pos = min(len(text), match_pos + len(match) + 50)
                        context = text[start_pos:end_pos]
                        
                        logger.warning(f"🚫 Violation {idx} context: '{match}'", extra={
                            "operation": "guardrails_violation_detail",
                            "violation_num": idx,
                           "flagged_word": match,
                            "context_text": f"...{context}...",
                            "position": match_pos
                        })
        else:
            logger.debug("✅ Guardrails validation passed", extra={
                "operation": "guardrails_validate",
                "status": "clean"
            })
        
        return result
    
    
    def add_disclaimer(self, text: str) -> str:
        """Add disclaimer to analysis output."""
        return f"{text}\n\n{DISCLAIMER}\n"
    
    
    def process_analysis(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process analysis through guardrails and add disclaimer.
        Handles both flat and nested (structured) formats.
        
        Args:
            analysis: Analysis dictionary (can be flat or nested)
            
        Returns:
            Processed analysis with guardrails applied
        """
        logger.info("🛡️  Processing analysis through guardrails", extra={
            "operation": "guardrails_process"
        })
        
        try:
            total_violations = 0
            
            # Handle nested structure (new format)
            if isinstance(analysis.get('analysis'), dict):
                # Validate nested analysis text
                analysis_full_text = analysis['analysis'].get('full_text', '')
                if analysis_full_text:
                    result = self.validate_output(analysis_full_text)
                    analysis['analysis']['full_text'] = result['sanitized_text']
                    total_violations += len(result.get('violations', []))
                
                # Validate analysis key points
                key_points = analysis['analysis'].get('key_points', [])
                sanitized_points = []
                for point in key_points:
                    result = self.validate_output(point)
                    sanitized_points.append(result['sanitized_text'])
                    total_violations += len(result.get('violations', []))
                analysis['analysis']['key_points'] = sanitized_points
            elif 'analysis' in analysis and isinstance(analysis['analysis'], str):
                # Fallback: flat format
                result = self.validate_output(analysis['analysis'])
                analysis['analysis'] = result['sanitized_text']
                total_violations += len(result.get('violations', []))
            
            # Handle nested prediction (new format)
            if isinstance(analysis.get('prediction'), dict):
                # Validate prediction outlook
                outlook = analysis['prediction'].get('outlook', '')
                if outlook:
                    result = self.validate_output(outlook)
                    analysis['prediction']['outlook'] = result['sanitized_text']
                    total_violations += len(result.get('violations', []))
                
                # Validate scenarios
                scenarios = analysis['prediction'].get('scenarios', {})
                for scenario_key in ['bull', 'base', 'bear']:
                    if scenario_key in scenarios:
                        result = self.validate_output(scenarios[scenario_key])
                        scenarios[scenario_key] = result['sanitized_text']
                        total_violations += len(result.get('violations', []))
            elif 'prediction' in analysis and isinstance(analysis['prediction'], str):
                # Fallback: flat format
                result = self.validate_output(analysis['prediction'])
                analysis['prediction'] = result['sanitized_text']
                total_violations += len(result.get('violations', []))
            
            # Validate other text fields
            if 'reasoning' in analysis:
                result = self.validate_output(analysis['reasoning'])
                analysis['reasoning'] = result['sanitized_text']
                total_violations += len(result.get('violations', []))
            
            # Validate risk factors
            if 'risk_factors' in analysis and isinstance(analysis['risk_factors'], list):
                sanitized_risks = []
                for risk in analysis['risk_factors']:
                    result = self.validate_output(risk)
                    sanitized_risks.append(result['sanitized_text'])
                    total_violations += len(result.get('violations', []))
                analysis['risk_factors'] = sanitized_risks
            
            # Validate key insights
            if 'key_insights' in analysis and isinstance(analysis['key_insights'], list):
                sanitized_insights = []
                for insight in analysis['key_insights']:
                    result = self.validate_output(insight)
                    sanitized_insights.append(result['sanitized_text'])
                    total_violations += len(result.get('violations', []))
                analysis['key_insights'] = sanitized_insights
            
            # Add compliance metadata
            analysis['compliance'] = {
                'validated': True,
                'total_violations': total_violations,
                'sanitized': total_violations > 0
            }
            
            logger.info("✅ Guardrails processing complete", extra={
                "operation": "guardrails_process",
                "total_violations": total_violations,
                "status": "success"
            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error in guardrails processing: {e}", extra={
                "operation": "guardrails_process",
                "error": str(e)
            })
            return analysis
    
    def log_output(self, user_id: int, output: str, endpoint: str):
        """
        Log output for compliance audit trail.
        
        Args:
            user_id: User ID who requested the analysis
            output: The output text
            endpoint: API endpoint that generated the output
        """
        # In production, this would write to a compliance logging system
        logger.info(
            f"Compliance Log - User: {user_id}, Endpoint: {endpoint}, "
            f"Output Length: {len(output)}"
        )


# Global instance
guardrails_service = GuardrailsService()
