"""Built-in STT engine modules."""

from __future__ import annotations

# Import modules for side effects (engine plugin registration)
from .nerd import engine  # noqa: F401
from .whisper import engine  # noqa: F401
from .google import engine  # noqa: F401
from .openai import engine  # noqa: F401
from .assemblyai import engine  # noqa: F401
from .gemini import engine  # noqa: F401
from .vosk_local import engine  # noqa: F401

__all__ = [
    "nerd",
    "whisper",
    "google",
    "openai",
    "assemblyai",
    "gemini",
    "vosk_local",
]
