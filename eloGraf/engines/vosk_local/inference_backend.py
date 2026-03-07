"""Vosk implementation of InferenceBackend."""
import json
import gc
from typing import Optional, Callable, Iterator

from eloGraf.inference_backend import InferenceBackend


class VoskInferenceBackend(InferenceBackend):
    """Inference backend for Vosk speech recognition.
    
    Uses external VAD (SileroVAD) for segmentation, not internal Kaldi VAD.
    """
    
    def __init__(self, sample_rate: int = 16000):
        self._sample_rate = sample_rate
        self._model: Optional['vosk.Model'] = None
        self._recognizer: Optional['vosk.KaldiRecognizer'] = None
        self._partial_callback: Optional[Callable[[str], None]] = None
    
    def load_model(self, model_path: str, **kwargs) -> None:
        """Load Vosk model.
        
        Args:
            model_path: Path to Vosk model directory
            **kwargs: 
                - partial_callback: Function to call with partial results
        """
        import vosk
        import logging
        
        # Sync Vosk log level with Python logging level
        # Vosk: -1 = off, 0 = normal, 1 = info, 2 = debug
        level = logging.getLogger().getEffectiveLevel()
        if level >= logging.ERROR:
            vosk.SetLogLevel(-1)
        elif level >= logging.WARNING:
            vosk.SetLogLevel(0)
        elif level >= logging.INFO:
            vosk.SetLogLevel(0)
        else: # DEBUG
            vosk.SetLogLevel(1)
        
        self._partial_callback = kwargs.get('partial_callback')
        self._model = vosk.Model(model_path)
        self._recognizer = vosk.KaldiRecognizer(self._model, self._sample_rate)
    
    def transcribe(self, audio: bytes) -> str:
        """Transcribe audio segment and flush recognizer.
        
        Note: Audio should already be segmented by VAD.
        """
        if not self._recognizer:
            raise RuntimeError("Model not loaded")
        
        # In segmented mode, we always want the final result of the segment
        # and reset the recognizer state for the next one.
        self._recognizer.AcceptWaveform(audio)
        result = json.loads(self._recognizer.Result())
        return result.get("text", "")
    
    def transcribe_streaming(self, audio: bytes) -> Iterator[str]:
        """Transcribe with partial results."""
        if not self._recognizer:
            raise RuntimeError("Model not loaded")
        
        if self._recognizer.AcceptWaveform(audio):
            result = json.loads(self._recognizer.Result())
            text = result.get("text", "")
            if text:
                yield text
        else:
            partial = json.loads(self._recognizer.PartialResult())
            text = partial.get("partial", "")
            if text and self._partial_callback:
                self._partial_callback(text)
            yield text
    
    def unload_model(self) -> None:
        """Unload model and free memory."""
        self._recognizer = None
        self._model = None
        self._partial_callback = None
        gc.collect()
    
    @property
    def is_loaded(self) -> bool:
        return self._model is not None
    
    def get_memory_usage(self) -> dict:
        """Get memory usage."""
        import psutil
        process = psutil.Process()
        return {
            'ram_mb': process.memory_info().rss // (1024 * 1024),
            'vram_mb': None,  # Vosk doesn't use GPU
        }
