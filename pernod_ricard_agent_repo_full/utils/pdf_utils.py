"""
PDF parsing utilities for extracting text from earnings reports and PDFs.
"""

import io
import logging
from typing import Optional

try:
    import pdfplumber
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_content: bytes, max_pages: int = 50) -> Optional[str]:
    """
    Extract text from PDF content.
    
    Tries pdfplumber first (better quality), falls back to PyPDF2.
    
    Args:
        pdf_content: Raw PDF bytes
        max_pages: Maximum pages to process (to avoid huge files)
    
    Returns:
        Extracted text or None if failed
    """
    if not PDF_AVAILABLE:
        logger.warning("PDF parsing libraries not available")
        return None
    
    # Try pdfplumber first (better quality)
    try:
        text = _extract_with_pdfplumber(pdf_content, max_pages)
        if text and len(text.strip()) > 100:
            return text
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")
    
    # Fallback to PyPDF2
    try:
        text = _extract_with_pypdf2(pdf_content, max_pages)
        if text and len(text.strip()) > 100:
            return text
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {e}")
    
    return None


def _extract_with_pdfplumber(pdf_content: bytes, max_pages: int) -> Optional[str]:
    """Extract text using pdfplumber (preferred method)."""
    with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
        text_parts = []
        
        for page_num, page in enumerate(pdf.pages):
            if page_num >= max_pages:
                break
            
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return "\n\n".join(text_parts)


def _extract_with_pypdf2(pdf_content: bytes, max_pages: int) -> Optional[str]:
    """Extract text using PyPDF2 (fallback method)."""
    pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
    text_parts = []
    
    num_pages = min(len(pdf_reader.pages), max_pages)
    
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)
    
    return "\n\n".join(text_parts)


def is_pdf_url(url: str) -> bool:
    """
    Check if URL points to a PDF file.
    
    Args:
        url: URL to check
    
    Returns:
        True if likely PDF, False otherwise
    """
    url_lower = url.lower()
    return (
        url_lower.endswith('.pdf') or
        '.pdf?' in url_lower or
        '/pdf/' in url_lower or
        'filetype=pdf' in url_lower
    )


def extract_text_from_pdf_url(pdf_url: str, timeout: int = 30) -> Optional[str]:
    """
    Download and extract text from PDF URL.
    
    Args:
        pdf_url: URL to PDF file
        timeout: Request timeout in seconds
    
    Returns:
        Extracted text or None
    """
    import requests
    
    try:
        response = requests.get(
            pdf_url,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (compatible; E-Commerce-Intelligence-Bot/1.0)'
            },
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'pdf' not in content_type:
            logger.warning(f"URL did not return PDF: {content_type}")
            return None
        
        return extract_text_from_pdf(response.content)
    
    except Exception as e:
        logger.error(f"Failed to download/parse PDF from {pdf_url}: {e}")
        return None


def is_earnings_report_pdf(text: str) -> bool:
    """
    Check if PDF text looks like an earnings/financial report.
    
    Args:
        text: Extracted PDF text
    
    Returns:
        True if likely earnings report
    """
    if not text or len(text) < 200:
        return False
    
    text_lower = text.lower()
    
    # Keywords that indicate earnings/financial reports
    earnings_keywords = [
        'quarterly report', 'earnings', 'revenue', 'profit', 'loss',
        'financial results', 'quarterly results', 'q1', 'q2', 'q3', 'q4',
        'fiscal year', 'net income', 'operating income', 'ebitda',
        'sales growth', 'year-over-year', 'yoy', 'balance sheet',
        'cash flow', 'investor relations', 'ir', 'earnings call'
    ]
    
    # Check if at least 3 keywords present
    matches = sum(1 for kw in earnings_keywords if kw in text_lower)
    
    return matches >= 3


def extract_key_metrics_from_text(text: str) -> dict:
    """
    Extract key financial metrics from text (simple pattern matching).
    
    Args:
        text: Extracted text
    
    Returns:
        Dictionary with found metrics
    """
    import re
    
    metrics = {}
    
    # Simple patterns for common metrics
    patterns = {
        'revenue': r'revenue[:\s]+[\$€£]?(\d+(?:\.\d+)?)\s*(?:million|billion|m|b)',
        'growth': r'growth[:\s]+(\d+(?:\.\d+)?)\s*%',
        'ebitda': r'ebitda[:\s]+[\$€£]?(\d+(?:\.\d+)?)\s*(?:million|billion|m|b)',
    }
    
    for metric, pattern in patterns.items():
        matches = re.findall(pattern, text.lower())
        if matches:
            metrics[metric] = matches[0]
    
    return metrics
