from __future__ import annotations

import logging
import os


PID_FILE = os.path.expanduser("~/.config/Elograf/elograf.pid")


def write_pid_file() -> str:
    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, "w", encoding="utf-8") as handle:
        handle.write(str(os.getpid()))
    return PID_FILE


def remove_pid_file() -> None:
    try:
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
    except Exception as exc:
        logging.warning("Failed to remove PID file: %s", exc)
