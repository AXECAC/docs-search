"""
Multilingual Semantic Keyword Set
A tool for extracting and managing keywords with semantic deduplication.
Supported languages: Russian and English.
"""

from .keyword_set import MultilingualKeywordSet
from .collocation_deduplicator import CollocationDeduplicator
from .language_detection import detect_language_simple
from .paragraph_processor import ParagraphProcessor
from .keyword_processor import KeywordProcessor
from .collocation_extractor import CollocationExtractor

__version__ = "1.0.2"
__all__ = [
    'MultilingualKeywordSet',
    'CollocationDeduplicator',
    'detect_language_simple',
    'ParagraphProcessor',
    'KeywordProcessor',
    'CollocationExtractor'
]