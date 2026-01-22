"""
LLM Fact-Checker - Layer 6 of Anti-Hallucination System

Second LLM pass to verify extracted facts.
Uses a different prompt strategy focused on verification and falsification.
"""

import os
from typing import Optional

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class LLMFactChecker:
    """
    Uses LLM to verify extracted facts against source text.
    
    Different from extraction: focuses on finding CONTRADICTIONS,
    not just confirming facts.
    """
    
    VERIFICATION_PROMPT = """You are a critical fact-checker. Your ONLY job is to verify if a claim is EXPLICITLY supported by the source text.

**CRITICAL RULES:**
1. Only confirm facts that are DIRECTLY STATED in the text
2. Look for CONTRADICTIONS or inconsistencies
3. If numbers don't match EXACTLY, flag it
4. If context is missing or unclear, flag it
5. Be SKEPTICAL - assume claims are wrong unless proven right

**Source Text:**
{source_text}

**Claim to Verify:**
- Metric: {metric}
- Value: {value}
- Period: {period}
- Region: {region}
- Quote: "{quote}"

**Your Task:**
1. Does the quote EXACTLY appear in the source? (yes/no/partial)
2. Does the source SUPPORT this specific claim? (yes/no/unclear)
3. Are there any CONTRADICTIONS? (yes/no - explain if yes)
4. Confidence in claim (0.0-1.0)
5. Reason for your assessment (1 sentence)

**Respond ONLY with valid JSON:**
{{
  "quote_verified": true/false,
  "claim_supported": true/false,
  "contradictions_found": false,
  "confidence": 0.0-1.0,
  "reason": "explanation"
}}
"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize fact-checker.
        
        Args:
            api_key: OpenAI API key (or from env)
            model: Model to use (cheaper model OK for verification)
        """
        if not api_key:
            api_key = os.environ.get('OPENAI_API_KEY')
        
        if not OpenAI or not api_key:
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        
        self.model = model
        self.stats = {
            'total_checked': 0,
            'verified': 0,
            'rejected': 0,
            'api_errors': 0
        }
    
    def verify_signal(
        self,
        signal: dict,
        source_text: str
    ) -> dict:
        """
        Verify a single signal using LLM.
        
        Args:
            signal: Signal dict
            source_text: Full source text
        
        Returns:
            Verification result dict
        """
        if not self.client:
            return {
                'verified': None,
                'reason': 'LLM not available',
                'confidence_adjustment': 0.0
            }
        
        self.stats['total_checked'] += 1
        
        # Build prompt
        value = signal.get('value', {})
        prompt = self.VERIFICATION_PROMPT.format(
            source_text=source_text[:4000],  # Limit context
            metric=value.get('metric', 'N/A'),
            value=value.get('numeric_value', 'N/A'),
            period=value.get('period', 'N/A'),
            region=value.get('region', 'N/A'),
            quote=signal.get('verbatim_quote', '')[:300]
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a critical fact-checker. Be skeptical."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=500
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Determine if verified
            verified = (
                result.get('quote_verified', False) and
                result.get('claim_supported', False) and
                not result.get('contradictions_found', False)
            )
            
            if verified:
                self.stats['verified'] += 1
            else:
                self.stats['rejected'] += 1
            
            # Calculate confidence adjustment
            llm_confidence = result.get('confidence', 0.5)
            current_confidence = signal.get('confidence', 0.5)
            
            # Conservative adjustment: pull towards LLM confidence
            adjustment = (llm_confidence - current_confidence) * 0.5
            
            return {
                'verified': verified,
                'llm_confidence': llm_confidence,
                'confidence_adjustment': adjustment,
                'reason': result.get('reason', ''),
                'quote_match': result.get('quote_verified', False),
                'contradictions': result.get('contradictions_found', False)
            }
        
        except Exception as e:
            self.stats['api_errors'] += 1
            return {
                'verified': None,
                'reason': f'LLM error: {str(e)[:100]}',
                'confidence_adjustment': -0.05  # Small penalty for verification failure
            }
    
    def verify_signals(
        self,
        signals: list[dict],
        sources: list[dict]
    ) -> list[dict]:
        """
        Verify multiple signals.
        
        Args:
            signals: List of signal dicts
            sources: List of source dicts (for text lookup)
        
        Returns:
            List of signals with verification results
        """
        # Build source lookup
        source_lookup = {
            s.get('url', ''): s.get('raw_text', '') or s.get('text', '')
            for s in sources
        }
        
        verified_signals = []
        
        for signal in signals:
            source_url = signal.get('source_url', '')
            source_text = source_lookup.get(source_url, '')
            
            if not source_text:
                # Can't verify without source
                signal['llm_verification'] = {
                    'verified': None,
                    'reason': 'Source text not available'
                }
                verified_signals.append(signal)
                continue
            
            # Run verification
            verification = self.verify_signal(signal, source_text)
            signal['llm_verification'] = verification
            
            # Apply confidence adjustment
            if verification['confidence_adjustment'] != 0:
                old_conf = signal.get('confidence', 0.5)
                new_conf = max(0.0, min(1.0, old_conf + verification['confidence_adjustment']))
                signal['confidence'] = new_conf
            
            verified_signals.append(signal)
        
        return verified_signals
    
    def get_stats(self) -> dict:
        """Get verification statistics."""
        stats = self.stats.copy()
        if stats['total_checked'] > 0:
            stats['verification_rate'] = stats['verified'] / stats['total_checked']
            stats['rejection_rate'] = stats['rejected'] / stats['total_checked']
        return stats


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def llm_verify(
    signals: list[dict],
    sources: list[dict],
    api_key: Optional[str] = None
) -> list[dict]:
    """
    Convenience function: Verify signals with LLM.
    
    Args:
        signals: List of signal dicts
        sources: List of source dicts
        api_key: Optional OpenAI API key
    
    Returns:
        List of signals with LLM verification results
    """
    checker = LLMFactChecker(api_key=api_key)
    return checker.verify_signals(signals, sources)
