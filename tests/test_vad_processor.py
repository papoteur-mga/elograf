"""Tests for VAD processors."""
import pytest
import numpy as np
from unittest.mock import Mock, patch


def test_vad_result_enum():
    """Debe existir el enum de resultados."""
    from eloGraf.vad_processor import VADResult
    
    assert VADResult.SILENCE
    assert VADResult.SPEECH_START
    assert VADResult.SPEECH_ONGOING
    assert VADResult.SPEECH_END


def test_rms_vad_detects_silence():
    """RMSVAD debe detectar silencio (audio bajo)."""
    from eloGraf.vad_processor import RMSVADProcessor, VADResult
    
    vad = RMSVADProcessor(threshold=0.5)
    
    # Audio casi silencioso
    silence_audio = b"\x00\x00" * 1000
    result = vad.process(silence_audio)
    
    assert result == VADResult.SILENCE


def test_rms_vad_detects_speech():
    """RMSVAD debe detectar voz (audio alto)."""
    from eloGraf.vad_processor import RMSVADProcessor, VADResult
    
    vad = RMSVADProcessor(threshold=0.5)
    
    # Audio "ruidoso" (simulado con valores altos)
    loud_audio = b"\xff\x7f" * 1000  # Valores máximos 16-bit
    
    # Primera llamada: SPEECH_START
    result = vad.process(loud_audio)
    assert result == VADResult.SPEECH_START
    
    # Segunda llamada: SPEECH_ONGOING
    result = vad.process(loud_audio)
    assert result == VADResult.SPEECH_ONGOING


def test_vad_state_machine_silence_timeout():
    """El VAD debe emitir SPEECH_END después de silencio prolongado."""
    from eloGraf.vad_processor import RMSVADProcessor, VADResult
    
    # Timeout muy corto para testing
    vad = RMSVADProcessor(
        threshold=0.5,
        min_speech_duration_ms=0,
        silence_timeout_ms=50
    )
    
    loud_audio = b"\xff\x7f" * 100
    silence_audio = b"\x00\x00" * 100
    
    # Iniciar habla
    assert vad.process(loud_audio) == VADResult.SPEECH_START
    
    # Continuar habla
    assert vad.process(loud_audio) == VADResult.SPEECH_ONGOING
    
    # Silencio - aún no timeout
    vad.process(silence_audio)
    
    # Esperar más que el timeout
    import time
    time.sleep(0.06)
    
    # Ahora debe detectar fin de habla
    result = vad.process(silence_audio)
    assert result == VADResult.SPEECH_END


def test_silero_vad_processor_exists():
    """SileroVADProcessor debe existir y ser instanciable."""
    from eloGraf.vad_processor import SileroVADProcessor
    
    # Mock del modelo para no cargar torch en tests
    with patch('torch.hub.load') as mock_load:
        mock_load.return_value = (Mock(), [Mock()])
        vad = SileroVADProcessor(threshold=0.5)
        assert vad is not None


def test_webrtc_vad_processor_exists():
    """WebRTCVADProcessor debe existir y ser instanciable."""
    try:
        from eloGraf.vad_processor import WebRTCVADProcessor
        import webrtcvad
    except (ImportError, ModuleNotFoundError):
        pytest.skip("webrtcvad not available or failing to import (common on some environments)")
    
    with patch('webrtcvad.Vad') as mock_vad:
        vad = WebRTCVADProcessor(aggressiveness=2)
        assert vad is not None
