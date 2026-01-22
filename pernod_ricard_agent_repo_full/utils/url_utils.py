"""
URL utilities: domain guessing, normalization, EU detection.
"""

import re
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from typing import Optional


# EU country TLDs
EU_TLDS = (
    ".de", ".at", ".ch", ".fr", ".it", ".es", ".nl", ".se", ".pl",
    ".dk", ".no", ".fi", ".ie", ".uk", ".eu", ".be", ".pt", ".cz",
    ".ro", ".gr", ".hu", ".sk", ".bg", ".hr", ".lt", ".lv", ".ee",
    ".si", ".cy", ".lu", ".mt"
)


def guess_domain_from_company_name(company_name: str) -> str:
    """
    Guess domain from company name.
    
    Examples:
        "Coca-Cola" → "coca-cola.com"
        "Deutsche Post DHL" → "dhl.com"
        "Zalando SE" → "zalando.com"
    
    Args:
        company_name: Company name (e.g. "Coca-Cola")
    
    Returns:
        Guessed domain (e.g. "coca-cola.com")
    """
    # Clean name
    name = company_name.lower().strip()
    
    # Remove common suffixes
    suffixes = [" se", " ag", " gmbh", " inc", " corp", " ltd", " llc", 
                " s.a.", " n.v.", " b.v.", " plc", " group"]
    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)].strip()
    
    # Remove special characters, keep hyphens and spaces
    name = re.sub(r'[^a-z0-9\s\-]', '', name)
    
    # Replace spaces with hyphens
    name = name.replace(' ', '-')
    
    # Remove consecutive hyphens
    name = re.sub(r'-+', '-', name)
    
    # Remove leading/trailing hyphens
    name = name.strip('-')
    
    # Special cases (known brands)
    special_cases = {
        "deutsche-post-dhl": "dhl.com",
        "deutsche-post": "dhl.com",
        "dhl": "dhl.com",
        "coca-cola": "coca-cola.com",
        "cocacola": "coca-cola.com",
        "unilever": "unilever.com",
        "nestle": "nestle.com",
        "lvmh": "lvmh.com",
        "pernod-ricard": "pernod-ricard.com",
        "zalando": "zalando.com",
        "amazon": "amazon.com",
        "google": "google.com",
        "microsoft": "microsoft.com",
        "apple": "apple.com",
    }
    
    if name in special_cases:
        return special_cases[name]
    
    # Default: add .com
    return f"{name}.com"


def normalize_url(url: str) -> str:
    """
    Normalize URL for deduplication.
    
    - Lowercase
    - Sort query parameters
    - Remove trailing slash
    - Remove fragments
    
    Args:
        url: URL to normalize
    
    Returns:
        Normalized URL
    """
    try:
        parsed = urlparse(url.lower())
        
        # Sort query parameters
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        sorted_query = urlencode(sorted(query_params))
        
        # Remove trailing slash from path
        path = parsed.path.rstrip('/') if parsed.path else ''
        
        # Rebuild without fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            path,
            parsed.params,
            sorted_query,
            ''  # No fragment
        ))
        
        return normalized
    except Exception:
        return url.lower()


def is_eu_url(url: str) -> bool:
    """
    Check if URL is from EU domain.
    
    Args:
        url: URL to check
    
    Returns:
        True if EU domain, False otherwise
    """
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        
        # Remove port if present
        if ':' in netloc:
            netloc = netloc.split(':')[0]
        
        # Check TLD
        return any(netloc.endswith(tld) for tld in EU_TLDS)
    except Exception:
        return False


def extract_domain(url: str) -> Optional[str]:
    """
    Extract domain from URL.
    
    Args:
        url: URL to extract from
    
    Returns:
        Domain (e.g. "example.com") or None
    """
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        
        # Remove port
        if ':' in netloc:
            netloc = netloc.split(':')[0]
        
        # Remove www.
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        
        return netloc
    except Exception:
        return None


def build_newsroom_candidates(domain: str) -> list[str]:
    """
    Generate candidate URLs for company newsroom.
    
    Args:
        domain: Company domain (e.g. "coca-cola.com")
    
    Returns:
        List of candidate URLs to try
    """
    # Common newsroom patterns
    paths = [
        "/news",
        "/newsroom",
        "/press",
        "/media",
        "/press-releases",
        "/en/news",
        "/en/newsroom",
        "/en/media",
        "/de/news",
        "/de/presse",
        "/about/news",
        "/company/news",
    ]
    
    candidates = []
    
    # Try with https
    for path in paths:
        candidates.append(f"https://{domain}{path}")
        candidates.append(f"https://www.{domain}{path}")
    
    return candidates


def build_investor_relations_candidates(domain: str) -> list[str]:
    """
    Generate candidate URLs for investor relations pages.
    
    These pages typically have earnings reports, financial data,
    and quarterly/annual reports.
    
    Args:
        domain: Company domain (e.g. "coca-cola.com")
    
    Returns:
        List of candidate URLs to try (prioritized)
    """
    # Common IR patterns (prioritized by likelihood)
    paths = [
        "/investor-relations",
        "/investors",
        "/ir",
        "/en/investor-relations",
        "/en/investors",
        "/about/investor-relations",
        "/company/investors",
        "/investor",
        "/shareholder",
        "/de/investor-relations",
        "/de/investoren",
        "/finance",
        "/financial-reports",
    ]
    
    candidates = []
    
    # Try with https (both with and without www)
    for path in paths:
        candidates.append(f"https://{domain}{path}")
        candidates.append(f"https://www.{domain}{path}")
    
    # Some companies use ir. subdomain
    candidates.insert(0, f"https://ir.{domain}")
    candidates.insert(1, f"https://investors.{domain}")
    
    return candidates


def build_earnings_report_candidates(domain: str) -> list[str]:
    """
    Generate candidate URLs for earnings/quarterly reports.
    
    Args:
        domain: Company domain (e.g. "coca-cola.com")
    
    Returns:
        List of candidate URLs to try
    """
    paths = [
        "/investor-relations/financial-reports",
        "/investors/financial-reports",
        "/ir/financial-reports",
        "/investor-relations/quarterly-results",
        "/investors/quarterly-results",
        "/investor-relations/earnings",
        "/investors/earnings",
        "/en/investor-relations/reports",
        "/en/investors/reports",
        "/financial-calendar",
        "/earnings-releases",
    ]
    
    candidates = []
    
    for path in paths:
        candidates.append(f"https://{domain}{path}")
        candidates.append(f"https://www.{domain}{path}")
    
    # Subdomain variants
    candidates.insert(0, f"https://ir.{domain}/financial-reports")
    candidates.insert(1, f"https://ir.{domain}/quarterly-results")
    candidates.insert(2, f"https://investors.{domain}/reports")
    
    return candidates


def build_company_blog_candidates(domain: str) -> list[str]:
    """
    Generate candidate URLs for official company blogs.
    
    Args:
        domain: Company domain (e.g. "coca-cola.com")
    
    Returns:
        List of candidate URLs to try
    """
    paths = [
        "/blog",
        "/en/blog",
        "/de/blog",
        "/insights",
        "/stories",
        "/news-insights",
    ]
    
    candidates = []
    
    for path in paths:
        candidates.append(f"https://{domain}{path}")
        candidates.append(f"https://www.{domain}{path}")
    
    # Blog subdomain
    candidates.insert(0, f"https://blog.{domain}")
    
    return candidates


def is_linkedin_url(url: str) -> bool:
    """Check if URL is from LinkedIn."""
    try:
        netloc = urlparse(url).netloc.lower()
        return 'linkedin.com' in netloc
    except Exception:
        return False


def is_newsroom_url(url: str) -> bool:
    """
    Check if URL looks like a newsroom/press page.
    
    Args:
        url: URL to check
    
    Returns:
        True if likely newsroom, False otherwise
    """
    try:
        path = urlparse(url).path.lower()
        
        # Common newsroom indicators
        indicators = [
            '/news', '/newsroom', '/press', '/media',
            '/press-release', '/presse', '/aktuelles'
        ]
        
        return any(ind in path for ind in indicators)
    except Exception:
        return False


def is_investor_relations_url(url: str) -> bool:
    """
    Check if URL looks like an investor relations page.
    
    Args:
        url: URL to check
    
    Returns:
        True if likely IR page, False otherwise
    """
    try:
        url_lower = url.lower()
        parsed = urlparse(url_lower)
        path = parsed.path
        netloc = parsed.netloc
        
        # Subdomain indicators
        if netloc.startswith('ir.') or netloc.startswith('investors.'):
            return True
        
        # Path indicators
        ir_indicators = [
            '/investor', '/ir/', '/shareholder',
            '/financial-report', '/earnings', '/quarterly'
        ]
        
        return any(ind in path for ind in ir_indicators)
    except Exception:
        return False


def is_earnings_report_url(url: str) -> bool:
    """
    Check if URL looks like an earnings/financial report.
    
    Args:
        url: URL to check
    
    Returns:
        True if likely earnings report, False otherwise
    """
    try:
        url_lower = url.lower()
        
        # Path/query indicators
        earnings_indicators = [
            'earnings', 'quarterly', 'q1-', 'q2-', 'q3-', 'q4-',
            'financial-report', 'annual-report', 'fiscal-year',
            'results', 'fy20', 'fy21', 'fy22', 'fy23', 'fy24', 'fy25', 'fy26'
        ]
        
        return any(ind in url_lower for ind in earnings_indicators)
    except Exception:
        return False


def clean_url(url: str) -> str:
    """
    Clean URL for display purposes.
    
    - Remove tracking parameters
    - Shorten long URLs
    
    Args:
        url: URL to clean
    
    Returns:
        Cleaned URL
    """
    try:
        parsed = urlparse(url)
        
        # Remove tracking parameters
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'msclkid', '_ga', 'mc_cid', 'mc_eid'
        ]
        
        query_params = parse_qsl(parsed.query, keep_blank_values=True)
        filtered_params = [
            (k, v) for k, v in query_params
            if k.lower() not in tracking_params
        ]
        
        clean_query = urlencode(filtered_params) if filtered_params else ''
        
        cleaned = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            clean_query,
            ''
        ))
        
        return cleaned
    except Exception:
        return url


# ==============================================================================
# VALIDATION
# ==============================================================================

def is_valid_url(url: str) -> bool:
    """
    Check if URL is valid and well-formed.
    
    Args:
        url: URL to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        parsed = urlparse(url)
        return all([
            parsed.scheme in ('http', 'https'),
            parsed.netloc,
            '.' in parsed.netloc  # Has TLD
        ])
    except Exception:
        return False


def is_same_domain(url1: str, url2: str) -> bool:
    """
    Check if two URLs are from the same domain.
    
    Args:
        url1: First URL
        url2: Second URL
    
    Returns:
        True if same domain, False otherwise
    """
    try:
        domain1 = extract_domain(url1)
        domain2 = extract_domain(url2)
        return domain1 == domain2 and domain1 is not None
    except Exception:
        return False
