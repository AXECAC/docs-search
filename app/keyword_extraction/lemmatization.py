"""
Words lemmatization utilities for Russian.
Lemmatizes words in Russian.
"""
import pymorphy3

morph_ru = pymorphy3.MorphAnalyzer()

def lemmatize_russian(word: str) -> str:
    """
    Приводит русское слово к начальной форме.
    Если лемматизация не удалась, возвращает исходное слово.
    """
    try:
        parsed = morph_ru.parse(word)[0]
        return parsed.normal_form
    except:
        return word

def lemmatize_russian_collocation(phrase: str) -> str:
    """
    Лемматизирует всю коллокацию (фразу из нескольких слов).
    Пример: "глубокие нейронные сети" -> "глубокий нейронный сеть"
    """
    if not phrase or len(phrase.strip()) == 0:
        return phrase
    
    words = phrase.lower().split()
    lemmatized_words = [lemmatize_russian(word) for word in words]
    return ' '.join(lemmatized_words)

def is_function_word(word: str) -> bool:
    """
    Определяет, является ли слово служебной частью речи.
    Возвращает True для слов, которые стоит исключить из ключевых слов.
    """
    try:
        parsed = morph_ru.parse(word)[0]
        pos = parsed.tag.POS
        
        # Служебные части речи (стоит исключить)
        function_positions = {'PREP', 'CONJ', 'PRCL', 'INTJ', 'NPRO'}
        
        # Также исключаем числительные
        if pos == 'NUMR':
            return True
            
        return pos in function_positions
    except:
        return False

def is_content_word(word: str) -> bool:
    """
    Определяет, является ли слово знаменательной частью речи.
    """
    try:
        parsed = morph_ru.parse(word)[0]
        pos = parsed.tag.POS
        content_positions = {'NOUN', 'ADJF', 'ADJS', 'VERB', 'INFN'}
        return pos in content_positions
    except:
        return False