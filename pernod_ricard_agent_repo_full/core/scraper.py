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
    is_valid_url,
    extract_domain
)
from utils.text_utils import hash_text, clean_whitespace, remove_html_tags


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
            "google_news": 0,
            "linkedin": 0,
            "newsroom": 0,
            "errors": []
        }
    
    # ==========================================================================
    # MAIN ORCHESTRATOR
    # ==========================================================================
    
    def discover_all_sources(self) -> List[Dict]:
        """
        Discover sources from all available channels.
        
        Returns:
            List of source dicts with keys:
                - url: Source URL
                - title: Article title
                - source: Source type (e.g. "gnews:de:DE")
                - published_at: ISO timestamp (optional)
        """
        all_sources = []
        
        print(f"\n🔍 Discovering sources for: {self.company_name}")
        print(f"   Domain: {self.domain}")
        print(f"   Lookback: {self.lookback_days} days")
        
        # 1. Google News (EU editions + E-Commerce)
        print("\n📰 Google News...")
        try:
            gnews_sources = self._discover_google_news()
            all_sources.extend(gnews_sources)
            self.stats["google_news"] = len(gnews_sources)
            print(f"   ✓ Found {len(gnews_sources)} items")
        except Exception as e:
            error_msg = f"Google News failed: {e}"
            print(f"   ✗ {error_msg}")
            self.stats["errors"].append(error_msg)
        
        # 2. LinkedIn (via Google News site: search)
        print("\n💼 LinkedIn...")
        try:
            linkedin_sources = self._discover_linkedin()
            all_sources.extend(linkedin_sources)
            self.stats["linkedin"] = len(linkedin_sources)
            print(f"   ✓ Found {len(linkedin_sources)} items")
        except Exception as e:
            error_msg = f"LinkedIn discovery failed: {e}"
            print(f"   ✗ {error_msg}")
            self.stats["errors"].append(error_msg)
        
        # 3. Newsroom (auto-discovery or provided URL)
        print("\n🏢 Newsroom...")
        try:
            newsroom_sources = self._discover_newsroom()
            all_sources.extend(newsroom_sources)
            self.stats["newsroom"] = len(newsroom_sources)
            print(f"   ✓ Found {len(newsroom_sources)} items")
        except Exception as e:
            error_msg = f"Newsroom discovery failed: {e}"
            print(f"   ✗ {error_msg}")
            self.stats["errors"].append(error_msg)
        
        # Deduplicate by URL
        all_sources = self._deduplicate_sources(all_sources)
        
        print(f"\n✅ Total sources discovered: {len(all_sources)}")
        print(f"   Google News: {self.stats['google_news']}")
        print(f"   LinkedIn: {self.stats['linkedin']}")
        print(f"   Newsroom: {self.stats['newsroom']}")
        
        if self.stats["errors"]:
            print(f"\n⚠️  Errors encountered: {len(self.stats['errors'])}")
            for err in self.stats["errors"][:3]:  # Show first 3
                print(f"   - {err}")
        
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
    # NEWSROOM DISCOVERY
    # ==========================================================================
    
    def _discover_newsroom(self) -> List[Dict]:
        """Discover company newsroom (auto-detect or use provided URL)."""
        sources = []
        
        # If newsroom URL provided, use it
        if self.newsroom_url:
            try:
                items = self._scrape_newsroom_index(self.newsroom_url)
                sources.extend(items)
                return sources
            except Exception as e:
                print(f"   ⚠️  Provided newsroom URL failed: {e}")
        
        # Auto-discover newsroom
        candidates = build_newsroom_candidates(self.domain)
        
        for candidate_url in candidates:
            try:
                # Quick check if URL exists
                response = requests.head(candidate_url, headers=HEADERS, timeout=5, allow_redirects=True)
                
                if response.status_code < 400:
                    print(f"   ✓ Found newsroom: {candidate_url}")
                    items = self._scrape_newsroom_index(candidate_url)
                    sources.extend(items)
                    return sources  # Found one, stop searching
            except Exception:
                continue  # Try next candidate
        
        # No newsroom found
        print(f"   ℹ️  No newsroom found for {self.domain}")
        return []
    
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
        
        Args:
            sources: List of source dicts
        
        Returns:
            List of enriched source dicts with additional keys:
                - raw_text: Full article text
                - text_hash: SHA256 hash
                - is_eu_source: bool
                - has_ecommerce_keywords: bool
                - fetch_timestamp: ISO timestamp
                - http_status_code: int
        """
        enriched = []
        
        print(f"\n📄 Enriching {len(sources)} sources...")
        
        for i, source in enumerate(sources, 1):
            url = source["url"]
            
            try:
                # Fetch full page
                response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
                response.raise_for_status()
                html = response.text
                
                # Extract main content
                text = self._extract_article_text(html)
                
                # Skip if too short
                if len(text) < 200:
                    continue
                
                # Enrich
                source["raw_text"] = text
                source["text_hash"] = hash_text(text)
                source["is_eu_source"] = is_eu_url(url)
                source["has_ecommerce_keywords"] = self._has_ecommerce_keywords(text)
                source["fetch_timestamp"] = datetime.now(timezone.utc).isoformat()
                source["http_status_code"] = response.status_code
                
                enriched.append(source)
                
                if i % 10 == 0:
                    print(f"   {i}/{len(sources)} enriched...")
                
                # Rate limiting (be nice)
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ✗ Failed to enrich {url}: {e}")
                continue
        
        print(f"✅ Enriched {len(enriched)}/{len(sources)} sources")
        
        return enriched
    
    def _extract_article_text(self, html: str) -> str:
        """Extract main article text from HTML."""
        try:
            # Try readability first
            from readability import Document
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
