"""
Tests for CompanyIntelligenceScraper.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scraper import CompanyIntelligenceScraper, discover_company_sources
from utils.url_utils import guess_domain_from_company_name, is_eu_url, normalize_url


# ==============================================================================
# DOMAIN GUESSING TESTS
# ==============================================================================

def test_domain_guessing():
    """Test domain guessing from company names."""
    test_cases = [
        ("Coca-Cola", "coca-cola.com"),
        ("Coca Cola", "coca-cola.com"),
        ("Unilever", "unilever.com"),
        ("LVMH", "lvmh.com"),
        ("Deutsche Post DHL", "dhl.com"),
        ("Zalando SE", "zalando.com"),
        ("Nestlé AG", "nestle.com"),
    ]
    
    for company_name, expected_domain in test_cases:
        result = guess_domain_from_company_name(company_name)
        assert result == expected_domain, f"{company_name} → {result}, expected {expected_domain}"


def test_domain_guessing_special_chars():
    """Test domain guessing with special characters."""
    assert "muller" in guess_domain_from_company_name("Müller").lower()
    assert "kase" in guess_domain_from_company_name("Käse GmbH").lower()


# ==============================================================================
# URL UTILITIES TESTS
# ==============================================================================

def test_url_normalization():
    """Test URL normalization for deduplication."""
    # Same URL, different orders of query params
    url1 = "https://example.com/article?id=123&source=news"
    url2 = "https://example.com/article?source=news&id=123"
    
    assert normalize_url(url1) == normalize_url(url2)


def test_url_normalization_trailing_slash():
    """Test trailing slash removal."""
    url1 = "https://example.com/article/"
    url2 = "https://example.com/article"
    
    assert normalize_url(url1) == normalize_url(url2)


def test_eu_url_detection():
    """Test EU domain detection."""
    eu_urls = [
        "https://example.de/article",
        "https://example.fr/article",
        "https://www.example.co.uk/article",
        "https://news.at/article",
    ]
    
    non_eu_urls = [
        "https://example.com/article",
        "https://example.us/article",
        "https://news.cn/article",
    ]
    
    for url in eu_urls:
        assert is_eu_url(url), f"{url} should be EU"
    
    for url in non_eu_urls:
        assert not is_eu_url(url), f"{url} should not be EU"


# ==============================================================================
# SCRAPER INITIALIZATION TESTS
# ==============================================================================

def test_scraper_initialization():
    """Test scraper initialization."""
    scraper = CompanyIntelligenceScraper("Coca-Cola")
    
    assert scraper.company_name == "Coca-Cola"
    assert scraper.domain == "coca-cola.com"
    assert scraper.lookback_days == 14  # default
    assert scraper.max_per_source == 10  # default


def test_scraper_initialization_with_config():
    """Test scraper initialization with custom config."""
    config = {
        "domain": "custom.com",
        "lookback_days": 30,
        "max_per_source": 20,
        "newsroom_url": "https://custom.com/news"
    }
    
    scraper = CompanyIntelligenceScraper("Test Company", config)
    
    assert scraper.domain == "custom.com"
    assert scraper.lookback_days == 30
    assert scraper.max_per_source == 20
    assert scraper.newsroom_url == "https://custom.com/news"


# ==============================================================================
# GOOGLE NEWS URL BUILDING TESTS
# ==============================================================================

def test_gnews_url_building():
    """Test Google News URL construction."""
    scraper = CompanyIntelligenceScraper("Test Company", {"lookback_days": 7})
    
    url = scraper._build_gnews_url("Test Company", "de", "DE", "DE:de")
    
    assert "news.google.com/rss/search" in url
    assert "Test+Company" in url or "Test%20Company" in url
    assert "when:7d" in url
    assert "hl=de" in url
    assert "gl=DE" in url


# ==============================================================================
# DEDUPLICATION TESTS
# ==============================================================================

def test_source_deduplication():
    """Test source deduplication by URL."""
    sources = [
        {"url": "https://example.com/article?id=1", "title": "Article 1"},
        {"url": "https://example.com/article?id=1", "title": "Article 1 Duplicate"},
        {"url": "https://example.com/article?id=2", "title": "Article 2"},
    ]
    
    scraper = CompanyIntelligenceScraper("Test")
    deduplicated = scraper._deduplicate_sources(sources)
    
    # Should have 2 unique URLs
    assert len(deduplicated) == 2
    assert deduplicated[0]["url"] != deduplicated[1]["url"]


# ==============================================================================
# E-COMMERCE KEYWORD DETECTION TESTS
# ==============================================================================

def test_ecommerce_keyword_detection():
    """Test e-commerce keyword detection."""
    scraper = CompanyIntelligenceScraper("Test")
    
    # Texts with e-commerce keywords
    ecom_texts = [
        "Company expands e-commerce operations",
        "New marketplace strategy announced",
        "Amazon partnership for retail media",
        "D2C sales increased by 30%",
        "Onlinehandel wächst stark",
    ]
    
    # Texts without e-commerce keywords
    non_ecom_texts = [
        "Company opens new factory",
        "CEO appointed",
        "Quarterly earnings announced",
    ]
    
    for text in ecom_texts:
        assert scraper._has_ecommerce_keywords(text), f"Should detect e-commerce in: {text}"
    
    for text in non_ecom_texts:
        assert not scraper._has_ecommerce_keywords(text), f"Should not detect e-commerce in: {text}"


# ==============================================================================
# INTEGRATION TESTS (require network, mark as slow)
# ==============================================================================

@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("RUN_INTEGRATION_TESTS"), reason="Integration tests disabled")
def test_discover_sources_real():
    """Integration test: Discover real sources for Coca-Cola."""
    sources = discover_company_sources("Coca-Cola", {"lookback_days": 7, "max_per_source": 5})
    
    # Should find at least some sources
    assert len(sources) > 0, "Should discover at least one source"
    
    # Check source structure
    first_source = sources[0]
    assert "url" in first_source
    assert "title" in first_source
    assert "source" in first_source


@pytest.mark.slow
@pytest.mark.skipif(not os.getenv("RUN_INTEGRATION_TESTS"), reason="Integration tests disabled")
def test_discover_sources_unknown_company():
    """Integration test: Discover sources for unknown company (should handle gracefully)."""
    sources = discover_company_sources("XYZ Nonexistent Company 12345", {"lookback_days": 7, "max_per_source": 2})
    
    # Should not crash, might find 0 sources
    assert isinstance(sources, list)


# ==============================================================================
# STATS TESTS
# ==============================================================================

def test_stats_initialization():
    """Test statistics tracking initialization."""
    scraper = CompanyIntelligenceScraper("Test")
    stats = scraper.get_stats()
    
    assert "google_news" in stats
    assert "linkedin" in stats
    assert "newsroom" in stats
    assert "errors" in stats
    assert stats["google_news"] == 0
    assert stats["errors"] == []


# ==============================================================================
# RUN TESTS
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
