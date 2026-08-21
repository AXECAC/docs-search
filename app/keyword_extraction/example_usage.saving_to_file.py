"""
Example usage of the Multilingual Keyword Set.
"""

import sys
import os

# Add parent directory to path if running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from keyword_extraction import MultilingualKeywordSet

model_cache_path = './model_cache'

def example_usage():
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    print("MULTILINGUAL SEMANTIC KEYWORD SET (No langdetect)")
    print("=" * 70)
    
    initial_keywords = {
        'en': ["machine learning", "neural network", "deep learning"],
        'ru': ["машинное обучение", "нейронная сеть", "глубокое обучение"]
    }
    
    keyword_set = MultilingualKeywordSet(
        initial_keywords=initial_keywords,
        similarity_threshold=0.75,
        collocation_overlap_threshold=0.6,
        cache_folder=model_cache_path,
        use_collocations=True,
        max_chunk_size=500
    )
    
    print("\nInitial keyword set:")
    keyword_set.display_keyword_set()
    
    # Test texts with overlapping phrases
    texts = [
        # English sentences
        "Deep neural networks are revolutionizing artificial intelligence",
        "Глубокие нейронные сети революционизируют искусственный интеллект",
        "Support vector machines are used for classification tasks",
        "Методы опорных векторов используются для задач классификации",
        
        # Long English paragraph with overlapping phrases
        """
        This is a longer paragraph about machine learning. 
        It covers multiple topics including neural networks, deep neural networks, 
        and convolutional neural networks. The goal is to extract meaningful keywords 
        like machine learning algorithms and deep learning methods from longer texts.
        """,
        
        # Long Russian paragraph with overlapping phrases
        """
        Это длинный абзац о машинном обучении. 
        Он охватывает несколько тем, включая нейронные сети, глубокие нейронные сети 
        и сверточные нейронные сети. Цель состоит в том, чтобы извлечь значимые ключевые слова,
        такие как алгоритмы машинного обучения и методы глубокого обучения, из длинных текстов.
        """,
        
        # Another English text with more overlapping collocations
        """
        Convolutional neural networks (CNNs) are a type of neural network architecture.
        These deep learning models have revolutionized computer vision tasks.
        Transfer learning allows reusing pre-trained neural networks for new tasks.
        """
    ]
    
    print("\n" + "=" * 70)
    print("PROCESSING TEXTS WITH OVERLAPPING COLLOCATIONS")
    print("=" * 70)
    
    for i, text in enumerate(texts, 1):
        print(f"\n{'#'*70}")
        print(f"Text {i}/{len(texts)}")
        print(f"{'#'*70}")
        keyword_set.process_text(text, top_n=6, verbose=True)
    
    print("\n" + "=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)
    
    # Show final keyword set with frequencies
    keyword_set.display_keyword_set(show_frequencies=True)
    
    # Save keywords to file
    keyword_set.save_keywords_to_file('./multilingual_keywords.txt')
    """
    # Optional: Show the saved keywords
    print("\n" + "=" * 70)
    print("SAVED KEYWORDS PREVIEW")
    print("=" * 70)
    with open('multilingual_keywords.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for line in lines[:20]:  # Show first 20 lines
            print(line.rstrip())
        if len(lines) > 20:
            print(f"... and {len(lines) - 20} more lines")
    """

def simple_example():
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    """Very simple example for quick testing."""
    print("\n" + "=" * 70)
    print("SIMPLE QUICK TEST")
    print("=" * 70)
    
    keyword_set = MultilingualKeywordSet(
        similarity_threshold=0.7,
        collocation_overlap_threshold=0.6,
        cache_folder='./simple_cache'
    )
    
    # Quick English test
    keyword_set.process_text("Machine learning is transforming technology", top_n=3)
    
    # Quick Russian test
    keyword_set.process_text("Искусственный интеллект меняет мир", top_n=3)
    
    # Display results
    keyword_set.display_keyword_set()

def enter_example():
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    # Это длинный абзац о машинном обучении. Он охватывает несколько тем, включая нейронные сети, глубокие нейронные сети и сверточные нейронные сети. Цель состоит в том, чтобы извлечь значимые ключевые слова, такие как алгоритмы машинного обучения и методы глубокого обучения, из длинных текстов.
    
    keyword_set = MultilingualKeywordSet(
        initial_keywords={
            'en': [],
            'ru': []
        },
        similarity_threshold=0.75,
        collocation_overlap_threshold=0.6,
        cache_folder=model_cache_path,
        use_collocations=True,
        max_chunk_size=500
    )

    print("Enter your text: ")
    s = input()
    
    keyword_set.process_text(s, verbose=True)

    keyword_set.display_keyword_set()

    keyword_set.save_keywords_to_file('./entered_text_keywords.txt')


if __name__ == "__main__":
    # Run the main example
    # example_usage()
    
    enter_example()