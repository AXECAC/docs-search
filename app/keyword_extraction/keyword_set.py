"""
Main keyword set class with multilingual support and semantic deduplication.
"""

import os
import re
import warnings
from collections import defaultdict
from typing import List, Tuple, Set, Dict, Optional

from sentence_transformers import SentenceTransformer, util

from .language_detection import detect_language_simple
from .paragraph_processor import ParagraphProcessor
from .collocation_deduplicator import CollocationDeduplicator
from .keyword_processor import KeywordProcessor
from .lemmatization import lemmatize_russian_collocation

warnings.filterwarnings('ignore')

class MultilingualKeywordSet:
    """Multilingual keyword set with collocation deduplication."""
    
    def __init__(self, 
                 initial_keywords: Dict[str, List[str]] = None,
                 similarity_threshold: float = 0.75,
                 collocation_overlap_threshold: float = 0.6,
                 embedding_model: str = 'cointegrated/rubert-tiny2',
                 cache_folder: str = './model_cache',
                 use_collocations: bool = True,
                 max_ngram_size: int = 3,
                 max_chunk_size: int = 1000,
                 chunk_overlap: int = 100):
        """
        Initialize multilingual keyword set.
        """
        self.similarity_threshold = similarity_threshold
        self.collocation_overlap_threshold = collocation_overlap_threshold
        self.use_collocations = use_collocations
        self.max_ngram_size = max_ngram_size
        
        self.paragraph_processor = ParagraphProcessor(max_chunk_size, chunk_overlap)
        self.deduplicator = CollocationDeduplicator()
        
        if use_collocations:
            print("Collocations enabled")
        
        # Create cache folder
        os.makedirs(cache_folder, exist_ok=True)
        
        # Load model
        print(f"Loading multilingual model from: {embedding_model}")
        try:
            self.model = SentenceTransformer(embedding_model, cache_folder=cache_folder)
            print(f"Model loaded successfully")
        except Exception as e:
            print(f"Could not load {embedding_model}, falling back to English model...")
            self.model = SentenceTransformer('sentence-transformers/paraphrase-MiniLM-L3-v2', 
                                            cache_folder=cache_folder)
            print(f"English model loaded as fallback")
        
        # Initialize processors
        self.keyword_processor = KeywordProcessor(keybert_model=None)  # Will be set after model load
        self.keybert = None  # Will be initialized later if needed
        
        # Try to initialize KeyBERT with the model
        try:
            from keybert import KeyBERT
            self.keybert = KeyBERT(model=self.model)
            self.keyword_processor.keybert = self.keybert
        except Exception as e:
            print(f"KeyBERT not available ({e}), using fallback extraction")
            self.keybert = None
            self.keyword_processor.keybert = None
        
        # Store keywords per language
        self.keywords_by_lang: Dict[str, Set[str]] = {}
        self.keyword_embeddings: Dict[str, Dict[str, any]] = {}
        self.keyword_frequencies: Dict[str, Dict[str, int]] = {}
        self.keyword_metadata: Dict[str, Dict] = {}
        
        # Add initial keywords
        if initial_keywords:
            for lang, keywords in initial_keywords.items():
                if lang not in self.keywords_by_lang:
                    self.keywords_by_lang[lang] = set()
                    self.keyword_embeddings[lang] = {}
                    self.keyword_frequencies[lang] = defaultdict(int)
                
                for keyword in keywords:
                    self.add_keyword(keyword, lang, check_similarity=False)
    
    # Public methods
    
    def add_keyword(self, keyword: str, language: str, check_similarity: bool = True, verbose = False) -> bool:
        """Add a keyword to the set."""
        # Prepare keyword
        keyword_lower = self.keyword_processor.prepare_keyword_for_addition(keyword, language)
        
        # Check if should skip
        existing_keywords = self.keywords_by_lang.get(language, set())
        should_skip, reason = self.keyword_processor.should_skip_keyword(
            keyword_lower, language, existing_keywords
        )
        if should_skip:
            if verbose:
                print(f"  Skipped '{keyword}' ({language}) - {reason}")
            return False
        
        # Initialize language storage
        if language not in self.keywords_by_lang:
            self.keywords_by_lang[language] = set()
            self.keyword_embeddings[language] = {}
            self.keyword_frequencies[language] = defaultdict(int)
        
        # Check if already exists
        if keyword_lower in self.keywords_by_lang[language]:
            self.keyword_frequencies[language][keyword_lower] += 1
            return False
        
        # Check semantic similarity
        if check_similarity and self.keywords_by_lang[language]:
            try:
                new_embedding = self.model.encode(keyword_lower, convert_to_tensor=True)
                
                max_similarity = 0
                most_similar_keyword = None
                
                for existing_keyword, existing_embedding in self.keyword_embeddings[language].items():
                    similarity = util.pytorch_cos_sim(new_embedding, existing_embedding).item()
                    if similarity > max_similarity:
                        max_similarity = similarity
                        most_similar_keyword = existing_keyword
                
                if max_similarity >= self.similarity_threshold:
                    if verbose:
                        print(f"  Rejected '{keyword}' -> '{keyword_lower}' (similar to '{most_similar_keyword}': {max_similarity:.3f})")
                    return False
                else:
                    self._add_to_storage(keyword, keyword_lower, language, new_embedding)
                    if verbose:
                        print(f"  Added: '{keyword}' -> '{keyword_lower}' (max similarity: {max_similarity:.3f})")
                    return True
            except Exception as e:
                if verbose:
                    print(f"  Error adding keyword '{keyword}': {e}")
                return False
        else:
            try:
                embedding = self.model.encode(keyword_lower, convert_to_tensor=True)
                self._add_to_storage(keyword, keyword_lower, language, embedding)
                if verbose:
                    print(f"  Added: '{keyword}' -> '{keyword_lower}'")
                return True
            except Exception as e:
                if verbose:
                    print(f"  Error adding keyword '{keyword}': {e}")
                return False
    
    def process_text(self, text: str, top_n: int = -1, verbose: bool = False) -> Dict:
        """Process text (sentence or paragraph)."""
        # Calculate top_n if not specified
        if top_n < 0:
            marks = r'[,;.!?]+[\n]+'
            marks_num = len(re.split(marks, text))
            top_n = marks_num if marks_num > 1 else int(text.count(' ') / 3)
        
        language = detect_language_simple(text)
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"Processing Text (Language: {language.upper()})")
            print(f"{'='*70}")
            print(f"Text: {text[:150]}...")
        
        all_keywords = []
        all_new_keywords = []
        
        # Process based on text length
        if len(text) > self.paragraph_processor.max_chunk_size:
            chunks = self.paragraph_processor.process_paragraph(text, language)
            if verbose:
                print(f"\nSplit into {len(chunks)} chunk(s)")
            
            for chunk_info in chunks:
                keywords, new_keywords = self._process_chunk(chunk_info, language, top_n, verbose)
                all_keywords.extend(keywords)
                all_new_keywords.extend(new_keywords)
        else:
            extracted = self.keyword_processor.extract_keywords_from_text(text, language, top_n, verbose)
            
            if verbose and extracted:
                print(f"\nExtracted keywords (after deduplication):")
                for i, (candidate, score) in enumerate(extracted[:5], 1):
                    print(f"   {i}. '{candidate}' (score: {score:.3f})")
            
            for candidate, score in extracted:
                lemmatized = self.keyword_processor.lemmatize_if_necessary(candidate)
                if self.add_keyword(candidate, language, check_similarity=True, verbose=verbose):
                    all_new_keywords.append(lemmatized)
                    all_keywords.append(lemmatized)
                else:
                    similar = self.find_similar_keywords(lemmatized, 1)
                    if similar:
                        all_keywords.append(similar[0][0])
        
        # Filter final keywords
        filtered_keywords = self.keyword_processor.filter_stopwords(list(set(all_keywords)))
        
        if verbose:
            print(f"\nAdded {len(all_new_keywords)} new keyword(s)")
            print(f"Total keywords: {sum(len(kw) for kw in self.keywords_by_lang.values())}")
        
        return {
            'language': language,
            'keywords_added': all_new_keywords,
            'total_keywords': sum(len(kw) for kw in self.keywords_by_lang.values()),
            'keywords': filtered_keywords
        }
    
    # Helper methods
    
    def _add_to_storage(self, original: str, normalized: str, language: str, embedding):
        """Add keyword to storage."""
        self.keywords_by_lang[language].add(normalized)
        self.keyword_embeddings[language][normalized] = embedding
        self.keyword_frequencies[language][normalized] = 1
        self.keyword_metadata[normalized] = {'language': language, 'original': original}
    
    def _process_chunk(self, chunk_info: Dict, language: str, top_n: int, verbose: bool):
        """Process a single chunk."""
        if verbose:
            print(f"\n{'#'*40}")
            print(f"Processing Chunk {chunk_info['chunk_id']}")
            print(f"{'#'*40}")
        
        extracted = self.keyword_processor.extract_keywords_from_text(
            chunk_info['text'], language, top_n
        )
        
        if verbose and extracted:
            print(f"\nExtracted candidates:")
            for i, (candidate, score) in enumerate(extracted[:5], 1):
                print(f"   {i}. '{candidate}' (score: {score:.3f})")
        
        all_keywords = []
        all_new_keywords = []
        
        for candidate, score in extracted:
            lemmatized = self.keyword_processor.lemmatize_if_necessary(candidate)
            if self.add_keyword(candidate, language, check_similarity=True, verbose=verbose):
                all_new_keywords.append(lemmatized)
                all_keywords.append(lemmatized)
            else:
                similar = self.find_similar_keywords(lemmatized, 1)
                if similar:
                    all_keywords.append(similar[0][0])
        
        return all_keywords, all_new_keywords

    def get_all_keywords(self, language: Optional[str] = None, sort_by_frequency: bool = False) -> Dict[str, List[str]]:
        """
        Get all keywords, optionally filtered by language.
        """
        if language:
            if language in self.keywords_by_lang:
                keywords = list(self.keywords_by_lang[language])
                if sort_by_frequency:
                    keywords.sort(key=lambda x: self.keyword_frequencies[language].get(x, 0), reverse=True)
                return {language: keywords}
            else:
                return {language: []}
        else:
            result = {}
            for lang, keywords in self.keywords_by_lang.items():
                sorted_keywords = list(keywords)
                if sort_by_frequency:
                    sorted_keywords.sort(key=lambda x: self.keyword_frequencies[lang].get(x, 0), reverse=True)
                result[lang] = sorted_keywords
            return result
    
    def find_similar_keywords(self, keyword: str, top_n: int = 5) -> List[Tuple[str, float, str]]:
        """
        Find similar keywords across all languages.
        
        Returns:
            List of (keyword, similarity_score, language) tuples
        """
        keyword_lower = keyword.lower().strip()
        
        try:
            keyword_embedding = self.model.encode(keyword_lower, convert_to_tensor=True)
            
            similarities = []
            for lang, embeddings in self.keyword_embeddings.items():
                for existing_keyword, existing_embedding in embeddings.items():
                    similarity = util.pytorch_cos_sim(keyword_embedding, existing_embedding).item()
                    similarities.append((existing_keyword, similarity, lang))
            
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:top_n]
        except Exception as e:
            print(f"Error finding similar keywords: {e}")
            return []
    
    def set_similarity_threshold(self, threshold: float):
        """Adjust the similarity threshold."""
        self.similarity_threshold = threshold
        print(f"Similarity threshold updated to {threshold}")
    
    def display_keyword_set(self, show_frequencies: bool = False):
        """Display all keywords organized by language."""
        print(f"\nCurrent Multilingual Keyword Set")
        print("=" * 60)
        
        for lang in sorted(self.keywords_by_lang.keys()):
            count = len(self.keywords_by_lang[lang])
            print(f"\n{lang.upper()} ({count} keywords):")
            print("-" * 40)
            
            if show_frequencies:
                sorted_items = sorted(self.keyword_frequencies[lang].items(), 
                                     key=lambda x: x[1], reverse=True)
                for i, (kw, freq) in enumerate(sorted_items[:20], 1):
                    print(f"{i:2d}. {kw:<35} (freq: {freq})")
            else:
                for i, kw in enumerate(sorted(self.keywords_by_lang[lang])[:20], 1):
                    print(f"{i:2d}. {kw}")
            
            if count > 20:
                print(f"   ... and {count - 20} more")
        
        print("=" * 60)
    
    def save_keywords_to_file(self, filename: str):
        """Save current keywords to a file."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# Multilingual Keyword Set\n")
            f.write(f"# Similarity Threshold: {self.similarity_threshold}\n")
            f.write(f"# Collocation Overlap Threshold: {self.collocation_overlap_threshold}\n\n")
            
            for lang in sorted(self.keywords_by_lang.keys()):
                f.write(f"\n## {lang.upper()} Keywords:\n")
                for kw in sorted(self.keywords_by_lang[lang]):
                    freq = self.keyword_frequencies[lang].get(kw, 1)
                    f.write(f"{kw}\t{freq}\t{lang}\n")
        
        print(f"Keywords saved to {filename}")
    
    def load_keywords_from_file(self, filename: str):
        """Load keywords from a file."""
        if not os.path.exists(filename):
            print(f"File {filename} not found")
            return
        
        with open(filename, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('##'):
                    continue
                
                parts = line.split('\t')
                if len(parts) >= 2:
                    keyword = parts[0]
                    freq = int(parts[1]) if len(parts) > 1 else 1
                    lang = parts[2] if len(parts) > 2 else 'en'
                    
                    if lang not in self.keywords_by_lang:
                        self.keywords_by_lang[lang] = set()
                        self.keyword_embeddings[lang] = {}
                        self.keyword_frequencies[lang] = defaultdict(int)
                    
                    if keyword not in self.keywords_by_lang[lang]:
                        self.keywords_by_lang[lang].add(keyword)
                        try:
                            self.keyword_embeddings[lang][keyword] = self.model.encode(keyword, convert_to_tensor=True)
                            self.keyword_frequencies[lang][keyword] = freq
                        except Exception as e:
                            print(f"Warning: Could not load '{keyword}': {e}")
        
        print(f"Loaded keywords from {filename}")