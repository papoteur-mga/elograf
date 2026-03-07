"""Tests for VoskInferenceBackend."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json


def test_vosk_backend_implements_interface():
    """VoskInferenceBackend debe implementar InferenceBackend."""
    from eloGraf.engines.vosk_local.inference_backend import VoskInferenceBackend
    from eloGraf.inference_backend import InferenceBackend
    
    assert issubclass(VoskInferenceBackend, InferenceBackend)


def test_vosk_backend_load_model():
    """Debe cargar modelo Vosk correctamente."""
    from eloGraf.engines.vosk_local.inference_backend import VoskInferenceBackend
    
    with patch('vosk.Model') as mock_model, \
         patch('vosk.KaldiRecognizer') as mock_recognizer:
        
        backend = VoskInferenceBackend()
        backend.load_model("/path/to/model")
        
        mock_model.assert_called_once_with("/path/to/model")
        assert backend.is_loaded


def test_vosk_backend_transcribe():
    """Debe transcribir audio correctamente."""
    from eloGraf.engines.vosk_local.inference_backend import VoskInferenceBackend
    
    with patch('vosk.Model'), patch('vosk.KaldiRecognizer') as mock_rec_class:
        mock_recognizer = MagicMock()
        mock_rec_class.return_value = mock_recognizer
        
        # Simular resultado de Vosk
        mock_recognizer.AcceptWaveform.return_value = True
        mock_recognizer.Result.return_value = json.dumps({"text": "hello world"})
        
        backend = VoskInferenceBackend()
        backend.load_model("/path/to/model")
        
        result = backend.transcribe(b"audio_data")
        
        assert result == "hello world"


def test_vosk_backend_unload():
    """Debe liberar recursos correctamente."""
    from eloGraf.engines.vosk_local.inference_backend import VoskInferenceBackend
    
    with patch('vosk.Model'), patch('vosk.KaldiRecognizer'):
        backend = VoskInferenceBackend()
        backend.load_model("/path/to/model")
        assert backend.is_loaded
        
        backend.unload_model()
        assert not backend.is_loaded


def test_vosk_backend_partial_callback():
    """Debe llamar callback de resultados parciales."""
    from eloGraf.engines.vosk_local.inference_backend import VoskInferenceBackend
    
    with patch('vosk.Model'), patch('vosk.KaldiRecognizer') as mock_rec_class:
        mock_recognizer = MagicMock()
        mock_rec_class.return_value = mock_recognizer
        
        partial_callback = Mock()
        
        backend = VoskInferenceBackend()
        backend.load_model("/path/to/model", partial_callback=partial_callback)
        
        # Simular resultado parcial
        mock_recognizer.AcceptWaveform.return_value = False
        mock_recognizer.PartialResult.return_value = json.dumps({"partial": "hello"})
        
        list(backend.transcribe_streaming(b"audio"))
        
        partial_callback.assert_called_with("hello")
