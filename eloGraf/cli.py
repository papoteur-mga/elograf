from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Optional

from eloGraf.settings import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Place an icon in systray to launch offline speech recognition."
    )
    parser.add_argument("-l", "--log", help="specify the log level", dest="loglevel")
    parser.add_argument("--version", help="show version and exit", action="store_true")
    parser.add_argument("--begin", help="begin dictation (or launch if not running)", action="store_true")
    parser.add_argument("--end", help="end dictation in running instance", action="store_true")
    parser.add_argument("--exit", help="exit the running instance", action="store_true")
    parser.add_argument("--list-models", help="list available models", action="store_true")
    parser.add_argument("--set-model", help="set the active model by name", metavar="MODEL_NAME")
    parser.add_argument("--resume", help="resume dictation if suspended", action="store_true")
    parser.add_argument("--suspend", help="suspend dictation in running instance", action="store_true")
    return parser


@dataclass
class CliExit:
    code: int
    stdout: str = ""
    stderr: str = ""


def handle_model_commands(args, settings: Settings) -> Optional[CliExit]:
    if not args.list_models and not args.set_model:
        return None

    settings.load()

    if args.list_models:
        if not settings.models:
            return CliExit(
                code=0,
                stdout="No models configured\n\nUse the GUI (elograf) to download or import models\n",
            )

        current_model = settings.value("Model/name") if settings.contains("Model/name") else ""
        lines = ["Available models:", "-" * 80]
        for model in settings.models:
            marker = "●" if model["name"] == current_model else " "
            lines.extend(
                [
                    f"{marker} {model['name']}",
                    f"  Language: {model['language']}",
                    f"  Type: {model['type']}",
                    f"  Version: {model['version']}",
                    f"  Size: {model['size']}",
                    f"  Location: {model['location']}",
                    "",
                ]
            )
        return CliExit(code=0, stdout="\n".join(lines) + "\n")

    if args.set_model:
        model_name = args.set_model
        for model in settings.models:
            if model["name"] == model_name:
                settings.setValue("Model/name", model_name)
                return CliExit(code=0, stdout=f"✓ Model set to '{model_name}'\n")
        available = "\n".join(f"  - {model['name']}" for model in settings.models)
        message = f"✗ Model '{model_name}' not found\n\nAvailable models:\n{available}\n"
        return CliExit(code=1, stderr=message)

    return None


def choose_ipc_command(args) -> Optional[str]:
    if args.exit:
        return "exit"
    if args.end:
        return "end"
    if args.begin:
        return "begin"
    if getattr(args, "resume", False):
        return "resume"
    if getattr(args, "suspend", False):
        return "suspend"
    return None
