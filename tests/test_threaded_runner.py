"""Tests for ThreadedInferenceRunner."""
import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch


def test_threaded_runner_initialization():
    """Debe inicializarse con componentes requeridos."""
    from eloGraf.threaded_runner import ThreadedInferenceRunner
    
    mock_controller = Mock()
    mock_backend = Mock()
    mock_pipeline = Mock()
    
    runner = ThreadedInferenceRunner(
        controller=mock_controller,
        inference_backend=mock_backend,
        audio_pipeline=mock_pipeline,
    )
    
    assert runner._controller == mock_controller
    assert runner._backend == mock_backend


def test_threaded_runner_starts_pipeline():
    """Debe iniciar el pipeline de audio."""
    from eloGraf.threaded_runner import ThreadedInferenceRunner
    
    mock_controller = Mock()
    mock_backend = Mock()
    mock_backend.is_loaded = True
    mock_pipeline = Mock()
    
    runner = ThreadedInferenceRunner(
        controller=mock_controller,
        inference_backend=mock_backend,
        audio_pipeline=mock_pipeline,
    )
    
    with patch('threading.Thread'):
        runner.start()
    
    mock_pipeline.start.assert_called_once()


def test_threaded_runner_processes_audio_queue():
    """Debe procesar audio de la cola de inferencia."""
    from eloGraf.threaded_runner import ThreadedInferenceRunner
    import queue
    
    mock_controller = Mock()
    mock_backend = Mock()
    mock_backend.transcribe.return_value = "transcribed text"
    mock_pipeline = Mock()
    
    runner = ThreadedInferenceRunner(
        controller=mock_controller,
        inference_backend=mock_backend,
        audio_pipeline=mock_pipeline,
    )
    
    # Simular audio en cola
    runner._inference_queue = queue.Queue()
    runner._inference_queue.put(b"audio data")
    runner._stop_event.clear()
    
    # Procesar una iteración
    runner._process_one_item()
    
    mock_backend.transcribe.assert_called_once_with(b"audio data")
    mock_controller.emit_transcription.assert_called_once_with("transcribed text")


def test_threaded_runner_applies_formatter():
    """Debe aplicar TextFormatter si está configurado."""
    from eloGraf.threaded_runner import ThreadedInferenceRunner
    import queue
    
    mock_controller = Mock()
    mock_backend = Mock()
    mock_backend.transcribe.return_value = "hello world"
    mock_pipeline = Mock()
    mock_formatter = Mock()
    mock_formatter.format.return_value = "Hello world."
    
    runner = ThreadedInferenceRunner(
        controller=mock_controller,
        inference_backend=mock_backend,
        audio_pipeline=mock_pipeline,
        text_formatter=mock_formatter,
    )
    
    runner._inference_queue = queue.Queue()
    runner._inference_queue.put(b"audio")
    runner._stop_event.clear()
    
    runner._process_one_item()
    
    mock_formatter.format.assert_called_once_with("hello world")
    mock_controller.emit_transcription.assert_called_once_with("Hello world.")


def test_threaded_runner_queue_full_warning():
    """Debe emitir warning cuando la cola está llena."""
    from eloGraf.threaded_runner import ThreadedInferenceRunner
    import queue
    
    mock_controller = Mock()
    mock_backend = Mock()
    mock_pipeline = Mock()
    
    runner = ThreadedInferenceRunner(
        controller=mock_controller,
        inference_backend=mock_backend,
        audio_pipeline=mock_pipeline,
        max_queue_depth=1,
    )
    
    # Llenar cola
    runner._inference_queue.put(b"audio1")
    
    # Intentar añadir más (no debe bloquear)
    runner._on_speech_detected(b"audio2")
    
    mock_controller.emit_error.assert_called_once()
    assert "CPU" in mock_controller.emit_error.call_args[0][0]


def test_threaded_runner_stop_cleans_resources():
    """Debe limpiar recursos al detener."""
    from eloGraf.threaded_runner import ThreadedInferenceRunner
    
    mock_controller = Mock()
    mock_backend = Mock()
    mock_pipeline = Mock()
    
    runner = ThreadedInferenceRunner(
        controller=mock_controller,
        inference_backend=mock_backend,
        audio_pipeline=mock_pipeline,
    )
    
    runner._inference_thread = Mock()
    runner._stop_event = Mock()
    
    runner.stop()
    
    runner._stop_event.set.assert_called_once()
    runner._inference_thread.join.assert_called_once()
