"""
Collocation deduplication utilities.
Handles removal of overlapping and redundant collocations.
"""

from typing import List, Tuple, Set
import re

class CollocationDeduplicator:
    """
    Handles deduplication of overlapping collocations.
    """
    
    @staticmethod
    def tokenize_phrase(phrase: str) -> List[str]:
        """Split a phrase into tokens (words)."""
        return phrase.lower().split()
    
    @staticmethod
    def calculate_overlap(phrase1: str, phrase2: str) -> Tuple[int, List[str]]:
        """
        Calculate overlapping words between two phrases.
        Returns (overlap_count, overlapping_words).
        """
        tokens1 = set(CollocationDeduplicator.tokenize_phrase(phrase1))
        tokens2 = set(CollocationDeduplicator.tokenize_phrase(phrase2))
        
        overlap = tokens1.intersection(tokens2)
        return len(overlap), list(overlap)

    @staticmethod
    def is_subsumed(longer: str, shorter: str) -> bool:
        """
        Check if shorter phrase is completely contained within longer phrase.
        Example: "neural network" is subsumed by "deep neural network"
        """
        tokens_longer = CollocationDeduplicator.tokenize_phrase(longer)
        tokens_shorter = CollocationDeduplicator.tokenize_phrase(shorter)
        
        # Check if all tokens of shorter are in longer (in order)
        long_idx = 0
        for short_token in tokens_shorter:
            found = False
            while long_idx < len(tokens_longer):
                if tokens_longer[long_idx] == short_token:
                    found = True
                    long_idx += 1
                    break
                long_idx += 1
            if not found:
                return False
        return True
    
    
    @staticmethod
    def remove_overlapping_collocations(collocations: List[Tuple[str, float]], 
                                       overlap_threshold: float = 0.6) -> List[Tuple[str, float]]:
        """
        Remove overlapping collocations, keeping the most specific (longer) ones.
        
        Args:
            collocations: List of (phrase, score) tuples
            overlap_threshold: Minimum overlap ratio to consider as overlapping
                              (e.g., 0.6 means 60% of words overlap)
        
        Returns:
            Deduplicated list of collocations
        """
        if not collocations:
            return []
        
        # Sort by length (longest first) and then by score
        sorted_collocations = sorted(collocations, 
                                    key=lambda x: (len(x[0].split()), x[1]), 
                                    reverse=True)
        
        kept = []
        kept_phrases = []
        
        for phrase, score in sorted_collocations:
            tokens_phrase = set(CollocationDeduplicator.tokenize_phrase(phrase))
            phrase_len = len(tokens_phrase)
            
            should_keep = True
            
            # Check against already kept phrases
            for kept_phrase in kept_phrases:
                tokens_kept = set(CollocationDeduplicator.tokenize_phrase(kept_phrase))
                kept_len = len(tokens_kept)
                
                # Calculate overlap
                overlap_count = len(tokens_phrase.intersection(tokens_kept))
                overlap_ratio = overlap_count / min(phrase_len, kept_len)
                
                # If significant overlap exists
                if overlap_ratio >= overlap_threshold:
                    # If current phrase is longer, replace the kept one
                    if phrase_len > kept_len:
                        # Remove the kept phrase (will be replaced)
                        continue
                    else:
                        # Current phrase is subsumed by kept phrase
                        should_keep = False
                        break
            
            if should_keep:
                # Check if this phrase subsumes any kept phrases
                new_kept = []
                for kept_phrase in kept_phrases:
                    if not CollocationDeduplicator.is_subsumed(phrase, kept_phrase):
                        new_kept.append(kept_phrase)
                new_kept.append(phrase)
                kept_phrases = new_kept
                kept.append((phrase, score))
        
        # Sort by score again for output
        kept.sort(key=lambda x: x[1], reverse=True)
        return kept