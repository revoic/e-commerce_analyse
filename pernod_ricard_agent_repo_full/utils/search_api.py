"""
Google Custom Search API Integration
Uses Google's Custom Search JSON API to find relevant sources.
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class GoogleSearchClient:
    """
    Client for Google Custom Search API.
    Finds relevant investor relations pages, earnings reports, and news.
    """
    
    def __init__(self):
        """Initialize the Google Search client."""
        self.api_key = os.getenv('GOOGLE_SEARCH_API')
        self.search_engine_id = os.getenv('SEARCH_ENGINE_ID')
        
        if not self.api_key or not self.search_engine_id:
            logger.warning("Google Search API credentials not found. Search features will be limited.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("Google Search API initialized successfully")
        
        # Try to import google api client
        try:
            from googleapiclient.discovery import build
            self.build = build
        except ImportError:
            logger.warning("google-api-python-client not installed. Search features disabled.")
            self.enabled = False
    
    def search(self, query: str, num_results: int = 10, **kwargs) -> List[Dict]:
        """
        Perform a Google search and return results.
        
        Args:
            query: Search query string
            num_results: Number of results to return (max 10 per request)
            **kwargs: Additional parameters for the search
        
        Returns:
            List of search results with title, link, snippet
        """
        if not self.enabled:
            logger.warning("Google Search API not enabled, returning empty results")
            return []
        
        try:
            # Build the search service
            service = self.build("customsearch", "v1", developerKey=self.api_key)
            
            # Execute the search
            result = service.cse().list(
                q=query,
                cx=self.search_engine_id,
                num=min(num_results, 10),  # API max is 10 per request
                **kwargs
            ).execute()
            
            # Extract search results
            items = result.get('items', [])
            
            search_results = []
            for item in items:
                search_results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'displayLink': item.get('displayLink', '')
                })
            
            logger.info(f"Google Search: '{query}' returned {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Google Search error for query '{query}': {e}")
            return []
    
    def search_investor_relations(self, company: str, domain_hint: Optional[str] = None) -> List[Dict]:
        """
        Search for investor relations pages for a company.
        
        Args:
            company: Company name
            domain_hint: Optional domain hint (e.g., "zalando.com")
        
        Returns:
            List of relevant IR pages
        """
        queries = [
            f'"{company}" investor relations',
            f'"{company}" IR website',
            f'"{company}" shareholder information',
        ]
        
        # Add domain-specific query if hint provided
        if domain_hint:
            queries.insert(0, f'site:{domain_hint} investor relations')
        
        all_results = []
        for query in queries[:2]:  # Limit to 2 queries to save API calls
            results = self.search(query, num_results=5)
            all_results.extend(results)
            if results:  # If we found something, don't need more queries
                break
        
        # Deduplicate by link
        seen_links = set()
        unique_results = []
        for result in all_results:
            if result['link'] not in seen_links:
                seen_links.add(result['link'])
                unique_results.append(result)
        
        return unique_results[:10]
    
    def search_earnings_reports(self, company: str, year: Optional[int] = None) -> List[Dict]:
        """
        Search for earnings reports for a company.
        
        Args:
            company: Company name
            year: Optional year to search for (defaults to current year)
        
        Returns:
            List of relevant earnings report pages/PDFs
        """
        if year is None:
            year = datetime.now().year
        
        queries = [
            f'"{company}" earnings report {year}',
            f'"{company}" quarterly results {year}',
            f'"{company}" financial results {year} filetype:pdf',
        ]
        
        all_results = []
        for query in queries[:2]:  # Limit to 2 queries
            results = self.search(query, num_results=5)
            all_results.extend(results)
        
        # Deduplicate
        seen_links = set()
        unique_results = []
        for result in all_results:
            if result['link'] not in seen_links:
                seen_links.add(result['link'])
                unique_results.append(result)
        
        return unique_results[:10]
    
    def search_ecommerce_news(self, company: str, months_back: int = 3) -> List[Dict]:
        """
        Search for recent e-commerce news about a company.
        
        Args:
            company: Company name
            months_back: How many months back to search
        
        Returns:
            List of relevant news articles
        """
        queries = [
            f'"{company}" e-commerce revenue growth',
            f'"{company}" online sales {datetime.now().year}',
            f'"{company}" digital commerce strategy',
        ]
        
        all_results = []
        for query in queries[:2]:  # Limit queries
            results = self.search(
                query, 
                num_results=5,
                dateRestrict=f'm{months_back}'  # Last N months
            )
            all_results.extend(results)
        
        # Deduplicate
        seen_links = set()
        unique_results = []
        for result in all_results:
            if result['link'] not in seen_links:
                seen_links.add(result['link'])
                unique_results.append(result)
        
        return unique_results[:15]
    
    def search_company_website(self, company: str) -> Optional[str]:
        """
        Find the main website for a company.
        
        Args:
            company: Company name
        
        Returns:
            Main website URL or None
        """
        results = self.search(f'"{company}" official website', num_results=3)
        
        if results:
            # Return the first result's display link (domain)
            return results[0].get('displayLink', None)
        
        return None
