"""
Pydantic schemas for user authentication and authorization
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re
import html


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr


class UserCreate(BaseModel):
    """Schema for user registration"""
    email: str  # Changed from EmailStr to allow encrypted values
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: Optional[str] = None
    
    # Encryption support flags
    email_encrypted: Optional[bool] = False
    password_encrypted: Optional[bool] = False
    full_name_encrypted: Optional[bool] = False
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str, info) -> str:
        """Validate email only if not encrypted"""
        # Skip validation if encrypted (encrypted emails are base64 and long)
        if len(v) > 50:  # Encrypted values are much longer
            return v
        
        # Validate as email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        
        # Additional SQL injection check
        if "'" in v or '"' in v or ';' in v or '--' in v:
            raise ValueError('Invalid email format')
        
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Enforce strong password requirements (only for unencrypted passwords)"""
        # Skip validation if password looks encrypted (base64-like)
        if len(v) > 50:  # Encrypted passwords are much longer
            return v
        
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v
    
    @field_validator('full_name')
    @classmethod
    def sanitize_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize full_name to prevent XSS"""
        if v:
            # HTML escape to prevent XSS
            return html.escape(v.strip())
        return v
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Additional email validation to prevent SQL injection attempts"""
        # EmailStr already validates format, but add extra check
        if "'" in v or '"' in v or ';' in v or '--' in v:
            raise ValueError('Invalid email format')
        return v.lower()


class UserLogin(BaseModel):
    """Schema for user login"""
    email: str  # Changed from EmailStr to allow encrypted values
    password: str
    
    # Encryption support flags
    email_encrypted: Optional[bool] = False
    password_encrypted: Optional[bool] = False
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate email only if not encrypted"""
        # Skip validation if encrypted
        if len(v) > 50:
            return v
        
        # Simple email validation
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        
        return v.lower()


class UserResponse(BaseModel):
    """Schema for user response (no sensitive data)"""
    id: int
    email: str
    role: str
    is_verified: bool
    is_active: bool
    full_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: int  # user_id
    role: str
    exp: Optional[int] = None
    type: str = "access"  # access or refresh


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request"""
    refresh_token: str


class PasswordChange(BaseModel):
    """Schema for password change"""
    old_password: str
    new_password: str = Field(..., min_length=8)
