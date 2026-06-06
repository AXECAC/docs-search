"""
Collocation extraction utilities for multilingual text.
"""

import re
from collections import Counter
from typing import List, Tuple, Set
from .stopwords import get_stopwords, is_stopword
from .lemmatization import is_content_word
from .collocation_deduplicator import CollocationDeduplicator

# Try to import NLTK
try:
    import nltk
    from nltk.collocations import BigramCollocationFinder, TrigramCollocationFinder
    from nltk.metrics import BigramAssocMeasures, TrigramAssocMeasures
    
    nltk_data_downloaded = False
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
        nltk_data_downloaded = True
    except LookupError:
        print("Downloading required NLTK data...")
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk_data_downloaded = True
            print("NLTK data downloaded successfully")
        except Exception as e:
            print(f"Could not download NLTK data: {e}")
            nltk_data_downloaded = False
    
    NLTK_AVAILABLE = nltk_data_downloaded
    
except ImportError:
    print("NLTK not installed. Using fallback methods.")
    NLTK_AVAILABLE = False
    nltk = None


class CollocationExtractor:
    """Extracts and processes collocations from text."""
    
    def __init__(self, max_ngram_size: int = 3, deduplicator=None):
        self.max_ngram_size = max_ngram_size
        self.deduplicator = deduplicator or CollocationDeduplicator()
    
    def extract_collocations_fallback(self, text: str, language: str = 'en', 
                                      top_n: int = 10, verbose: bool = False) -> List[Tuple[str, float]]:
        """Fallback method for extracting collocations."""
        from .stopwords import get_punctuation_pattern
        punct_pattern = get_punctuation_pattern(language)
        clean_text = re.sub(punct_pattern, ' ', text.lower())
        words = clean_text.split()
        
        collocations = []
        
        # Стоп-слова, которые не должны быть в коллокациях
        stopwords = get_stopwords(language)
        bad_patterns = {'это', 'он', 'она', 'оно', 'они', 'этот', 'эта', 'это', 'эти'}
        
        for n in range(2, self.max_ngram_size + 1):
            for i in range(len(words) - n + 1):
                ngram_words = words[i:i+n]
                ngram = ' '.join(ngram_words)
                
                # Пропускаем коллокации, начинающиеся с местоимений или предлогов
                first_word = ngram_words[0]
                if first_word in stopwords or first_word in bad_patterns:
                    continue
                
                # Пропускаем коллокации, заканчивающиеся на предлоги
                last_word = ngram_words[-1]
                if last_word in {'о', 'об', 'в', 'на', 'для', 'с', 'к', 'у', 'по', 'за'}:
                    continue
                
                # Проверяем, что коллокация содержит хотя бы одно знаменательное слово
                has_content = False
                for w in ngram_words:
                    if is_content_word(w) if language == 'ru' else len(w) > 3:
                        has_content = True
                        break
                
                if not has_content:
                    continue
                
                # Считаем частоту
                freq = sum(1 for j in range(len(words) - n + 1) 
                          if ' '.join(words[j:j+n]) == ngram)
                
                if freq >= 1:
                    # Вес коллокации: частота + длина
                    score = freq * len(ngram) / 50
                    
                    # Бонус за длину
                    if n == 2:
                        score *= 1.2
                    elif n == 3:
                        score *= 1.5
                    
                    collocations.append((ngram, score))
        
        # Удаляем дубликаты
        unique_collocations = {}
        for colloc, score in collocations:
            if colloc not in unique_collocations or score > unique_collocations[colloc]:
                unique_collocations[colloc] = score
        
        # Отладочный вывод
        if verbose:
            print(f"\n[DEBUG] Filtered collocations (after cleaning):")
        for colloc, score in list(unique_collocations.items())[:15]:
            if verbose:
                print(f"  - '{colloc}' (score: {score:.3f})")
        
        sorted_collocations = sorted(unique_collocations.items(), 
                                    key=lambda x: x[1], reverse=True)
        
        return sorted_collocations[:top_n]
    
    def extract_collocations_nltk(self, text: str, language: str = 'en', 
                                  top_n: int = 10) -> List[Tuple[str, float]]:
        """Extract collocations using NLTK."""
        if not NLTK_AVAILABLE:
            return self.extract_collocations_fallback(text, language, top_n)
        
        try:
            from nltk.corpus import stopwords
            
            try:
                nltk_stopwords = set(stopwords.words(language))
            except:
                nltk_stopwords = get_stopwords(language)
            
            tokens = nltk.word_tokenize(text.lower())
            
            filtered_tokens = [token for token in tokens 
                              if token.isalnum() and token not in nltk_stopwords and len(token) > 2]
            
            if len(filtered_tokens) < 2:
                return []
            
            collocations = []
            
            if self.max_ngram_size >= 2:
                try:
                    bigram_finder = BigramCollocationFinder.from_words(filtered_tokens)
                    bigram_finder.apply_freq_filter(1)
                    bigrams = bigram_finder.nbest(BigramAssocMeasures.pmi, min(top_n, 20))
                    for bigram in bigrams:
                        collocation = ' '.join(bigram)
                        score = len(collocation) / 50
                        collocations.append((collocation, score))
                except:
                    pass
            
            if self.max_ngram_size >= 3:
                try:
                    trigram_finder = TrigramCollocationFinder.from_words(filtered_tokens)
                    trigram_finder.apply_freq_filter(1)
                    trigrams = trigram_finder.nbest(TrigramAssocMeasures.pmi, min(top_n, 20))
                    for trigram in trigrams:
                        collocation = ' '.join(trigram)
                        score = len(collocation) / 50
                        collocations.append((collocation, score))
                except:
                    pass
            
            unique_collocations = {}
            for colloc, score in collocations:
                if colloc not in unique_collocations or score > unique_collocations[colloc]:
                    unique_collocations[colloc] = score
            
            sorted_collocations = sorted(unique_collocations.items(), 
                                        key=lambda x: x[1], reverse=True)
            
            # Apply deduplication
            deduplicated = self.deduplicator.remove_overlapping_collocations(
                sorted_collocations, 0.6
            )
            
            return deduplicated[:top_n]
            
        except Exception as e:
            return self.extract_collocations_fallback(text, language, top_n)
    
    def extract_collocations(self, text: str, language: str = 'en', 
                            top_n: int = 10, verbose: bool = False) -> List[Tuple[str, float]]:
        """Extract collocations from text with deduplication."""
        if NLTK_AVAILABLE:
            return self.extract_collocations_nltk(text, language, top_n)
        else:
            return self.extract_collocations_fallback(text, language, top_n, verbose)