"""Tests for InferenceBackend abstract class."""
import pytest
from abc import ABC


def test_inference_backend_is_abstract():
    """InferenceBackend debe ser una clase abstracta."""
    from eloGraf.inference_backend import InferenceBackend
    
    assert issubclass(InferenceBackend, ABC)
    
    # No debe poder instanciarse directamente
    with pytest.raises(TypeError):
        InferenceBackend()


def test_inference_backend_has_required_methods():
    """Debe definir los métodos abstractos requeridos."""
    from eloGraf.inference_backend import InferenceBackend
    
    required_methods = ['load_model', 'transcribe', 'transcribe_streaming', 
                       'unload_model', 'is_loaded', 'get_memory_usage']
    
    for method in required_methods:
        assert hasattr(InferenceBackend, method)


def test_mock_backend_can_be_created():
    """Un backend mock debe poder implementar la interfaz."""
    from eloGraf.inference_backend import InferenceBackend
    
    class MockBackend(InferenceBackend):
        def load_model(self, model_path: str, **kwargs) -> None:
            self._loaded = True
        
        def transcribe(self, audio: bytes) -> str:
            return "mock transcription"
        
        def transcribe_streaming(self, audio: bytes):
            yield "mock"
            yield "transcription"
        
        def unload_model(self) -> None:
            self._loaded = False
        
        @property
        def is_loaded(self) -> bool:
            return getattr(self, '_loaded', False)
        
        def get_memory_usage(self) -> dict:
            return {'ram_mb': 100, 'vram_mb': None}
    
    backend = MockBackend()
    assert not backend.is_loaded
    
    backend.load_model("/path/to/model")
    assert backend.is_loaded
    
    text = backend.transcribe(b"audio data")
    assert text == "mock transcription"
    
    backend.unload_model()
    assert not backend.is_loaded
