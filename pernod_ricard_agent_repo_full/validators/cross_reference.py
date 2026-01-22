"""
Cross-Reference Validator - Layer 5 of Anti-Hallucination System

Validates that facts appear in multiple sources (corroboration).
"""

try:
    from utils.text_utils import normalize_text
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.text_utils import normalize_text


class CrossReferenceValidator:
    """
    Validates facts by finding corroborating sources.
    
    Boosts confidence when multiple sources confirm the same fact.
    Reduces confidence when only single source available.
    """
    
    def __init__(self, min_sources_for_boost: int = 2):
        """
        Initialize validator.
        
        Args:
            min_sources_for_boost: Minimum corroborating sources for confidence boost
        """
        self.min_sources = min_sources_for_boost
        self.stats = {
            'total_checked': 0,
            'with_corroboration': 0,
            'single_source': 0
        }
    
    def find_corroborating_sources(self, signal: dict, all_sources: list[dict]) -> list[str]:
        """
        Find additional sources that mention the same fact.
        
        Args:
            signal: Signal dict to validate
            all_sources: List of all source dicts
        
        Returns:
            List of URLs of corroborating sources
        """
        # Extract key information from signal
        value = signal.get('value', {})
        original_url = signal.get('source_url', '')
        
        # Build search terms
        search_terms = []
        
        # Numeric value (strongest signal)
        if value.get('numeric_value') is not None:
            num = value['numeric_value']
            search_terms.append(str(int(num)))
            search_terms.append(f"{num:.1f}")
            search_terms.append(f"{num:.2f}")
        
        # Metric name
        if value.get('metric'):
            metric_norm = normalize_text(value['metric'])
            if metric_norm:
                search_terms.append(metric_norm)
        
        # Region
        if value.get('region'):
            search_terms.append(value['region'].upper())
        
        # Period
        if value.get('period'):
            period_norm = normalize_text(value['period'])
            if period_norm:
                search_terms.append(period_norm)
        
        # Search in all sources
        corroborating_urls = []
        
        for source in all_sources:
            source_url = source.get('url', '')
            
            # Skip original source
            if source_url == original_url:
                continue
            
            # Get text
            text = source.get('raw_text', '') or source.get('text', '')
            if not text:
                continue
            
            text_normalized = normalize_text(text)
            
            # Count how many search terms appear
            matches = sum(
                1 for term in search_terms
                if term and term in text_normalized
            )
            
            # If at least 2 terms match, consider it corroborating
            if matches >= 2:
                corroborating_urls.append(source_url)
        
        return corroborating_urls
    
    def validate_signals_cross_reference(
        self,
        signals: list[dict],
        sources: list[dict]
    ) -> list[dict]:
        """
        Validate signals and adjust confidence based on corroboration.
        
        Args:
            signals: List of signal dicts
            sources: List of source dicts
        
        Returns:
            List of signals with updated confidence scores
        """
        enhanced_signals = []
        
        for signal in signals:
            self.stats['total_checked'] += 1
            
            # Find corroborating sources
            corroborating = self.find_corroborating_sources(signal, sources)
            
            signal['corroborating_sources'] = corroborating
            signal['corroboration_count'] = len(corroborating)
            
            original_conf = signal.get('confidence', 0.5)
            
            # Adjust confidence
            if len(corroborating) >= self.min_sources:
                # Boost confidence for corroboration
                boost = min(0.10, len(corroborating) * 0.03)
                new_conf = min(0.99, original_conf + boost)
                signal['confidence'] = new_conf
                signal['confidence_boost'] = f"+{boost:.2f} ({len(corroborating)} sources)"
                self.stats['with_corroboration'] += 1
                
            elif len(corroborating) == 0:
                # Reduce confidence for single source
                penalty = 0.15
                new_conf = original_conf * (1 - penalty)
                signal['confidence'] = new_conf
                signal['confidence_penalty'] = f"-{penalty:.0%} (single source)"
                self.stats['single_source'] += 1
            
            enhanced_signals.append(signal)
        
        return enhanced_signals
    
    def get_stats(self) -> dict:
        """Get cross-reference statistics."""
        stats = self.stats.copy()
        if stats['total_checked'] > 0:
            stats['corroboration_rate'] = stats['with_corroboration'] / stats['total_checked']
        return stats


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def cross_validate(signals: list[dict], sources: list[dict]) -> list[dict]:
    """
    Convenience function: Cross-validate signals.
    
    Args:
        signals: List of signal dicts
        sources: List of source dicts
    
    Returns:
        List of signals with adjusted confidence
    """
    validator = CrossReferenceValidator()
    return validator.validate_signals_cross_reference(signals, sources)
