"""
Analysis Engine - Orchestrates the complete analysis pipeline

Coordinates:
1. Source discovery (via CompanyIntelligenceScraper)
2. Signal extraction (via SignalExtractor)
3. Multi-layer validation (7 layers of anti-hallucination)
4. Report generation
5. Database persistence

This is the main entry point for running a company analysis.
"""

import sys
import os
from typing import Optional, Callable
from datetime import datetime

# Add parent directory to path so we can import from project root
_parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

# Import from project modules
from core.scraper import CompanyIntelligenceScraper
from extractor import SignalExtractor
from validators.citation_validator import CitationValidator
from validators.confidence_filter import ConfidenceFilter
from validators.cross_reference import CrossReferenceValidator
from validators.llm_fact_checker import LLMFactChecker


class AnalysisEngine:
    """
    Orchestrates complete company analysis pipeline.
    
    Implements 7-layer anti-hallucination system:
    1. Source Verification (scraper handles)
    2. Citation Enforcement (CitationValidator)
    3. Structured Extraction (Pydantic models)
    4. Confidence Filtering (ConfidenceFilter)
    5. Cross-Reference Validation (CrossReferenceValidator)
    6. LLM Fact-Checking (LLMFactChecker)
    7. Human Review (optional - not implemented in MVP)
    """
    
    def __init__(
        self,
        company_name: str,
        config: Optional[dict] = None,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize analysis engine.
        
        Args:
            company_name: Company to analyze
            config: Configuration dict (scraper settings, etc.)
            progress_callback: Optional callback(message: str, progress: float)
        """
        self.company_name = company_name
        self.config = config or {}
        self.progress_callback = progress_callback or (lambda msg, pct: None)
        
        # Initialize components (validators will be created after we have sources)
        self.scraper = CompanyIntelligenceScraper(company_name, config)
        self.extractor = SignalExtractor()
        
        # Results
        self.sources = []
        self.raw_signals = []
        self.validated_signals = []
        self.final_signals = []
        self.report = {}
        
        # Stats
        self.stats = {
            'start_time': None,
            'end_time': None,
            'duration_seconds': None
        }
    
    def _progress(self, message: str, percent: float):
        """Report progress."""
        self.progress_callback(message, percent)
    
    def run_analysis(self) -> dict:
        """
        Run complete analysis pipeline.
        
        Returns:
            Analysis result dict with sources, signals, and report
        """
        self.stats['start_time'] = datetime.now()
        
        try:
            # Step 1: Discover sources (0-30%)
            self._progress("🔍 Discovering sources...", 0.0)
            self.sources = self.scraper.discover_all_sources()
            self._progress(f"✓ Found {len(self.sources)} sources", 0.30)
            
            if not self.sources:
                self.report = self._generate_empty_report("No sources found")
                return self._build_result("No sources found")
            
            # Step 2: Extract signals (30-50%)
            self._progress("🧠 Extracting signals with LLM...", 0.30)
            self.raw_signals = self.extractor.extract_from_sources(
                self.sources,
                self.company_name
            )
            self._progress(f"✓ Extracted {len(self.raw_signals)} raw signals", 0.50)
            
            if not self.raw_signals:
                # Generate report with stats even if no signals extracted
                self.citation_validator = CitationValidator(self.sources)
                self.cross_validator = CrossReferenceValidator()
                self.fact_checker = LLMFactChecker()
                self.confidence_filter = ConfidenceFilter()
                filter_results = {'high_confidence': [], 'medium_confidence': [], 'low_confidence': [], 'stats': {}}
                self.report = self._generate_report(filter_results)
                return self._build_result("No signals extracted from sources")
            
            # Step 3: Citation validation (50-60%)
            self._progress("📝 Validating citations...", 0.50)
            self.citation_validator = CitationValidator(self.sources)
            citation_results = self.citation_validator.validate_all_signals(
                self.raw_signals,
                self.sources
            )
            self.validated_signals = citation_results['validated_signals']
            self._progress(
                f"✓ Validated {len(self.validated_signals)} signals",
                0.60
            )
            
            if not self.validated_signals:
                # Still generate report even with 0 signals
                self.cross_validator = CrossReferenceValidator()
                self.fact_checker = LLMFactChecker()
                self.confidence_filter = ConfidenceFilter()
                filter_results = {'high_confidence': [], 'medium_confidence': [], 'low_confidence': [], 'stats': {}}
                self.report = self._generate_report(filter_results)
                return self._build_result("All signals failed citation validation")
            
            # Step 4: Cross-reference validation (60-70%)
            self._progress("🔗 Cross-referencing sources...", 0.60)
            self.cross_validator = CrossReferenceValidator()
            self.validated_signals = self.cross_validator.validate_signals_cross_reference(
                self.validated_signals,
                self.sources
            )
            self._progress("✓ Cross-reference complete", 0.70)
            
            # Step 5: LLM fact-checking (70-85%)
            self._progress("🔍 LLM fact-checking...", 0.70)
            self.fact_checker = LLMFactChecker()
            self.validated_signals = self.fact_checker.verify_signals(
                self.validated_signals,
                self.sources
            )
            self._progress("✓ Fact-checking complete", 0.85)
            
            # Step 6: Confidence filtering (85-90%)
            self._progress("📊 Filtering by confidence...", 0.85)
            self.confidence_filter = ConfidenceFilter()
            filter_results = self.confidence_filter.filter_signals(self.validated_signals)
            self.final_signals = filter_results['high_confidence']
            self._progress(
                f"✓ {len(self.final_signals)} high-confidence signals",
                0.90
            )
            
            # Step 7: Generate report (90-100%)
            self._progress("📄 Generating report...", 0.90)
            self.report = self._generate_report(filter_results)
            self._progress("✅ Analysis complete!", 1.0)
            
            return self._build_result("success")
        
        except Exception as e:
            self._progress(f"❌ Error: {str(e)}", 1.0)
            return self._build_result(f"Error: {str(e)}")
        
        finally:
            self.stats['end_time'] = datetime.now()
            if self.stats['start_time']:
                delta = self.stats['end_time'] - self.stats['start_time']
                self.stats['duration_seconds'] = delta.total_seconds()
    
    def _generate_empty_report(self, reason: str) -> dict:
        """Generate minimal report when analysis fails early."""
        return {
            'company': self.company_name,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_sources': len(self.sources),
                'high_confidence_signals': 0,
                'medium_confidence_signals': 0,
                'metrics_covered': 0,
                'regions': {},
                'error': reason
            },
            'signals_by_metric': {},
            'all_high_confidence_signals': [],
            'validation_stats': {
                'scraper': self.scraper.get_stats() if hasattr(self, 'scraper') else {},
                'extractor': self.extractor.get_stats() if hasattr(self, 'extractor') else {},
                'error': reason
            }
        }
    
    def _generate_report(self, filter_results: dict) -> dict:
        """
        Generate analysis report.
        
        Args:
            filter_results: Output from ConfidenceFilter
        
        Returns:
            Report dict
        """
        high_conf = filter_results['high_confidence']
        medium_conf = filter_results['medium_confidence']
        
        # Group signals by metric type
        metrics_map = {}
        for sig in high_conf:
            metric = sig.get('value', {}).get('metric', 'unknown')
            if metric not in metrics_map:
                metrics_map[metric] = []
            metrics_map[metric].append(sig)
        
        # Summary stats
        total_sources = len(self.sources)
        high_conf_count = len(high_conf)
        medium_conf_count = len(medium_conf)
        
        # Regional breakdown
        regions = {}
        for sig in high_conf:
            region = sig.get('value', {}).get('region', 'Unknown')
            regions[region] = regions.get(region, 0) + 1
        
        return {
            'company': self.company_name,
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_sources': total_sources,
                'high_confidence_signals': high_conf_count,
                'medium_confidence_signals': medium_conf_count,
                'metrics_covered': len(metrics_map),
                'regions': regions
            },
            'signals_by_metric': metrics_map,
            'all_high_confidence_signals': high_conf,
            'validation_stats': {
                'scraper': self.scraper.get_discovery_stats(),
                'extractor': self.extractor.get_stats(),
                'citation_validator': self.citation_validator.get_stats() if hasattr(self, 'citation_validator') else {},
                'cross_reference': self.cross_validator.get_stats() if hasattr(self, 'cross_validator') else {},
                'fact_checker': self.fact_checker.get_stats() if hasattr(self, 'fact_checker') else {},
                'confidence_filter': filter_results.get('stats', {})
            }
        }
    
    def _build_result(self, status: str) -> dict:
        """Build final result dict."""
        return {
            'status': status,
            'company': self.company_name,
            'sources': self.sources,
            'signals': self.final_signals,
            'report': self.report,
            'stats': {
                **self.stats,
                'source_count': len(self.sources),
                'signal_count': len(self.final_signals)
            }
        }


# ==============================================================================
# CONVENIENCE FUNCTION
# ==============================================================================

def analyze_company(
    company_name: str,
    config: Optional[dict] = None,
    progress_callback: Optional[Callable] = None
) -> dict:
    """
    Convenience function: Run complete company analysis.
    
    Args:
        company_name: Company to analyze
        config: Optional configuration
        progress_callback: Optional progress callback
    
    Returns:
        Analysis result dict
    """
    engine = AnalysisEngine(company_name, config, progress_callback)
    return engine.run_analysis()


# ==============================================================================
# CLI TEST
# ==============================================================================

if __name__ == "__main__":
    import sys
    
    company = sys.argv[1] if len(sys.argv) > 1 else "ACME Corp"
    
    def print_progress(msg, pct):
        print(f"[{pct*100:3.0f}%] {msg}")
    
    print(f"🚀 Starting analysis for: {company}")
    print("=" * 60)
    
    result = analyze_company(
        company_name=company,
        config={'lookback_days': 30, 'max_sources': 20},
        progress_callback=print_progress
    )
    
    print("\n" + "=" * 60)
    print(f"Status: {result['status']}")
    print(f"Sources: {result['stats']['source_count']}")
    print(f"Signals: {result['stats']['signal_count']}")
    print(f"Duration: {result['stats'].get('duration_seconds', 0):.1f}s")
    
    if result.get('report'):
        print("\n📊 Report Summary:")
        summary = result['report']['summary']
        for key, val in summary.items():
            print(f"  {key}: {val}")
