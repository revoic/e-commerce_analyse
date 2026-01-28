"""
Confidence Filter - Layer 4 of Anti-Hallucination System

Multi-tier confidence filtering with badges for UI display.
"""

class ConfidenceFilter:
    """
    Multi-tier confidence filtering system.
    
    Thresholds (RELAXED):
    - Verified: >= 0.90
    - High: >= 0.75
    - Medium: >= 0.60
    - Low: >= 0.40 (still included!)
    - Excluded: < 0.40
    """
    
    # Confidence thresholds (RELAXED)
    THRESHOLD_VERIFIED = 0.90
    THRESHOLD_HIGH = 0.75      # Was 0.80
    THRESHOLD_MEDIUM = 0.60    # Was 0.70
    THRESHOLD_INCLUDE = 0.40   # Was 0.70 - NOW MUCH LOWER!
    
    def __init__(self, min_confidence: float = THRESHOLD_INCLUDE):
        """
        Initialize filter.
        
        Args:
            min_confidence: Minimum confidence to include (default: 0.40 - RELAXED)
        """
        self.min_confidence = min_confidence
        
        # Statistics
        self.stats = {
            'total': 0,
            'verified': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'excluded': 0
        }
    
    def filter_signals(self, signals: list[dict]) -> dict:
        """
        Categorize signals by confidence level.
        
        Args:
            signals: List of signal dicts
        
        Returns:
            Dict with keys: verified, high, medium, low, excluded
        """
        result = {
            'verified': [],  # >= 0.90
            'high': [],      # >= 0.75
            'medium': [],    # >= 0.60
            'low': [],       # >= 0.40 (still included!)
            'excluded': []   # < 0.40
        }
        
        for signal in signals:
            self.stats['total'] += 1
            conf = signal.get('confidence', 0.0)
            
            if conf >= self.THRESHOLD_VERIFIED:
                result['verified'].append(signal)
                self.stats['verified'] += 1
            elif conf >= self.THRESHOLD_HIGH:
                result['high'].append(signal)
                self.stats['high'] += 1
            elif conf >= self.THRESHOLD_MEDIUM:
                result['medium'].append(signal)
                self.stats['medium'] += 1
            elif conf >= self.THRESHOLD_INCLUDE:
                result['low'].append(signal)
                self.stats['low'] += 1
            else:
                result['excluded'].append(signal)
                self.stats['excluded'] += 1
        
        return result
    
    def get_report_signals(self, signals: list[dict]) -> list[dict]:
        """
        Get signals suitable for reporting (>= min_confidence).
        Adds confidence badges for UI display.
        
        Args:
            signals: List of signal dicts
        
        Returns:
            List of signals with confidence_badge added
        """
        categorized = self.filter_signals(signals)
        
        report_signals = []
        
        # Verified signals
        for signal in categorized['verified']:
            signal['confidence_badge'] = '🟢 Verified'
            signal['confidence_tier'] = 'verified'
            report_signals.append(signal)
        
        # High confidence
        for signal in categorized['high']:
            signal['confidence_badge'] = '🟡 High Confidence'
            signal['confidence_tier'] = 'high'
            report_signals.append(signal)
        
        # Medium confidence
        for signal in categorized['medium']:
            signal['confidence_badge'] = '🟠 Medium Confidence'
            signal['confidence_tier'] = 'medium'
            report_signals.append(signal)
        
        # Low confidence (NEW - now included!)
        for signal in categorized['low']:
            signal['confidence_badge'] = '🔵 Low Confidence'
            signal['confidence_tier'] = 'low'
            signal['_show_warning'] = True  # Show warning for low confidence
            report_signals.append(signal)
        
        # Log excluded
        excluded_count = len(categorized.get('excluded', []))
        if excluded_count > 0:
            print(f"⚠️  Excluded {excluded_count} very-low-confidence signals (< {self.min_confidence:.2f})")
        
        return report_signals
    
    def get_stats(self) -> dict:
        """Get filtering statistics."""
        stats = self.stats.copy()
        if stats['total'] > 0:
            stats['inclusion_rate'] = (stats['total'] - stats['excluded']) / stats['total']
            stats['avg_tier_distribution'] = {
                'verified': stats['verified'] / stats['total'],
                'high': stats['high'] / stats['total'],
                'medium': stats['medium'] / stats['total'],
                'low': stats['low'] / stats['total']
            }
        return stats


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def filter_by_confidence(signals: list[dict], min_confidence: float = 0.40) -> list[dict]:
    """
    Convenience function: Filter signals by confidence.
    
    Args:
        signals: List of signal dicts
        min_confidence: Minimum confidence threshold (default: 0.40 - RELAXED)
    
    Returns:
        List of signals above threshold with badges
    """
    filter_obj = ConfidenceFilter(min_confidence)
    return filter_obj.get_report_signals(signals)
