"""
Keyword processing utilities for extraction and filtering.
"""

import re
from collections import Counter
from typing import List, Tuple, Set
from .stopwords import get_punctuation_pattern, is_stopword
from .lemmatization import lemmatize_russian, lemmatize_russian_collocation, is_function_word
from .language_detection import detect_language_simple


class KeywordProcessor:
    """Processes keywords: extraction, lemmatization, filtering."""
    
    def __init__(self, keybert_model=None):
        self.keybert = keybert_model
    
    def lemmatize_if_necessary(self, keyword: str) -> str:
        """Lemmatize keyword if it's Russian."""
        if detect_language_simple(keyword).lower() == 'ru':
            return lemmatize_russian_collocation(keyword)
        return keyword
    
    def filter_stopwords(self, words: List[str]) -> List[str]:
        """Filter out stopwords from a list of words."""
        filtered = []
        for w in words:
            lang = detect_language_simple(w).lower()
            lemmatized = self.lemmatize_if_necessary(w)
            if not is_stopword(lemmatized, lang) and len(w) > 2:
                filtered.append(w)
        return filtered
    
    def extract_simple_keywords(self, text: str, language: str = 'en') -> List[str]:
        """Simple keyword extraction as fallback."""
        punct_pattern = get_punctuation_pattern(language)
        clean_text = re.sub(punct_pattern, ' ', text.lower())
        words = clean_text.split()
        
        keywords = self.filter_stopwords(words)
        
        unique_keywords = []
        seen = set()
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:10]
    
    def prepare_keyword_for_addition(self, keyword: str, language: str) -> str:
        """Prepare keyword before adding to set (lemmatize, normalize)."""
        keyword_lower = keyword.lower().strip()
        
        if language == 'ru':
            keyword_lower = lemmatize_russian_collocation(keyword_lower)
        
        return keyword_lower
    
    def should_skip_keyword(self, keyword: str, language: str, 
                            existing_keywords: set = None) -> Tuple[bool, str]:
        """
        Check if keyword should be skipped.
        
        Returns:
            (should_skip, reason)
        """
        keyword_lower = keyword.lower().strip()
        
        # Check length
        if len(keyword_lower) < 3:
            return True, "too short"
        
        # Check if single word is part of existing collocation
        if existing_keywords and len(keyword_lower.split()) == 1:
            for existing in existing_keywords:
                if len(existing.split()) >= 2 and keyword_lower in existing.split():
                    return True, f"part of collocation '{existing}'"
        
        # Check stopwords
        words = keyword_lower.split()
        stopword_count = sum(1 for w in words if is_stopword(w, language))
        if len(words) > 0 and stopword_count == len(words):
            return True, "all words are stopwords"
        
        # Check function words for Russian
        if language == 'ru':
            func_count = sum(1 for w in words if is_function_word(w))
            if len(words) > 0 and func_count == len(words):
                return True, "all words are function words"
        
        return False, ""
    
    def extract_keywords_from_text(self, text: str, language: str = 'en', 
                              top_n: int = 10, verbose: bool = False) -> List[Tuple[str, float]]:
        """Extract keywords and collocations from text."""
        all_candidates = []
        from .collocation_extractor import CollocationExtractor
        
        # Extract collocations
        coll_extractor = CollocationExtractor(max_ngram_size=3)
        collocations = coll_extractor.extract_collocations(text, language, top_n=top_n * 2, verbose=verbose)
        
        # Lemmatize collocations
        if language == 'ru':
            lemmatized_collocs = []
            for phrase, score in collocations:
                lemmatized_phrase = lemmatize_russian_collocation(phrase)
                words = lemmatized_phrase.split()
                if len(words) >= 2:
                    lemmatized_collocs.append((lemmatized_phrase, score * 2.0))
                    if verbose:
                        print(f"[COLLOC] Found: '{phrase}' -> '{lemmatized_phrase}' (score: {score:.3f})")
            all_candidates.extend(lemmatized_collocs)
        else:
            all_candidates.extend(collocations)
        
        # Extract single words using simple method (without KeyBERT)
        simple_keywords = self.extract_simple_keywords(text, language)
        
        # Filter words that are already in collocations
        collocation_words = set()
        for phrase, _ in all_candidates:
            for word in phrase.split():
                collocation_words.add(word)
        
        for word in simple_keywords[:top_n]:
            if word not in collocation_words:
                all_candidates.append((word, 0.5))
        
        # Remove duplicates
        unique_candidates = {}
        for phrase, score in all_candidates:
            if phrase not in unique_candidates or score > unique_candidates[phrase]:
                unique_candidates[phrase] = score
        
        sorted_candidates = sorted(unique_candidates.items(), 
                                key=lambda x: x[1], reverse=True)
        
        # Deduplicate overlapping collocations
        from .collocation_deduplicator import CollocationDeduplicator
        deduplicated = CollocationDeduplicator.remove_overlapping_collocations(
            sorted_candidates, 0.6
        )
        
        return deduplicated[:top_n]