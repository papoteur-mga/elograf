"""Integration tests for VoskLocal engine."""
import pytest
from unittest.mock import Mock, patch, MagicMock


def test_vosk_local_plugin_registration():
    """El plugin debe estar registrado."""
    from eloGraf.stt_factory import get_available_engines
    
    engines = get_available_engines()
    assert "vosk-local" in engines


def test_vosk_local_create_engine():
    """Debe poder crear controller y runner."""
    from eloGraf.stt_factory import create_stt_engine
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    
    settings = VoskLocalSettings(model_path="/fake/path")
    
    with patch('vosk.Model'), patch('vosk.KaldiRecognizer'):
        controller, runner = create_stt_engine("vosk-local", settings=settings)
        
        assert controller is not None
        assert runner is not None


def test_vosk_local_full_lifecycle():
    """Test del ciclo completo: start -> transcribe -> stop."""
    from eloGraf.engines.vosk_local.runner import VoskLocalRunner
    from eloGraf.engines.vosk_local.controller import VoskLocalController
    from eloGraf.engines.vosk_local.settings import VoskLocalSettings
    
    settings = VoskLocalSettings(
        model_path="/fake/path",
        vad_type="rms",  # Usar RMS para no cargar Silero en tests
        text_formatting=False,
    )
    
    with patch('eloGraf.engines.vosk_local.runner.VoskInferenceBackend') as mock_backend_class, \
         patch('eloGraf.engines.vosk_local.runner.AudioPipeline') as mock_pipeline_class:
        
        # Setup mocks
        mock_backend = MagicMock()
        mock_backend.is_loaded = True
        mock_backend_class.return_value = mock_backend
        
        mock_pipeline = MagicMock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # Create components
        controller = VoskLocalController(settings)
        runner = VoskLocalRunner(controller, settings)
        
        # Test lifecycle
        # Start expects some command args, but for threaded it might be ignored
        assert runner.start([])
        
        # Wait for background loading to finish
        import time
        max_wait = 5.0
        start_wait = time.time()
        while controller.state.name != "READY" and time.time() - start_wait < max_wait:
            time.sleep(0.1)
            
        assert controller.state.name == "READY"
        
        runner.suspend()
        assert controller.state.name == "SUSPENDED"
        
        runner.resume()
        assert controller.state.name == "READY"
        
        runner.stop()
        assert controller.state.name == "IDLE"
