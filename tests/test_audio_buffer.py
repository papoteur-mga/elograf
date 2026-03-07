"""Tests for AudioBuffer circular buffer."""
import pytest
import threading
import time


def test_audiobuffer_stores_audio():
    """El buffer debe almacenar y recuperar audio."""
    from eloGraf.audio_pipeline import AudioBuffer
    
    buf = AudioBuffer(max_duration=5.0, sample_rate=16000)
    audio = b"\x00\x01\x02\x03" * 1000
    
    buf.append(audio)
    assert len(buf) == len(audio)


def test_audiobuffer_respects_max_duration():
    """El buffer no debe exceder max_duration."""
    from eloGraf.audio_pipeline import AudioBuffer
    
    # 1 segundo máximo a 16kHz mono 16-bit = 32000 bytes
    buf = AudioBuffer(max_duration=1.0, sample_rate=16000)
    
    # Añadir 2 segundos de audio
    audio_2s = b"\x00" * (16000 * 2 * 2)  # 2s * 16kHz * 2 bytes
    buf.append(audio_2s)
    
    # Debe mantener solo ~1 segundo
    assert len(buf) <= 32000 * 1.1  # 10% tolerancia


def test_audiobuffer_thread_safety():
    """El buffer debe ser thread-safe."""
    from eloGraf.audio_pipeline import AudioBuffer
    
    buf = AudioBuffer(max_duration=10.0, sample_rate=16000)
    errors = []
    
    def writer():
        try:
            for i in range(1000):
                buf.append(b"\x00\x01" * 100)
        except Exception as e:
            errors.append(e)
    
    def reader():
        try:
            for i in range(1000):
                _ = len(buf)
        except Exception as e:
            errors.append(e)
    
    t1 = threading.Thread(target=writer)
    t2 = threading.Thread(target=reader)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    assert not errors, f"Thread errors: {errors}"


def test_audiobuffer_get_slice():
    """Debe extraer slices de audio por tiempo."""
    from eloGraf.audio_pipeline import AudioBuffer
    
    buf = AudioBuffer(max_duration=5.0, sample_rate=16000)
    
    # Simular 100ms de audio = 16000 * 0.1 * 2 = 3200 bytes
    audio_100ms = b"ABCDEFGH" * 400  # 3200 bytes
    buf.append(audio_100ms)
    
    # Extraer los últimos 50ms = 1600 bytes
    slice_data = buf.get_slice(start_ms=-50, end_ms=0)
    assert len(slice_data) == 1600


def test_audiobuffer_clear():
    """Debe poder limpiarse completamente."""
    from eloGraf.audio_pipeline import AudioBuffer
    
    buf = AudioBuffer(max_duration=5.0, sample_rate=16000)
    buf.append(b"\x00" * 1000)
    assert len(buf) > 0
    
    buf.clear()
    assert len(buf) == 0
