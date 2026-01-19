"""
Text utilities: normalization, hashing, cleaning.
"""

import re
import hashlib
from typing import Optional


def normalize_text(text: str) -> str:
    """
    Normalize text for comparison and deduplication.
    
    - Lowercase
    - Normalize whitespace
    - Normalize quotes and dashes
    - Remove extra punctuation
    
    Args:
        text: Text to normalize
    
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Normalize whitespace (tabs, newlines → single space)
    text = re.sub(r'\s+', ' ', text)
    
    # Normalize quotes
    text = re.sub(r'[„""«»]', '"', text)
    text = re.sub(r'[‚''‹›]', "'", text)
    
    # Normalize dashes
    text = re.sub(r'[–—]', '-', text)
    
    # Normalize ellipsis
    text = text.replace('…', '...')
    
    # Remove zero-width characters
    text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
    
    # Strip
    return text.strip()


def hash_text(text: str) -> str:
    """
    Generate SHA256 hash of text.
    
    Args:
        text: Text to hash
    
    Returns:
        Hex digest (64 characters)
    """
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def hash_short(text: str) -> str:
    """
    Generate short hash (first 16 chars of SHA256).
    
    Args:
        text: Text to hash
    
    Returns:
        Short hash (16 characters)
    """
    return hash_text(text)[:16]


def clean_whitespace(text: str) -> str:
    """
    Clean excessive whitespace while preserving structure.
    
    Args:
        text: Text to clean
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Normalize line breaks (keep max 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove trailing/leading whitespace per line
    lines = [line.strip() for line in text.split('\n')]
    
    # Rejoin
    return '\n'.join(lines).strip()


def truncate(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """
    Truncate text to max length, adding suffix if truncated.
    
    Args:
        text: Text to truncate
        max_length: Maximum length (including suffix)
        suffix: Suffix to add if truncated
    
    Returns:
        Truncated text
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def extract_numbers(text: str) -> list[float]:
    """
    Extract all numbers from text.
    
    Args:
        text: Text to extract from
    
    Returns:
        List of numbers found
    """
    # Pattern matches: 123, 123.45, 123,45, 1,234.56
    pattern = r'\d+(?:[.,]\d+)*'
    
    numbers = []
    for match in re.finditer(pattern, text):
        num_str = match.group(0)
        # Normalize: remove thousands separators, convert decimal comma to dot
        num_str = num_str.replace(',', '.')
        # Try to parse
        try:
            num = float(num_str)
            numbers.append(num)
        except ValueError:
            continue
    
    return numbers


def contains_number(text: str, number: float, tolerance: float = 0.01) -> bool:
    """
    Check if text contains a specific number (with tolerance).
    
    Args:
        text: Text to search in
        number: Number to find
        tolerance: Relative tolerance (0.01 = 1%)
    
    Returns:
        True if number found, False otherwise
    """
    numbers = extract_numbers(text)
    
    for num in numbers:
        # Relative difference
        if abs(num - number) / max(abs(number), 1) <= tolerance:
            return True
    
    return False


def remove_html_tags(text: str) -> str:
    """
    Remove HTML tags from text.
    
    Args:
        text: HTML text
    
    Returns:
        Plain text
    """
    if not text:
        return ""
    
    # Remove script and style tags with content
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)
    
    # Decode HTML entities
    import html
    text = html.unescape(text)
    
    # Clean whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_sentences(text: str, max_sentences: int = 5) -> list[str]:
    """
    Extract first N sentences from text.
    
    Args:
        text: Text to extract from
        max_sentences: Maximum number of sentences
    
    Returns:
        List of sentences
    """
    if not text:
        return []
    
    # Simple sentence splitting (not perfect, but good enough)
    # Split on ., !, ? followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÄÖÜ])', text)
    
    return sentences[:max_sentences]


def slugify(text: str) -> str:
    """
    Convert text to URL-safe slug.
    
    Args:
        text: Text to slugify
    
    Returns:
        Slug (lowercase, hyphens, no special chars)
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Replace umlauts
    replacements = {
        'ä': 'ae', 'ö': 'oe', 'ü': 'ue', 'ß': 'ss',
        'é': 'e', 'è': 'e', 'ê': 'e', 'à': 'a', 'â': 'a',
        'ô': 'o', 'î': 'i', 'ï': 'i', 'ç': 'c'
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # Remove non-alphanumeric (except spaces and hyphens)
    text = re.sub(r'[^a-z0-9\s\-]', '', text)
    
    # Replace spaces with hyphens
    text = text.replace(' ', '-')
    
    # Remove consecutive hyphens
    text = re.sub(r'-+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    return text


def word_count(text: str) -> int:
    """
    Count words in text.
    
    Args:
        text: Text to count
    
    Returns:
        Number of words
    """
    if not text:
        return 0
    
    # Split on whitespace
    words = text.split()
    return len(words)


def char_count(text: str, exclude_whitespace: bool = False) -> int:
    """
    Count characters in text.
    
    Args:
        text: Text to count
        exclude_whitespace: If True, don't count whitespace
    
    Returns:
        Number of characters
    """
    if not text:
        return 0
    
    if exclude_whitespace:
        text = re.sub(r'\s+', '', text)
    
    return len(text)


def has_min_quality(text: str, min_words: int = 50, min_chars: int = 200) -> bool:
    """
    Check if text meets minimum quality thresholds.
    
    Args:
        text: Text to check
        min_words: Minimum word count
        min_chars: Minimum character count
    
    Returns:
        True if quality OK, False otherwise
    """
    if not text:
        return False
    
    return word_count(text) >= min_words and char_count(text) >= min_chars


def extract_quoted_text(text: str) -> list[str]:
    """
    Extract all quoted text (between quotes).
    
    Args:
        text: Text to extract from
    
    Returns:
        List of quoted strings
    """
    # Match text between quotes (both " and ")
    pattern = r'[""](.*?)[""]'
    matches = re.findall(pattern, text)
    return [m.strip() for m in matches if m.strip()]


def similarity_ratio(text1: str, text2: str) -> float:
    """
    Calculate simple similarity ratio between two texts.
    
    Uses character-level overlap (Jaccard similarity).
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    if not text1 or not text2:
        return 0.0
    
    # Normalize
    text1 = normalize_text(text1)
    text2 = normalize_text(text2)
    
    # Character-level sets
    set1 = set(text1)
    set2 = set(text2)
    
    # Jaccard similarity
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    if union == 0:
        return 0.0
    
    return intersection / union
