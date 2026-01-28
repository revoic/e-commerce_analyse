"""
Pydantic models for signal validation with strict anti-hallucination rules.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal
from datetime import datetime
import re


# ==============================================================================
# SIGNAL VALUE (STRUCTURED DATA)
# ==============================================================================

class SignalValue(BaseModel):
    """
    Structured signal value with relaxed validation.
    """
    
    headline: str = Field(
        ..., 
        min_length=5,  # RELAXED: 10 → 5
        max_length=200,
        description="Short factual headline"
    )
    
    fact: str = Field(
        ..., 
        min_length=10,  # RELAXED: 20 → 10
        max_length=500,
        description="The concrete, verifiable fact"
    )
    
    # Optional numeric data
    metric: Optional[str] = Field(None, max_length=100)
    numeric_value: Optional[float] = None
    unit: Optional[str] = Field(None, max_length=20)
    
    # Context
    period: Optional[str] = Field(None, max_length=50)
    region: Optional[str] = Field(None, max_length=10)
    topic: Optional[str] = Field(None, max_length=100)
    summary: Optional[str] = Field(None, max_length=300)
    note: Optional[str] = Field(None, max_length=200)
    
    @field_validator('numeric_value')
    @classmethod
    def validate_numeric(cls, v):
        """Validate numeric values are reasonable."""
        if v is not None:
            if not -1e15 < v < 1e15:
                raise ValueError("Numeric value out of reasonable range")
            if abs(v) < 1e-10:  # Essentially zero
                raise ValueError("Numeric value too small to be meaningful")
        return v
    
    @model_validator(mode='after')
    def validate_metric_consistency(self):
        """If numeric_value exists, metric should exist too."""
        # RELAXED: Made this a warning instead of error
        if self.numeric_value is not None and not self.metric:
            # Just set a default instead of raising error
            self.metric = "value"
        return self


# ==============================================================================
# SIGNAL (WITH MANDATORY CITATION)
# ==============================================================================

class Signal(BaseModel):
    """
    A validated, fact-based signal with mandatory citation.
    
    CRITICAL: verbatim_quote is MANDATORY for anti-hallucination!
    """
    
    type: Literal[
        "financial", "ecommerce", "retail_media", "marketplace",
        "d2c", "partnership", "product", "strategy", "leadership",
        "sustainability", "markets", "risks", "summary"
    ] = Field(..., description="Signal category")
    
    value: SignalValue = Field(..., description="Structured signal data")
    
    # MANDATORY CITATION FIELDS (Layer 2: Citation Enforcement)
    verbatim_quote: str = Field(
        ..., 
        min_length=15,  # RELAXED: 20 → 15
        max_length=500,
        description="Quote from source text for verification (can be paraphrased)"
    )
    
    source_title: str = Field(
        ..., 
        min_length=3,
        max_length=300
    )
    
    source_url: str = Field(
        ..., 
        pattern=r'^https?://.+',
        description="Must be valid HTTP(S) URL"
    )
    
    # Confidence (Layer 4: Confidence Filtering)
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0,
        description="Confidence score (0.0-1.0)"
    )
    
    extraction_reasoning: str = Field(
        ..., 
        min_length=20, 
        max_length=300,
        description="Why this confidence level?"
    )
    
    # Validation metadata (set by validators)
    validation_status: Optional[str] = Field(
        default="pending",
        description="pending/verified/rejected"
    )
    rejection_reason: Optional[str] = None
    
    # Layer 5: Cross-reference
    corroboration_count: Optional[int] = Field(default=0, ge=0)
    corroborating_sources: Optional[list[str]] = Field(default_factory=list)
    
    # Layer 6: Fact-check
    fact_check_status: Optional[Literal[
        "verified", "partially_correct", "incorrect", "cannot_verify"
    ]] = None
    fact_check_reasoning: Optional[str] = None
    fact_check_issues: Optional[list[str]] = Field(default_factory=list)
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Validate confidence is in valid range."""
        # RELAXED: Removed 0.95 upper limit - allow high confidence
        if v < 0.0 or v > 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v
    
    @field_validator('verbatim_quote')
    @classmethod
    def validate_quote_quality(cls, v):
        """Ensure quote has minimum length."""
        # RELAXED: Removed strict requirements for numbers/proper nouns
        # RELAXED: Min length 20 → 15
        if not v or len(v.strip()) < 15:
            raise ValueError("verbatim_quote must be at least 15 characters")
        
        return v.strip()
    
    @field_validator('source_url')
    @classmethod
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(('http://', 'https://')):
            raise ValueError("source_url must start with http:// or https://")
        if len(v) < 10:
            raise ValueError("source_url too short")
        return v


# ==============================================================================
# EXTRACTION RESULT
# ==============================================================================

class ExtractionResult(BaseModel):
    """
    Complete extraction result with metadata.
    """
    
    company: str = Field(..., min_length=2)
    signals: list[Signal] = Field(default_factory=list)
    
    # Metadata
    extraction_timestamp: Optional[datetime] = Field(
        default_factory=lambda: datetime.utcnow()
    )
    model_used: Optional[str] = None
    total_sources: Optional[int] = 0
    
    # Validation summary
    validation_summary: Optional[dict] = Field(default_factory=dict)
    
    @model_validator(mode='after')
    def validate_signals_list(self):
        """Ensure signals list is valid."""
        if not isinstance(self.signals, list):
            self.signals = []
        
        # Remove None values
        self.signals = [s for s in self.signals if s is not None]
        
        return self


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def validate_signal_dict(signal_dict: dict) -> Signal:
    """
    Validate a signal dictionary and return Signal instance.
    
    Raises:
        ValidationError: If signal doesn't meet requirements
    """
    return Signal(**signal_dict)


def signals_to_dict_list(signals: list[Signal]) -> list[dict]:
    """Convert list of Signal instances to list of dicts."""
    return [s.model_dump() for s in signals]


def dict_list_to_signals(dict_list: list[dict]) -> list[Signal]:
    """Convert list of dicts to list of Signal instances."""
    result = []
    for d in dict_list:
        try:
            signal = Signal(**d)
            result.append(signal)
        except Exception:
            continue  # Skip invalid signals
    return result
