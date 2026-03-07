"""Utilities for simulating keyboard input via external tools."""

from __future__ import annotations

import logging
import shutil
from subprocess import CalledProcessError, run
from typing import Iterable, Optional


class InputSimulator:
    """Simulates keyboard input using dotool or xdotool when available."""

    def __init__(self, preferred_tool: Optional[str] = None) -> None:
        self._preferred_tool = preferred_tool

    def type_text(self, text: str) -> None:
        """Type *text* using the first available input tool.

        Falls back from dotool to xdotool and logs a warning if neither succeeds.
        """
        for tool in self._candidate_tools():
            try:
                if self._execute_tool(tool, text):
                    return
            except (CalledProcessError, FileNotFoundError):
                logging.debug("Input simulator '%s' failed; trying fallback", tool)
                continue
        logging.warning("Neither dotool nor xdotool available for input simulation")

    def _execute_tool(self, tool: str, text: str) -> bool:
        """Execute the given tool to type text. Returns True on success."""
        if shutil.which(tool) is None:
            return False
        if tool == "dotool":
            # dotool reads commands from stdin: "type <text>"
            run([tool], input=f"type {text}", text=True, check=True)
            return True
        if tool == "xdotool":
            run([tool, "type", "--", text], check=True)
            return True
        return False

    def _candidate_tools(self) -> Iterable[str]:
        seen = set()
        if self._preferred_tool:
            seen.add(self._preferred_tool)
            yield self._preferred_tool
        for tool in ("dotool", "xdotool"):
            if tool not in seen:
                yield tool


_simulator: Optional[InputSimulator] = None


def get_input_simulator() -> InputSimulator:
    """Return a singleton input simulator instance."""
    global _simulator
    if _simulator is None:
        _simulator = InputSimulator()
    return _simulator


def type_text(text: str) -> None:
    """Convenience wrapper that types *text* using the singleton simulator."""
    get_input_simulator().type_text(text)
