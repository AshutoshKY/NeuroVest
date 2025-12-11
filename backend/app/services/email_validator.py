"""
Email validation service
Validates email domains and blocks temporary email providers
"""
from typing import Set
from loguru import logger


class EmailValidator:
    """Email domain validation"""
    
    # Allowed major email providers
    ALLOWED_DOMAINS: Set[str] = {
        # Google
        "gmail.com", "googlemail.com",
        # Microsoft
        "outlook.com", "hotmail.com", "live.com", "msn.com",
        # Yahoo
        "yahoo.com", "yahoo.co.uk", "yahoo.co.in", "ymail.com",
        # Apple
        "icloud.com", "me.com", "mac.com",
        # Privacy-focused
        "protonmail.com", "proton.me", "pm.me",
        # Other major providers
        "aol.com", "zoho.com", "mail.com",
        # Corporate (can be expanded)
        "company.com",  # Placeholder for corporate domains
    }
    
    # Known temporary/disposable email domains
    BLOCKED_DOMAINS: Set[str] = {
        "tempmail.com", "temp-mail.org", "guerrillamail.com",
        "10minutemail.com", "throwaway.email", "mailinator.com",
        "maildrop.cc", "trashmail.com", "fakeinbox.com",
        "yopmail.com", "getnada.com", "emailondeck.com",
        "temp-mail.io", "mohmal.com", "throwaway.email",
        "dispostable.com", "mintemail.com", "mytemp.email",
        "sharklasers.com", "guerrillamail.info", "grr.la",
        "spam4.me", "discard.email", "fakemail.net",
        "tempail.com", "throwawayemail.com", "mailnesia.com",
        "anonbox.net", "anonymousemail.me", "burnermail.io",
        "duck.com", "bugmenot.com", "dodgeit.com",
        "emailtemporario.com.br", "emailtemporanea.com",
        "gmail.com.co", "gmail.com.br"  # Fake Gmail variants
    }
    
    @staticmethod
    def is_valid_domain(email: str) -> bool:
        """
        Check if email domain is allowed
        
        Args:
            email: Email address to validate
            
        Returns:
            True if domain is allowed, False otherwise
        """
        try:
            domain = email.lower().split('@')[1]
        except IndexError:
            logger.warning(f"[EMAIL_VALIDATOR] Invalid email format: {email}")
            return False
        
        # Check if blocked
        if domain in EmailValidator.BLOCKED_DOMAINS:
            logger.warning(f"[EMAIL_VALIDATOR] Blocked temporary email domain: {domain}")
            return False
        
        # Check if allowed
        if domain not in EmailValidator.ALLOWED_DOMAINS:
            # Allow if it looks like a corporate domain (has company name)
            # This is a simple heuristic - you can make it more sophisticated
            if '.' in domain and not any(x in domain for x in ['temp', 'fake', 'disposable', 'trash']):
                logger.info(f"[EMAIL_VALIDATOR] Allowing potential corporate domain: {domain}")
                return True
            
            logger.warning(f"[EMAIL_VALIDATOR] Domain not in allowed list: {domain}")
            return False
        
        logger.info(f"[EMAIL_VALIDATOR] Valid email domain: {domain}")
        return True
    
    @staticmethod
    def get_domain(email: str) -> str:
        """Extract domain from email"""
        try:
            return email.lower().split('@')[1]
        except IndexError:
            return ""
    
    @staticmethod
    def is_corporate_email(email: str) -> bool:
        """Check if email appears to be from a corporate domain"""
        domain = EmailValidator.get_domain(email)
        
        # Not a corporate email if it's a consumer email provider
        public_providers = {
            "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
            "icloud.com", "aol.com", "protonmail.com"
        }
        
        return domain not in public_providers and '.' in domain


# Singleton instance
_email_validator = EmailValidator()


def get_email_validator() -> EmailValidator:
    """Get email validator instance"""
    return _email_validator
