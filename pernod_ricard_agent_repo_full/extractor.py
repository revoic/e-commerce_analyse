"""
Signal Extractor - Multi-Company E-commerce Intelligence

Extracts structured signals from articles using LLM with strict anti-hallucination measures.
Supports any company (not just Pernod Ricard).
"""

import os
import json
import re
from typing import Optional, List
from pathlib import Path

# Environment setup
from dotenv import load_dotenv
load_dotenv()

# Streamlit secrets fallback
try:
    import streamlit as st
except ImportError:
    st = None

# OpenAI client
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Pydantic models
from models.signal_models import Signal, SignalValue


class SignalExtractor:
    """
    Extracts signals from article text using LLM.
    
    Enforces strict validation to prevent hallucination:
    - Uses specialized extraction prompt
    - Validates against Pydantic schema
    - Requires verbatim quotes
    - Conservative confidence scores
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        prompt_file: str = "extract_signals_v2.txt"
    ):
        """
        Initialize extractor.
        
        Args:
            api_key: OpenAI API key (or from env/secrets)
            model: Model to use
            prompt_file: Prompt filename in prompts/ directory
        """
        # Get API key
        if not api_key:
            api_key = os.getenv('OPENAI_API_KEY')
        if not api_key and st is not None:
            api_key = st.secrets.get('OPENAI_API_KEY')
        
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY not set. Set in .env or Streamlit secrets."
            )
        
        if not OpenAI:
            raise RuntimeError("openai package not installed. Run: pip install openai")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        
        # Load prompt template
        prompt_path = Path(__file__).parent / "prompts" / prompt_file
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        self.prompt_template = prompt_path.read_text(encoding='utf-8')
        
        # Stats
        self.stats = {
            'articles_processed': 0,
            'signals_extracted': 0,
            'validation_failures': 0,
            'api_errors': 0
        }
    
    def extract_from_article(
        self,
        article_text: str,
        article_title: str,
        article_url: str,
        company_name: str
    ) -> List[Signal]:
        """
        Extract signals from a single article.
        
        Args:
            article_text: Full article text
            article_title: Article title
            article_url: Article URL
            company_name: Company being analyzed
        
        Returns:
            List of validated Signal objects
        """
        self.stats['articles_processed'] += 1
        
        # Build prompt
        prompt = self.prompt_template.format(
            company_name=company_name,
            article_text=article_text[:8000],  # Limit context
            article_title=article_title,
            article_url=article_url
        )
        
        try:
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a rigorous fact extractor. Only extract explicitly stated facts with exact quotes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=2000
            )
            
            # Parse response
            content = response.choices[0].message.content
            data = json.loads(content)
            
            # Extract signals array
            signals_raw = data.get('signals', [])
            if not signals_raw:
                return []
            
            # Validate each signal with Pydantic
            validated_signals = []
            
            for signal_data in signals_raw:
                try:
                    # Pydantic validation (strict schema)
                    signal = Signal(**signal_data)
                    validated_signals.append(signal)
                    self.stats['signals_extracted'] += 1
                    
                except Exception as e:
                    # Validation failed - skip this signal
                    self.stats['validation_failures'] += 1
                    continue
            
            return validated_signals
        
        except Exception as e:
            self.stats['api_errors'] += 1
            # Return empty list on error (graceful degradation)
            return []
    
    def extract_from_sources(
        self,
        sources: List[dict],
        company_name: str
    ) -> List[dict]:
        """
        Extract signals from multiple sources.
        
        Args:
            sources: List of source dicts with 'text', 'title', 'url'
            company_name: Company being analyzed
        
        Returns:
            List of signal dicts (serialized Pydantic models)
        """
        all_signals = []
        
        for source in sources:
            text = source.get('text') or source.get('raw_text', '')
            title = source.get('title', '')
            url = source.get('url', '')
            
            if not text or len(text) < 100:
                continue
            
            # Extract signals
            signals = self.extract_from_article(
                article_text=text,
                article_title=title,
                article_url=url,
                company_name=company_name
            )
            
            # Convert to dicts for further processing
            for signal in signals:
                signal_dict = signal.model_dump()
                all_signals.append(signal_dict)
        
        return all_signals
    
    def get_stats(self) -> dict:
        """Get extraction statistics."""
        return self.stats.copy()


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def extract_signals(
    sources: List[dict],
    company_name: str,
    api_key: Optional[str] = None
) -> List[dict]:
    """
    Convenience function: Extract signals from sources.
    
    Args:
        sources: List of source dicts
        company_name: Company name
        api_key: Optional OpenAI API key
    
    Returns:
        List of signal dicts
    """
    extractor = SignalExtractor(api_key=api_key)
    return extractor.extract_from_sources(sources, company_name)


# ==============================================================================
# CLI TEST
# ==============================================================================

if __name__ == "__main__":
    # Test extraction
    test_article = """
    ACME Corp Announces Strong Q4 Results
    
    San Francisco, Jan 15, 2026 - ACME Corp reported record quarterly revenue 
    of $2.5 billion for Q4 2025, representing 18% year-over-year growth.
    
    The company's e-commerce division was a key driver, with online sales 
    increasing 32% compared to Q4 2024. In Europe, ACME saw particularly 
    strong performance, with German market revenue up 25% to €450 million.
    
    "Our digital transformation is paying off," said CEO Jane Smith. 
    "We're seeing strong momentum across all channels."
    """
    
    try:
        extractor = SignalExtractor()
        signals = extractor.extract_from_article(
            article_text=test_article,
            article_title="ACME Corp Q4 Results",
            article_url="https://example.com/acme-q4",
            company_name="ACME Corp"
        )
        
        print(f"✅ Extracted {len(signals)} signals:")
        for i, sig in enumerate(signals, 1):
            print(f"\n{i}. {sig.value.metric}")
            print(f"   Value: {sig.value.numeric_value} {sig.value.unit}")
            print(f"   Confidence: {sig.confidence:.0%}")
            print(f"   Quote: {sig.verbatim_quote[:100]}...")
        
        print(f"\n📊 Stats: {extractor.get_stats()}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
