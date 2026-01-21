"""
Citation Validator - Layer 2 of Anti-Hallucination System

CRITICAL: Validates that every signal has a verifiable citation from source text.
This is the MOST IMPORTANT layer for preventing hallucinations.
"""

import re
from difflib import SequenceMatcher
from typing import Tuple, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_utils import normalize_text, extract_numbers


class CitationValidator:
    """
    Validates that citations (verbatim quotes) actually exist in source texts.
    
    This is the PRIMARY defense against LLM hallucinations.
    """
    
    def __init__(self, sources: list[dict], fuzzy_threshold: float = 0.85):
        """
        Initialize validator with sources.
        
        Args:
            sources: List of source dicts with 'url' and 'raw_text' keys
            fuzzy_threshold: Similarity threshold for fuzzy matching (0.0-1.0)
        """
        self.sources = sources
        self.fuzzy_threshold = fuzzy_threshold
        
        # Build URL -> text mapping
        self.source_texts = {}
        for source in sources:
            url = source.get('url')
            text = source.get('raw_text', '') or source.get('text', '')
            if url and text:
                self.source_texts[url] = text
        
        # Statistics
        self.stats = {
            'total_validated': 0,
            'accepted': 0,
            'rejected': 0,
            'rejection_reasons': {}
        }
    
    # ==========================================================================
    # PUBLIC API
    # ==========================================================================
    
    def validate_signal(self, signal: dict) -> Tuple[bool, str]:
        """
        Validate a single signal's citation.
        
        Args:
            signal: Signal dict with verbatim_quote, source_url, value, etc.
        
        Returns:
            (is_valid, error_message)
            - is_valid: True if citation is valid
            - error_message: Empty string if valid, error description if not
        """
        self.stats['total_validated'] += 1
        
        # Rule 1: Citation must exist
        verbatim = signal.get('verbatim_quote', '').strip()
        if not verbatim:
            return self._reject("Missing verbatim_quote")
        
        if len(verbatim) < 20:
            return self._reject(f"verbatim_quote too short ({len(verbatim)} chars, min 20)")
        
        # Rule 2: Source URL must be referenced
        source_url = signal.get('source_url', '').strip()
        if not source_url:
            return self._reject("Missing source_url")
        
        # Rule 3: Source must be in our database
        if source_url not in self.source_texts:
            return self._reject(f"Unknown source_url: {source_url}")
        
        # Rule 4: Quote must exist in source text (fuzzy matching)
        source_text = self.source_texts[source_url]
        if not self._fuzzy_contains(source_text, verbatim):
            return self._reject(
                f"Quote not found in source: '{verbatim[:50]}...'"
            )
        
        # Rule 5: Validate numeric claims
        value_data = signal.get('value', {})
        if isinstance(value_data, dict) and 'numeric_value' in value_data:
            numeric_value = value_data['numeric_value']
            if numeric_value is not None:
                if not self._validate_number_in_text(verbatim, numeric_value):
                    return self._reject(
                        f"Numeric value {numeric_value} not found in quote"
                    )
        
        # All checks passed!
        self.stats['accepted'] += 1
        return True, ""
    
    def validate_all_signals(self, signals: list[dict]) -> list[dict]:
        """
        Validate all signals and return only valid ones.
        
        Args:
            signals: List of signal dicts
        
        Returns:
            List of valid signals (rejected ones are filtered out)
        """
        valid_signals = []
        
        for signal in signals:
            is_valid, error = self.validate_signal(signal)
            
            if is_valid:
                signal['validation_status'] = 'verified'
                valid_signals.append(signal)
            else:
                signal['validation_status'] = 'rejected'
                signal['rejection_reason'] = error
                
                # Log rejection
                print(f"⚠️  REJECTED SIGNAL: {error}")
                headline = signal.get('value', {}).get('headline', '(no headline)')
                print(f"   Headline: {headline}")
        
        return valid_signals
    
    def get_stats(self) -> dict:
        """Get validation statistics."""
        stats = self.stats.copy()
        if stats['total_validated'] > 0:
            stats['acceptance_rate'] = stats['accepted'] / stats['total_validated']
        else:
            stats['acceptance_rate'] = 0.0
        return stats
    
    # ==========================================================================
    # VALIDATION HELPERS
    # ==========================================================================
    
    def _fuzzy_contains(self, text: str, quote: str) -> bool:
        """
        Check if quote exists in text with fuzzy matching.
        
        Allows minor differences (typos, punctuation variations).
        """
        if not text or not quote:
            return False
        
        # Normalize both
        text_norm = normalize_text(text)
        quote_norm = normalize_text(quote)
        
        # Fast path: Direct substring match
        if quote_norm in text_norm:
            return True
        
        # Fuzzy matching: Sliding window
        quote_len = len(quote_norm)
        text_len = len(text_norm)
        
        if quote_len > text_len:
            return False
        
        # Try sliding window with fuzzy matching
        max_similarity = 0.0
        step = max(1, quote_len // 10)  # Don't check every position (too slow)
        
        for i in range(0, text_len - quote_len + 1, step):
            window = text_norm[i:i + quote_len]
            similarity = SequenceMatcher(None, window, quote_norm).ratio()
            max_similarity = max(max_similarity, similarity)
            
            if similarity >= self.fuzzy_threshold:
                return True
        
        # If we got close (80%), do a more thorough search
        if max_similarity >= 0.80:
            for i in range(0, text_len - quote_len + 1):
                window = text_norm[i:i + quote_len]
                similarity = SequenceMatcher(None, window, quote_norm).ratio()
                if similarity >= self.fuzzy_threshold:
                    return True
        
        return False
    
    def _validate_number_in_text(self, text: str, number: float, tolerance: float = 0.01) -> bool:
        """
        Validate that a specific number appears in the text.
        
        Args:
            text: Text to search in
            number: Number to find
            tolerance: Relative tolerance (0.01 = 1%)
        
        Returns:
            True if number found, False otherwise
        """
        numbers = extract_numbers(text)
        
        for num in numbers:
            # Relative difference
            if abs(number) < 1e-10:  # Avoid division by zero
                if abs(num - number) < 0.01:
                    return True
            else:
                relative_diff = abs(num - number) / abs(number)
                if relative_diff <= tolerance:
                    return True
        
        return False
    
    def _reject(self, reason: str) -> Tuple[bool, str]:
        """Helper to reject a signal with a reason."""
        self.stats['rejected'] += 1
        
        # Track rejection reasons
        if reason not in self.stats['rejection_reasons']:
            self.stats['rejection_reasons'][reason] = 0
        self.stats['rejection_reasons'][reason] += 1
        
        return False, reason


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def validate_citations(signals: list[dict], sources: list[dict]) -> list[dict]:
    """
    Convenience function: Validate citations for all signals.
    
    Args:
        signals: List of signal dicts
        sources: List of source dicts
    
    Returns:
        List of valid signals (rejected ones filtered out)
    """
    validator = CitationValidator(sources)
    return validator.validate_all_signals(signals)
