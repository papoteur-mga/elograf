"""Abstract base class for STT inference backends."""
from abc import ABC, abstractmethod
from typing import Iterator, Optional, Dict, Any


class InferenceBackend(ABC):
    """Abstract base class for speech-to-text inference backends.
    
    Implementations: VoskInferenceBackend, WhisperInferenceBackend, etc.
    
    This abstraction allows the ThreadedInferenceRunner to work with
    different STT engines without knowing their specifics.
    """
    
    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> None:
        """Load model into memory (RAM/VRAM).
        
        This method may take several seconds for large models.
        It should be called in a background thread to avoid blocking UI.
        
        Args:
            model_path: Path to model files or identifier (e.g., "tiny" for Whisper)
            **kwargs: Backend-specific options (device, compute_type, etc.)
        
        Raises:
            FileNotFoundError: If model files not found
            RuntimeError: If model loading fails
        """
        pass
    
    @abstractmethod
    def transcribe(self, audio: bytes) -> str:
        """Transcribe complete audio block (blocking).
        
        Args:
            audio: Raw PCM audio data (16-bit, 16kHz, mono)
            
        Returns:
            Complete transcribed text
            
        Raises:
            RuntimeError: If model not loaded or inference fails
        """
        pass
    
    @abstractmethod
    def transcribe_streaming(self, audio: bytes) -> Iterator[str]:
        """Transcribe with partial results for UI feedback.
        
        Note: Not all backends support true streaming. Default
        implementation may yield final result only.
        
        Args:
            audio: Raw PCM audio data (16-bit, 16kHz, mono)
            
        Yields:
            Partial transcription fragments
        """
        pass
    
    @abstractmethod
    def unload_model(self) -> None:
        """Release model resources (RAM/VRAM).
        
        Implementations should call gc.collect() and, if using GPU,
        torch.cuda.empty_cache() to free VRAM.
        """
        pass
    
    @property
    @abstractmethod
    def is_loaded(self) -> bool:
        """Return True if model is loaded in memory."""
        pass
    
    @abstractmethod
    def get_memory_usage(self) -> Dict[str, Optional[int]]:
        """Return memory usage statistics.
        
        Returns:
            Dictionary with keys:
                - 'ram_mb': RAM usage in megabytes
                - 'vram_mb': VRAM usage in megabytes (None if not using GPU)
        """
        pass
