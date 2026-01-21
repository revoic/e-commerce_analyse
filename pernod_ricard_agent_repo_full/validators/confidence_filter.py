"""
Confidence Filter - Layer 4 of Anti-Hallucination System

Multi-tier confidence filtering with badges for UI display.
"""

class ConfidenceFilter:
    """
    Multi-tier confidence filtering system.
    
    Thresholds:
    - Verified: >= 0.90
    - High: >= 0.80
    - Medium: >= 0.70
    - Low: < 0.70 (excluded from reports)
    """
    
    # Confidence thresholds
    THRESHOLD_VERIFIED = 0.90
    THRESHOLD_HIGH = 0.80
    THRESHOLD_INCLUDE = 0.70
    
    def __init__(self, min_confidence: float = THRESHOLD_INCLUDE):
        """
        Initialize filter.
        
        Args:
            min_confidence: Minimum confidence to include (default: 0.70)
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
            Dict with keys: verified, high, medium, low
        """
        result = {
            'verified': [],  # >= 0.90
            'high': [],      # >= 0.80
            'medium': [],    # >= 0.70
            'low': []        # < 0.70
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
            elif conf >= self.THRESHOLD_INCLUDE:
                result['medium'].append(signal)
                self.stats['medium'] += 1
            else:
                result['low'].append(signal)
                self.stats['low'] += 1
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
        
        # Medium confidence (with warning)
        for signal in categorized['medium']:
            signal['confidence_badge'] = '🟠 Medium Confidence'
            signal['confidence_tier'] = 'medium'
            signal['_show_warning'] = True
            report_signals.append(signal)
        
        # Log excluded
        excluded_count = len(categorized['low'])
        if excluded_count > 0:
            print(f"⚠️  Excluded {excluded_count} low-confidence signals (< {self.min_confidence:.2f})")
        
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

def filter_by_confidence(signals: list[dict], min_confidence: float = 0.70) -> list[dict]:
    """
    Convenience function: Filter signals by confidence.
    
    Args:
        signals: List of signal dicts
        min_confidence: Minimum confidence threshold
    
    Returns:
        List of signals above threshold with badges
    """
    filter_obj = ConfidenceFilter(min_confidence)
    return filter_obj.get_report_signals(signals)
