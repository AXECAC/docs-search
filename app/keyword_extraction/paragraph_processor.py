"""
Paragraph processing utilities for splitting long texts into chunks.
"""

import re
from typing import List, Dict

class ParagraphProcessor:
    """Handles processing of paragraphs into chunks."""
    
    def __init__(self, max_chunk_size: int = 500, overlap: int = 50):
        """
        Initialize paragraph processor.
        
        Args:
            max_chunk_size: Maximum characters per chunk
            overlap: Number of characters to overlap between chunks
        """
        self.max_chunk_size = max_chunk_size
        self.overlap = overlap
    
    def split_into_sentences(self, text: str, language: str = 'en') -> List[str]:
        """Split text into sentences."""
        sentence_endings = r'[.!?]+[\s\n]+'
        sentences = re.split(sentence_endings, text)
        return [s.strip() for s in sentences if s.strip()]
    
    def split_paragraph_into_chunks(self, paragraph: str, language: str = 'en') -> List[Dict]:
        """
        Split a paragraph into overlapping chunks.
        
        Returns:
            List of dicts with 'chunk_id', 'text', 'start_sentence', 'end_sentence'
        """
        sentences = self.split_into_sentences(paragraph, language)
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_length = 0
        chunk_id = 1
        
        for i, sentence in enumerate(sentences):
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.max_chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': chunk_text,
                    'start_sentence': chunk_id - 1,
                    'end_sentence': i
                })
                chunk_id += 1
                
                # Start new chunk with overlap
                overlap_sentences = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break
                
                current_chunk = overlap_sentences
                current_length = overlap_length
            
            current_chunk.append(sentence)
            current_length += sentence_length + 1
        
        # Add the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'chunk_id': chunk_id,
                'text': chunk_text,
                'start_sentence': chunk_id - 1,
                'end_sentence': len(sentences)
            })
        
        return chunks
    
    def process_paragraph(self, paragraph: str, language: str = 'en') -> List[Dict]:
        """
        Process a paragraph into chunks ready for keyword extraction.
        """
        # Remove extra whitespace
        paragraph = re.sub(r'\s+', ' ', paragraph).strip()
        
        # Check if paragraph needs to be split
        if len(paragraph) <= self.max_chunk_size:
            return [{
                'chunk_id': 1,
                'text': paragraph,
                'is_full_paragraph': True
            }]
        
        # Split into chunks
        chunks = self.split_paragraph_into_chunks(paragraph, language)
        
        return chunks