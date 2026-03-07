"""Text formatting utilities for post-processing transcriptions."""
import re
from typing import List


class TextFormatter:
    """Formats transcribed text with capitalization, punctuation, and number conversion.
    
    Replicates advanced features from nerd-dictation for Vosk/Whisper compatibility.
    """
    
    # Question words by language
    QUESTION_WORDS = {
        'en': ['how', 'what', 'who', 'where', 'when', 'why', 'which', 'whom', 
               'whose', 'can', 'could', 'would', 'will', 'do', 'does', 'did'],
        'es': ['cómo', 'como', 'qué', 'que', 'quién', 'quien', 'dónde', 'donde', 
               'cuándo', 'cuando', 'por qué', 'porque', 'cuál', 'cual', 
               'cuánto', 'cuanto', 'para qué'],
    }
    
    def __init__(self, locale: str = "en_US"):
        """
        Args:
            locale: Locale string (e.g., "en_US", "es_ES")
        """
        self._locale = locale
        self._language = locale.split('_')[0].lower()
    
    def format(self, text: str) -> str:
        """Apply all formatting transformations.
        
        Order matters:
        1. Add punctuation (detect questions)
        2. Capitalize sentences
        3. Format numbers
        """
        text = self.add_punctuation(text)
        text = self.capitalize_sentences(text)
        text = self.format_numbers(text, self._locale)
        return text
    
    def capitalize_sentences(self, text: str) -> str:
        """Capitalize the first letter of each sentence.
        
        Handles multiple sentence endings: . ! ?
        """
        if not text:
            return text
        
        # Split keeping delimiters
        parts = re.split(r'([.!?]\s+)', text)
        
        result = []
        capitalize_next = True
        
        for part in parts:
            if not part:
                continue
                
            stripped = part.strip()
            if not stripped:
                result.append(part)
                continue
            
            if capitalize_next and stripped[0].isalpha():
                part = part[0].upper() + part[1:]
                capitalize_next = False
            
            # Check if this part ends a sentence
            if stripped[-1] in '.!?' and not stripped.endswith('...'):
                capitalize_next = True
            
            result.append(part)
        
        return ''.join(result)
    
    def format_numbers(self, text: str, locale: str) -> str:
        """Convert written numbers to digits.
        
        TODO: Implement with word2number library for specific locales.
        For now, returns text unchanged.
        
        Examples (future):
            "twenty one" -> "21"
            "dos mil veinticuatro" -> "2024"
        """
        # Placeholder for future implementation
        # Would use word2number or similar library
        return text
    
    def add_punctuation(self, text: str) -> str:
        """Add basic punctuation based on sentence content.
        
        Currently detects questions based on starting words.
        """
        if not text:
            return text
        
        stripped = text.strip()
        
        # If already has ending punctuation, don't change
        if stripped[-1] in '.!?':
            return text
        
        # Check if it's a question
        text_lower = stripped.lower()
        words = self.QUESTION_WORDS.get(self._language, self.QUESTION_WORDS['en'])
        
        for word in words:
            if text_lower.startswith(word + ' '):
                return text + '?'
        
        return text
