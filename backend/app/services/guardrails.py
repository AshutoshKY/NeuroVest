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
            logger.warning("⚠️  Guardrails violations detected", extra={
                "operation": "guardrails_validate",
                "violations_count": len(violations),
                "violations": violations,
                "replacements_made": replacements_made,
                "status": "violations_found"
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
        Process AI analysis output through guardrails.
        
        Args:
            analysis: Analysis dictionary from RAG/LLM
            
        Returns:
            Processed analysis with disclaimer and validation
        """
        logger.info("🛡️  Processing analysis through guardrails", extra={
            "operation": "guardrails_process",
            "has_analysis": "analysis" in analysis,
            "has_reasoning": "reasoning" in analysis,
            "has_summary": "summary" in analysis
        })
        
        total_violations = 0
        
        # Validate main analysis text if present
        if "analysis" in analysis:
            validation = self.validate_output(analysis["analysis"])
            
            # Use sanitized text
            analysis["analysis"] = validation["sanitized_text"]
            
            # Add disclaimer
            analysis["analysis"] = self.add_disclaimer(analysis["analysis"])
            
            # Add compliance metadata
            analysis["compliance"] = {
                "validated": True,
                "has_violations": not validation["is_valid"],
                "violations": validation["violations"] if not validation["is_valid"] else []
            }
            
            total_violations += len(validation.get("violations", []))
        
        # Validate reasoning if present
        if "reasoning" in analysis:
            validation = self.validate_output(analysis["reasoning"])
            analysis["reasoning"] = validation["sanitized_text"]
            total_violations += len(validation.get("violations", []))
        
        # Add disclaimer to summary if present
        if "summary" in analysis:
            validation = self.validate_output(analysis["summary"])
            analysis["summary"] = validation["sanitized_text"]
            total_violations += len(validation.get("violations", []))
        
        # Ensure disclaimer is always present
        analysis["disclaimer"] = DISCLAIMER
        
        logger.info("✅ Guardrails processing complete", extra={
            "operation": "guardrails_process",
            "total_violations": total_violations,
            "sanitized": total_violations > 0,
            "disclaimer_added": True,
            "status": "success"
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
