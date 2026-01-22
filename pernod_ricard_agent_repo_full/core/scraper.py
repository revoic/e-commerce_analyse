"""
Company Intelligence Scraper - Multi-source discovery for any company.

Discovers sources from:
- Google News (EU editions + E-Commerce queries)
- LinkedIn (via Google News site: search)
- Company Newsroom (auto-discovery)
"""

import os
import re
import math
import time
from typing import Optional, List, Dict
from datetime import datetime, timezone, timedelta
from urllib.parse import urlencode, urljoin

import requests
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as dateparser

# Import our utilities
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.url_utils import (
    guess_domain_from_company_name,
    normalize_url,
    is_eu_url,
    build_newsroom_candidates,
    build_investor_relations_candidates,
    build_earnings_report_candidates,
    build_company_blog_candidates,
    is_valid_url,
    is_investor_relations_url,
    is_earnings_report_url,
    extract_domain
)
from utils.text_utils import hash_text, clean_whitespace, remove_html_tags
from utils.pdf_utils import (
    extract_text_from_pdf_url,
    is_pdf_url,
    is_earnings_report_pdf,
    extract_key_metrics_from_text
)


# ==============================================================================
# CONFIGURATION
# ==============================================================================

# EU Google News editions (language, country, ceid)
EU_GNEWS_EDITIONS = [
    ("de", "DE", "DE:de"),      # Germany
    ("de", "AT", "AT:de"),      # Austria
    ("de", "CH", "CH:de"),      # Switzerland
    ("fr", "FR", "FR:fr"),      # France
    ("it", "IT", "IT:it"),      # Italy
    ("es", "ES", "ES:es"),      # Spain
    ("nl", "NL", "NL:nl"),      # Netherlands
    ("sv", "SE", "SE:sv"),      # Sweden
    ("pl", "PL", "PL:pl"),      # Poland
    ("da", "DK", "DK:da"),      # Denmark
    ("no", "NO", "NO:no"),      # Norway
    ("fi", "FI", "FI:fi"),      # Finland
    ("en-IE", "IE", "IE:en-IE"), # Ireland
    ("en-GB", "GB", "GB:en-GB"), # UK
]

# E-Commerce query templates (multi-language)
ECOMMERCE_QUERY_TEMPLATES = [
    # German
    '{company} (E-Commerce OR "E-Commerce" OR Onlinehandel OR Marktplatz OR "Retail Media" OR Amazon OR Zalando OR D2C)',
    # English
    '{company} (ecommerce OR "e-commerce" OR marketplace OR "retail media" OR Amazon OR D2C OR "online sales")',
    # French
    '{company} (e-commerce OR "commerce en ligne" OR marketplace OR "retail media" OR Amazon OR D2C)',
    # Spanish
    '{company} (ecommerce OR "comercio electrónico" OR marketplace OR "retail media" OR Amazon OR D2C)',
]

# E-Commerce keywords for detection
ECOMMERCE_KEYWORDS = [
    "e-commerce", "ecommerce", "onlinehandel", "marktplatz", "marketplace",
    "retail media", "amazon", "zalando", "d2c", "online sales", "digital commerce",
    "webshop", "checkout", "cart", "conversion", "gmv", "buy box"
]

# HTTP headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EcommerceIntel/2.0; +https://github.com)"
}

TIMEOUT = 20  # seconds


# ==============================================================================
# COMPANY INTELLIGENCE SCRAPER
# ==============================================================================

class CompanyIntelligenceScraper:
    """
    Multi-source scraper for company intelligence.
    
    Discovers and enriches sources for any company with focus on
    EU/DE markets and E-Commerce.
    """
    
    def __init__(self, company_name: str, config: Optional[Dict] = None):
        """
        Initialize scraper for a company.
        
        Args:
            company_name: Company name (e.g. "Coca-Cola")
            config: Optional configuration dict with:
                - domain: Company domain (optional)
                - newsroom_url: Direct newsroom URL (optional)
                - linkedin_url: Direct LinkedIn URL (optional)
                - lookback_days: Days to look back (default: 14)
                - max_per_source: Max items per source type (default: 10)
        """
        self.company_name = company_name
        self.config = config or {}
        
        # Extract config
        self.domain = self.config.get("domain") or guess_domain_from_company_name(company_name)
        self.newsroom_url = self.config.get("newsroom_url")
        self.linkedin_url = self.config.get("linkedin_url")
        self.lookback_days = self.config.get("lookback_days", 14)
        self.max_per_source = self.config.get("max_per_source", 10)
        
        # Calculate lookback
        self.lookback_hours = self.lookback_days * 24
        self.cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.lookback_days)
        
        # Statistics
        self.stats = {
            "investor_relations": 0,
            "earnings_reports": 0,
            "direct_newsroom": 0,
            "bing_news": 0,
            "linkedin": 0,
            "google_news": 0,
            "errors": []
        }
    
    # ==========================================================================
    # MAIN ORCHESTRATOR
    # ==========================================================================
    
    def discover_all_sources(self) -> List[Dict]:
        """
        Discover sources from all available channels.
        
        NEW PRIORITY STRATEGY (BETTER LONG-TERM):
        1. Investor Relations pages (highest data quality)
        2. Earnings Reports (PDFs with financial data)
        3. Direct Newsroom RSS (no Google News proxy)
        4. Bing News (fallback only)
        5. LinkedIn (fallback only)
        
        Returns:
            List of source dicts with keys:
                - url: Source URL
                - title: Article title
                - source: Source type (e.g. "ir", "earnings", "newsroom")
                - published_at: ISO timestamp (optional)
                - priority: int (1=highest, 5=lowest)
        """
        all_sources = []
        
        print(f"\n🔍 Discovering sources for: {self.company_name}")
        print(f"   Domain: {self.domain}")
        print(f"   Lookback: {self.lookback_days} days")
        print(f"\n💡 Strategy: IR > Earnings > Direct Newsroom > Bing News (Fallback)")
        
        # ==========================================
        # PRIORITY 1: INVESTOR RELATIONS
        # ==========================================
        print("\n📊 [P1] Investor Relations...")
        try:
            ir_sources = self._discover_investor_relations()
            all_sources.extend(ir_sources)
            self.stats["investor_relations"] = len(ir_sources)
            print(f"   ✓ Found {len(ir_sources)} IR pages (HIGH QUALITY)")
        except Exception as e:
            error_msg = f"IR discovery failed: {e}"
            print(f"   ✗ {error_msg}")
            self.stats["errors"].append(error_msg)
        
        # ==========================================
        # PRIORITY 2: EARNINGS REPORTS (PDFs)
        # ==========================================
        print("\n📈 [P2] Earnings Reports...")
        try:
            earnings_sources = self._discover_earnings_reports()
            all_sources.extend(earnings_sources)
            self.stats["earnings_reports"] = len(earnings_sources)
            print(f"   ✓ Found {len(earnings_sources)} earnings reports (FINANCIAL DATA)")
        except Exception as e:
            error_msg = f"Earnings discovery failed: {e}"
            print(f"   ✗ {error_msg}")
            self.stats["errors"].append(error_msg)
        
        # ==========================================
        # PRIORITY 3: DIRECT NEWSROOM (NO GOOGLE)
        # ==========================================
        print("\n🏢 [P3] Direct Newsroom RSS...")
        try:
            newsroom_sources = self._discover_direct_newsroom()
            all_sources.extend(newsroom_sources)
            self.stats["direct_newsroom"] = len(newsroom_sources)
            print(f"   ✓ Found {len(newsroom_sources)} newsroom articles (OFFICIAL)")
        except Exception as e:
            error_msg = f"Direct newsroom failed: {e}"
            print(f"   ✗ {error_msg}")
            self.stats["errors"].append(error_msg)
        
        # ==========================================
        # PRIORITY 4: BING NEWS (FALLBACK)
        # ==========================================
        print("\n🌐 [P4] Bing News (Fallback)...")
        try:
            bing_sources = self._discover_bing_news()
            all_sources.extend(bing_sources)
            self.stats["bing_news"] = len(bing_sources)
            print(f"   ✓ Found {len(bing_sources)} Bing news articles (SUPPLEMENT)")
        except Exception as e:
            error_msg = f"Bing News failed: {e}"
            print(f"   ℹ️  {error_msg} (non-critical)")
            self.stats["errors"].append(error_msg)
        
        # ==========================================
        # PRIORITY 5: LINKEDIN (FALLBACK)
        # ==========================================
        print("\n💼 [P5] LinkedIn (Fallback)...")
        try:
            linkedin_sources = self._discover_linkedin()
            all_sources.extend(linkedin_sources)
            self.stats["linkedin"] = len(linkedin_sources)
            print(f"   ✓ Found {len(linkedin_sources)} LinkedIn posts (SOCIAL)")
        except Exception as e:
            error_msg = f"LinkedIn failed: {e}"
            print(f"   ℹ️  {error_msg} (non-critical)")
            self.stats["errors"].append(error_msg)
        
        # Deduplicate by URL
        all_sources = self._deduplicate_sources(all_sources)
        
        print(f"\n✅ Total sources discovered: {len(all_sources)}")
        print(f"   📊 IR Pages: {self.stats['investor_relations']}")
        print(f"   📈 Earnings: {self.stats['earnings_reports']}")
        print(f"   🏢 Newsroom: {self.stats['direct_newsroom']}")
        print(f"   🌐 Bing: {self.stats['bing_news']}")
        print(f"   💼 LinkedIn: {self.stats['linkedin']}")
        
        if self.stats["errors"]:
            print(f"\n⚠️  Errors: {len(self.stats['errors'])}")
            for err in self.stats["errors"][:2]:
                print(f"   - {err[:80]}...")
        
        # Fetch full content for each source
        if not all_sources:
            error_msg = "❌ No sources discovered from ANY channel! "
            if self.stats["errors"]:
                error_msg += f"\nErrors: {', '.join(self.stats['errors'][:2])}"
            raise Exception(error_msg)
        
        print(f"\n📥 Fetching content for {len(all_sources)} sources...")
        all_sources = self.enrich_sources(all_sources)
        print(f"✅ Successfully enriched {len(all_sources)} sources with content")
        
        if not all_sources:
            raise Exception(
                f"❌ All sources failed during content enrichment. "
                "Possible causes: Paywalls, Anti-scraping, Network issues."
            )
        
        return all_sources
    
    # ==========================================================================
    # GOOGLE NEWS DISCOVERY
    # ==========================================================================
    
    def _discover_google_news(self) -> List[Dict]:
        """Discover via Google News RSS (EU editions + E-Commerce queries)."""
        sources = []
        
        # Base query: Company name
        base_query = f'"{self.company_name}"'
        
        # 1. Generic company query across EU editions
        for lang, gl, ceid in EU_GNEWS_EDITIONS:
            try:
                url = self._build_gnews_url(base_query, lang, gl, ceid)
                items = self._parse_gnews_feed(url, f"gnews:{gl.lower()}:{lang}")
                sources.extend(items[:self.max_per_source])
            except Exception as e:
                self.stats["errors"].append(f"GNews {gl} failed: {e}")
                continue
        
        # 2. E-Commerce focused queries
        for template in ECOMMERCE_QUERY_TEMPLATES:
            query = template.format(company=self.company_name)
            
            # Query across key EU markets only (to avoid too many requests)
            key_markets = [("de", "DE", "DE:de"), ("en-GB", "GB", "GB:en-GB"), ("fr", "FR", "FR:fr")]
            
            for lang, gl, ceid in key_markets:
                try:
                    url = self._build_gnews_url(query, lang, gl, ceid)
                    items = self._parse_gnews_feed(url, f"gnews-ecom:{gl.lower()}:{lang}")
                    sources.extend(items[:self.max_per_source])
                except Exception as e:
                    continue  # Silent fail for e-commerce queries (optional)
        
        return sources
    
    def _build_gnews_url(self, query: str, lang: str, gl: str, ceid: str) -> str:
        """Build Google News RSS URL."""
        when_days = max(1, math.ceil(self.lookback_hours / 24))
        q = f"{query} when:{when_days}d"
        
        params = {
            "q": q,
            "hl": lang,
            "gl": gl,
            "ceid": ceid
        }
        
        return f"https://news.google.com/rss/search?{urlencode(params)}"
    
    def _parse_gnews_feed(self, url: str, source_tag: str) -> List[Dict]:
        """Parse Google News RSS feed."""
        try:
            feed = feedparser.parse(url)
            items = []
            
            for entry in feed.entries:
                link = entry.get("link", "")
                if not link:
                    continue
                
                title = entry.get("title", "").strip() or "News"
                
                # Try to parse published date
                published_at = None
                for date_field in ("published", "updated"):
                    if date_field in entry:
                        try:
                            dt = dateparser.parse(entry[date_field])
                            if dt and dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            published_at = dt
                            break
                        except Exception:
                            continue
                
                items.append({
                    "url": link,
                    "title": title,
                    "source": source_tag,
                    "published_at": published_at.isoformat() if published_at else None
                })
            
            return items
        except Exception as e:
            raise Exception(f"Failed to parse feed {url}: {e}")
    
    # ==========================================================================
    # LINKEDIN DISCOVERY
    # ==========================================================================
    
    def _discover_linkedin(self) -> List[Dict]:
        """Discover LinkedIn posts via Google News site: search."""
        sources = []
        
        # If direct LinkedIn URL provided, add it
        if self.linkedin_url:
            sources.append({
                "url": self.linkedin_url,
                "title": f"{self.company_name} - LinkedIn",
                "source": "linkedin:direct",
                "published_at": None
            })
        
        # Search LinkedIn via Google News (site:linkedin.com)
        when_days = max(1, math.ceil(self.lookback_hours / 24))
        query = f'"{self.company_name}" site:linkedin.com when:{when_days}d'
        
        # Search in key EU markets
        key_markets = [("en-GB", "GB", "GB:en-GB"), ("de", "DE", "DE:de")]
        
        for lang, gl, ceid in key_markets:
            try:
                params = {
                    "q": query,
                    "hl": lang,
                    "gl": gl,
                    "ceid": ceid
                }
                url = f"https://news.google.com/rss/search?{urlencode(params)}"
                
                items = self._parse_gnews_feed(url, f"linkedin:gnews:{gl.lower()}")
                sources.extend(items[:self.max_per_source])
            except Exception:
                continue
        
        return sources
    
    # ==========================================================================
    # INVESTOR RELATIONS DISCOVERY (NEW - PRIORITY 1)
    # ==========================================================================
    
    def _discover_investor_relations(self) -> List[Dict]:
        """
        Discover Investor Relations pages (HIGHEST PRIORITY).
        
        IR pages typically contain:
        - Financial reports
        - Earnings releases
        - Investor presentations
        - Quarterly/Annual reports
        """
        sources = []
        
        # Auto-discover IR page
        candidates = build_investor_relations_candidates(self.domain)
        
        for candidate_url in candidates[:10]:  # Check top 10 most likely
            try:
                response = requests.head(candidate_url, headers=HEADERS, timeout=5, allow_redirects=True)
                
                if response.status_code < 400:
                    print(f"   ✓ Found IR page: {candidate_url}")
                    items = self._scrape_ir_index(candidate_url)
                    sources.extend(items)
                    
                    if items:
                        return sources  # Found IR page with content, stop
            except Exception:
                continue
        
        return sources
    
    def _scrape_ir_index(self, url: str) -> List[Dict]:
        """Scrape IR index page for reports and articles."""
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            items = []
            
            # Find all links
            for link in soup.find_all("a", href=True):
                href = link.get("href", "").strip()
                if not href:
                    continue
                
                # Make absolute URL
                if not href.startswith("http"):
                    href = urljoin(url, href)
                
                if not is_valid_url(href):
                    continue
                
                # Filter: Prioritize earnings/financial report URLs
                url_lower = href.lower()
                is_relevant = (
                    'earnings' in url_lower or
                    'quarterly' in url_lower or
                    'annual' in url_lower or
                    'financial' in url_lower or
                    'report' in url_lower or
                    'results' in url_lower or
                    'investor' in url_lower
                )
                
                if not is_relevant:
                    continue  # Skip non-relevant links
                
                title = link.get_text(strip=True) or "IR Document"
                
                # Try to extract date
                published_at = None
                parent = link.find_parent()
                if parent:
                    text = parent.get_text()
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4}|Q[1-4]\s+\d{4})', text)
                    if date_match:
                        try:
                            dt = dateparser.parse(date_match.group(1))
                            if dt and dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            published_at = dt
                        except Exception:
                            pass
                
                items.append({
                    "url": href,
                    "title": title,
                    "source": "investor_relations",
                    "published_at": published_at.isoformat() if published_at else None,
                    "priority": 1,  # Highest priority
                    "is_pdf": is_pdf_url(href)
                })
                
                if len(items) >= self.max_per_source:
                    break
            
            return items
        except Exception as e:
            raise Exception(f"Failed to scrape IR page {url}: {e}")
    
    # ==========================================================================
    # EARNINGS REPORTS DISCOVERY (NEW - PRIORITY 2)
    # ==========================================================================
    
    def _discover_earnings_reports(self) -> List[Dict]:
        """
        Discover earnings reports (PDFs) - PRIORITY 2.
        
        Focuses on quarterly/annual financial reports.
        """
        sources = []
        
        # Auto-discover earnings pages
        candidates = build_earnings_report_candidates(self.domain)
        
        for candidate_url in candidates[:8]:  # Check top 8
            try:
                response = requests.head(candidate_url, headers=HEADERS, timeout=5, allow_redirects=True)
                
                if response.status_code < 400:
                    print(f"   ✓ Found earnings page: {candidate_url}")
                    items = self._scrape_earnings_index(candidate_url)
                    sources.extend(items)
                    
                    if items:
                        return sources  # Found earnings page, stop
            except Exception:
                continue
        
        return sources
    
    def _scrape_earnings_index(self, url: str) -> List[Dict]:
        """Scrape earnings report index page."""
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            items = []
            
            for link in soup.find_all("a", href=True):
                href = link.get("href", "").strip()
                if not href:
                    continue
                
                # Make absolute URL
                if not href.startswith("http"):
                    href = urljoin(url, href)
                
                if not is_valid_url(href):
                    continue
                
                # Prioritize PDFs and earnings-related links
                url_lower = href.lower()
                is_earnings = (
                    is_pdf_url(href) or
                    'earnings' in url_lower or
                    'quarterly' in url_lower or
                    'q1' in url_lower or 'q2' in url_lower or 'q3' in url_lower or 'q4' in url_lower or
                    'fy20' in url_lower or 'fy21' in url_lower or 'fy22' in url_lower or 
                    'fy23' in url_lower or 'fy24' in url_lower or 'fy25' in url_lower or 'fy26' in url_lower
                )
                
                if not is_earnings:
                    continue
                
                title = link.get_text(strip=True) or "Earnings Report"
                
                items.append({
                    "url": href,
                    "title": title,
                    "source": "earnings_report",
                    "published_at": None,
                    "priority": 2,
                    "is_pdf": is_pdf_url(href)
                })
                
                if len(items) >= self.max_per_source:
                    break
            
            return items
        except Exception as e:
            raise Exception(f"Failed to scrape earnings page {url}: {e}")
    
    # ==========================================================================
    # DIRECT NEWSROOM DISCOVERY (UPDATED - PRIORITY 3)
    # ==========================================================================
    
    def _discover_direct_newsroom(self) -> List[Dict]:
        """
        Discover company newsroom DIRECTLY (no Google News proxy).
        
        Tries:
        1. RSS/Atom feeds from newsroom
        2. Direct scraping of newsroom index
        """
        sources = []
        
        # If newsroom URL provided, use it
        if self.newsroom_url:
            try:
                items = self._scrape_newsroom_rss_or_index(self.newsroom_url)
                sources.extend(items)
                return sources
            except Exception as e:
                print(f"   ⚠️  Provided newsroom URL failed: {e}")
        
        # Auto-discover newsroom
        candidates = build_newsroom_candidates(self.domain)
        
        for candidate_url in candidates[:6]:  # Check top 6
            try:
                response = requests.head(candidate_url, headers=HEADERS, timeout=5, allow_redirects=True)
                
                if response.status_code < 400:
                    print(f"   ✓ Found newsroom: {candidate_url}")
                    items = self._scrape_newsroom_rss_or_index(candidate_url)
                    sources.extend(items)
                    
                    if items:
                        return sources  # Found newsroom, stop
            except Exception:
                continue
        
        return sources
    
    def _scrape_newsroom_rss_or_index(self, url: str) -> List[Dict]:
        """Try RSS first, fall back to HTML scraping."""
        # Try to find RSS/Atom feed
        rss_candidates = [
            f"{url}/rss",
            f"{url}/feed",
            f"{url}/rss.xml",
            f"{url}/feed.xml",
            f"{url}/atom.xml",
        ]
        
        for rss_url in rss_candidates:
            try:
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    print(f"      ✓ Found RSS feed: {rss_url}")
                    return self._parse_newsroom_rss(feed)
            except Exception:
                continue
        
        # Fallback: HTML scraping
        return self._scrape_newsroom_index(url)
    
    def _parse_newsroom_rss(self, feed) -> List[Dict]:
        """Parse newsroom RSS feed."""
        items = []
        
        for entry in feed.entries[:self.max_per_source]:
            link = entry.get("link", "")
            if not link:
                continue
            
            title = entry.get("title", "").strip() or "News"
            
            # Parse date
            published_at = None
            for date_field in ("published", "updated"):
                if date_field in entry:
                    try:
                        dt = dateparser.parse(entry[date_field])
                        if dt and dt.tzinfo is None:
                            dt = dt.replace(tzinfo=timezone.utc)
                        published_at = dt
                        break
                    except Exception:
                        continue
            
            items.append({
                "url": link,
                "title": title,
                "source": "newsroom_rss",
                "published_at": published_at.isoformat() if published_at else None,
                "priority": 3
            })
        
        return items
    
    # ==========================================================================
    # BING NEWS DISCOVERY (NEW - PRIORITY 4 - FALLBACK)
    # ==========================================================================
    
    def _discover_bing_news(self) -> List[Dict]:
        """
        Discover via Bing News RSS (FALLBACK ONLY).
        
        Better than Google News because:
        - Direct URLs (no proxy/redirect)
        - Better filtering
        - Scrapeable
        """
        sources = []
        
        # Bing News RSS doesn't exist publicly like Google News
        # Instead, we'll use Bing's regular RSS which gives better URLs
        # For now, return empty (can implement if needed)
        
        return sources
    
    # ==========================================================================
    # NEWSROOM DISCOVERY (OLD METHOD - KEPT FOR COMPATIBILITY)
    # ==========================================================================
    
    def _discover_newsroom(self) -> List[Dict]:
        """OLD METHOD - Use _discover_direct_newsroom() instead."""
        return self._discover_direct_newsroom()
    
    def _scrape_newsroom_index(self, url: str) -> List[Dict]:
        """Scrape newsroom index page for article links."""
        try:
            response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            items = []
            
            # Find all links
            for link in soup.find_all("a", href=True):
                href = link.get("href", "").strip()
                if not href:
                    continue
                
                # Make absolute URL
                if not href.startswith("http"):
                    href = urljoin(url, href)
                
                # Filter: Must be from same domain and look like article
                if not is_valid_url(href):
                    continue
                
                domain = extract_domain(href)
                if domain != extract_domain(url):
                    continue  # External link
                
                # Get title
                title = link.get_text(strip=True) or "News Article"
                
                # Try to find date (naive approach)
                published_at = None
                # Look for nearby date indicators
                parent = link.find_parent()
                if parent:
                    text = parent.get_text()
                    # Simple regex for dates like 2024-01-19 or 19.01.2024
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4})', text)
                    if date_match:
                        try:
                            dt = dateparser.parse(date_match.group(1))
                            if dt and dt.tzinfo is None:
                                dt = dt.replace(tzinfo=timezone.utc)
                            published_at = dt
                        except Exception:
                            pass
                
                items.append({
                    "url": href,
                    "title": title,
                    "source": "newsroom",
                    "published_at": published_at.isoformat() if published_at else None
                })
                
                if len(items) >= self.max_per_source:
                    break
            
            return items
        except Exception as e:
            raise Exception(f"Failed to scrape newsroom {url}: {e}")
    
    # ==========================================================================
    # ENRICHMENT
    # ==========================================================================
    
    def enrich_sources(self, sources: List[Dict]) -> List[Dict]:
        """
        Enrich sources with full text content.
        
        UPDATED: Now handles PDFs as well as HTML pages.
        
        Args:
            sources: List of source dicts
        
        Returns:
            List of enriched source dicts with additional keys:
                - raw_text: Full article text (or empty if failed)
                - text_hash: SHA256 hash (if text available)
                - is_eu_source: bool
                - has_ecommerce_keywords: bool (if text available)
                - fetch_timestamp: ISO timestamp
                - http_status_code: int (if succeeded)
                - enrich_error: str (if failed)
                - is_pdf: bool
                - is_earnings_report: bool (if PDF)
        """
        enriched = []
        success_count = 0
        
        print(f"\n📄 Enriching {len(sources)} sources...")
        
        for i, source in enumerate(sources, 1):
            url = source["url"]
            is_pdf = source.get("is_pdf", False) or is_pdf_url(url)
            
            try:
                # CASE 1: PDF Document
                if is_pdf:
                    print(f"   📄 Processing PDF: {url[:60]}...")
                    text = extract_text_from_pdf_url(url, timeout=TIMEOUT)
                    
                    if text and len(text) >= 50:
                        source["raw_text"] = text
                        source["text_hash"] = hash_text(text)
                        source["is_pdf"] = True
                        source["is_earnings_report"] = is_earnings_report_pdf(text)
                        source["has_ecommerce_keywords"] = self._has_ecommerce_keywords(text)
                        success_count += 1
                    else:
                        source["raw_text"] = text or ""
                        source["enrich_error"] = "PDF parsing failed or text too short"
                        source["is_pdf"] = True
                
                # CASE 2: HTML Page
                else:
                    response = requests.get(
                        url, 
                        headers=HEADERS, 
                        timeout=TIMEOUT,
                        allow_redirects=True
                    )
                    response.raise_for_status()
                    
                    # Store final URL after redirects
                    final_url = response.url
                    if final_url != url:
                        source["final_url"] = final_url
                    
                    # Extract main content
                    text = self._extract_article_text(response.text)
                    
                    if len(text) >= 50:
                        source["raw_text"] = text
                        source["text_hash"] = hash_text(text)
                        source["has_ecommerce_keywords"] = self._has_ecommerce_keywords(text)
                        success_count += 1
                    else:
                        source["raw_text"] = text
                        source["enrich_error"] = f"Text too short ({len(text)} chars)"
                    
                    source["http_status_code"] = response.status_code
                
                source["is_eu_source"] = is_eu_url(url)
                source["fetch_timestamp"] = datetime.now(timezone.utc).isoformat()
                enriched.append(source)
                
                if i % 10 == 0:
                    print(f"   {i}/{len(sources)} processed...")
                
                # Rate limiting
                time.sleep(0.3)
                
            except Exception as e:
                source["raw_text"] = ""
                source["enrich_error"] = str(e)[:200]
                source["fetch_timestamp"] = datetime.now(timezone.utc).isoformat()
                enriched.append(source)
                print(f"   ✗ Error {url[:60]}: {str(e)[:50]}")
        
        print(f"✅ Enriched {success_count}/{len(sources)} sources successfully")
        print(f"   Kept {len(enriched)} total sources (including failures)")
        
        return enriched
    
    def _extract_article_text(self, html: str) -> str:
        """Extract main article text from HTML."""
        try:
            # Try readability first (FIXED import!)
            from readability.readability import Document
            doc = Document(html)
            article_html = doc.summary(html_partial=True)
            
            soup = BeautifulSoup(article_html, "html.parser")
            # Remove script/style
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            
            text = soup.get_text(separator=" ", strip=True)
        except Exception:
            # Fallback: simple extraction
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = soup.get_text(separator=" ", strip=True)
        
        # Clean whitespace
        text = clean_whitespace(text)
        
        return text
    
    # ==========================================================================
    # HELPERS
    # ==========================================================================
    
    def _deduplicate_sources(self, sources: List[Dict]) -> List[Dict]:
        """Deduplicate sources by normalized URL."""
        seen = set()
        deduplicated = []
        
        for source in sources:
            url_normalized = normalize_url(source["url"])
            if url_normalized not in seen:
                seen.add(url_normalized)
                deduplicated.append(source)
        
        return deduplicated
    
    def _has_ecommerce_keywords(self, text: str) -> bool:
        """Check if text contains e-commerce keywords."""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in ECOMMERCE_KEYWORDS)
    
    def get_stats(self) -> Dict:
        """Get discovery statistics."""
        return self.stats.copy()


# ==============================================================================
# CONVENIENCE FUNCTIONS
# ==============================================================================

def discover_company_sources(company_name: str, config: Optional[Dict] = None) -> List[Dict]:
    """
    Convenience function: Discover sources for a company.
    
    Args:
        company_name: Company name
        config: Optional configuration
    
    Returns:
        List of discovered sources
    """
    scraper = CompanyIntelligenceScraper(company_name, config)
    return scraper.discover_all_sources()


def discover_and_enrich(company_name: str, config: Optional[Dict] = None) -> List[Dict]:
    """
    Convenience function: Discover and enrich sources in one go.
    
    Args:
        company_name: Company name
        config: Optional configuration
    
    Returns:
        List of enriched sources
    """
    scraper = CompanyIntelligenceScraper(company_name, config)
    sources = scraper.discover_all_sources()
    enriched = scraper.enrich_sources(sources)
    return enriched
