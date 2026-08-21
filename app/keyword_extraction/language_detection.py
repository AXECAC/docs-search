"""
Simple language detection for English and Russian.
No external libraries.
"""

import re
from .stopwords import get_stopwords

def detect_language_simple(text: str) -> str:
    """
    Enhanced language detection using stopwords and character detection.
    Returns 'en' for English, 'ru' for Russian.
    """
    # Clean the text (remove punctuation, convert to lowercase)
    clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
    words = clean_text.split()
    
    if not words:
        return 'en'
    
    # Method 1: Cyrillic character detection (быстрый, но неточный)
    cyrillic_range = r'[а-яА-ЯёЁ]'
    cyrillic_chars = len(re.findall(cyrillic_range, text))
    
    # Method 2: Stopword-based detection (более точный)
    ru_stopwords = get_stopwords('ru')
    en_stopwords = get_stopwords('en')
    
    # Count stopwords from each language
    ru_stopword_count = sum(1 for word in words if word in ru_stopwords)
    en_stopword_count = sum(1 for word in words if word in en_stopwords)
    
    # Method 3: Common Russian indicators (для коротких текстов)
    russian_indicators = [
        'это', 'что', 'который', 'также', 'ещё', 'очень', 'можно',
        'нельзя', 'нужно', 'почему', 'потому', 'поэтому', 'итак'
    ]
    ru_indicator_count = sum(1 for word in words if word in russian_indicators)
    
    # Decision logic
    # If strong Cyrillic presence -> Russian
    if cyrillic_chars > len(text) * 0.3:
        return 'ru'
    
    # If strong stopword evidence
    if ru_stopword_count > en_stopword_count * 1.5:
        return 'ru'
    
    if en_stopword_count > ru_stopword_count * 1.5:
        return 'en'
    
    # If many Russian function words
    if ru_indicator_count >= 2:
        return 'ru'
    
    # Check for Russian-specific patterns
    if any(word.endswith(('ться', 'тся', 'щий', 'щая', 'щее')) for word in words):
        return 'ru'
    
    # Default to English
    return 'en'