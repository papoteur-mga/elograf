from __future__ import annotations

import os
import shlex
from typing import Dict, List, Tuple

from eloGraf.settings import DEFAULT_RATE, Settings


class CommandBuildError(Exception):
    """Raised when dictation command cannot be constructed."""


def build_dictation_command(settings: Settings, location: str) -> Tuple[List[str], Dict[str, str]]:
    if not location:
        raise CommandBuildError("Model location is required")

    cmd: List[str] = ["nerd-dictation", "begin"]
    if settings.sampleRate != DEFAULT_RATE:
        cmd.append(f"--sample-rate={settings.sampleRate}")
    if settings.timeout != 0:
        cmd.append(f"--timeout={settings.timeout}")
    if settings.idleTime != 0:
        cmd.append(f"--idle-time={float(settings.idleTime) / 1000}")
    if settings.fullSentence:
        cmd.append("--full-sentence")
    if settings.punctuate != 0:
        cmd.append(f"--punctuate-from-previous-timeout={settings.punctuate}")
    if settings.digits:
        cmd.append("--numbers-as-digits")
    if settings.useSeparator:
        cmd.append("--numbers-use-separator")
    if settings.deviceName != "default":
        cmd.append(f"--pulse-device-name={settings.deviceName}")
    if settings.freeCommand:
        try:
            cmd.extend(shlex.split(settings.freeCommand))
        except ValueError:
            cmd.append(settings.freeCommand)
    env: Dict[str, str] = os.environ.copy()
    if settings.env:
        for variable in settings.env.split(" "):
            if not variable:
                continue
            if "=" not in variable:
                raise CommandBuildError("Environment variables should be in the form key=value")
            key, value = variable.split("=", 1)
            env[key] = value
    if settings.tool == "DOTOOL":
        if settings.keyboard:
            env["DOTOOL_XKB_LAYOUT"] = settings.keyboard
        cmd.append("--simulate-input-tool=DOTOOL")
    cmd.append(f"--vosk-model-dir={location}")
    cmd.append("--output=SIMULATE_INPUT")
    cmd.append("--continuous")
    if os.name != "posix":
        cmd.append("--input-method=pynput")
    if not any(argument.startswith("--verbose") for argument in cmd):
        cmd.append("--verbose=1")
    return cmd, env
