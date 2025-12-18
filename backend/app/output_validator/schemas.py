"""
Validation Schemas
"""

from pydantic import BaseModel
from typing import List


class ValidationError(BaseModel):
    """Single validation error"""
    error_type: str
    message: str
    severity: str  # "error" | "warning"


class ValidationResult(BaseModel):
    """Result of validation"""
    is_valid: bool
    errors: List[ValidationError] = []
    warnings: List[ValidationError] = []
    validated_output: dict = {}
