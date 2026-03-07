"""Tests for TextFormatter."""
import pytest


def test_text_formatter_exists():
    """TextFormatter debe existir."""
    from eloGraf.text_formatter import TextFormatter
    
    formatter = TextFormatter()
    assert formatter is not None


def test_capitalize_sentences():
    """Debe capitalizar primera letra de cada oración."""
    from eloGraf.text_formatter import TextFormatter
    
    formatter = TextFormatter()
    
    # Oración simple
    assert formatter.capitalize_sentences("hello world") == "Hello world"
    
    # Múltiples oraciones
    text = "hello world. this is a test. another sentence"
    result = formatter.capitalize_sentences(text)
    assert result == "Hello world. This is a test. Another sentence"
    
    # Ya capitalizado no debe cambiar
    assert formatter.capitalize_sentences("Hello world") == "Hello world"


def test_capitalize_after_exclamation():
    """Debe capitalizar después de signos de exclamación e interrogación."""
    from eloGraf.text_formatter import TextFormatter
    
    formatter = TextFormatter()
    
    text = "hello! how are you? i'm fine"
    result = formatter.capitalize_sentences(text)
    assert "Hello! How are you? I'm fine" == result


def test_add_punctuation_for_questions():
    """Debe añadir '?' a preguntas detectadas por palabras clave."""
    from eloGraf.text_formatter import TextFormatter
    
    formatter_en = TextFormatter(locale="en_US")
    # En inglés
    assert formatter_en.add_punctuation("what time is it").endswith("?")
    assert formatter_en.add_punctuation("how are you").endswith("?")
    
    formatter_es = TextFormatter(locale="es_ES")
    # En español
    assert formatter_es.add_punctuation("cómo estás").endswith("?")
    assert formatter_es.add_punctuation("qué hora es").endswith("?")
    
    # No es pregunta
    assert not formatter_en.add_punctuation("hello world").endswith("?")


def test_format_method_applies_all():
    """El método format() debe aplicar todas las transformaciones."""
    from eloGraf.text_formatter import TextFormatter
    
    formatter = TextFormatter()
    
    text = "what time is it. hello world"
    result = formatter.format(text)
    
    assert result.startswith("What")  # Capitalizado
    assert "it. Hello" in result  # Segunda oración capitalizada (it no se capitaliza)
    assert result.endswith("?")  # Pregunta detectada
