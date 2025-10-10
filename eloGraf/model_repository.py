from __future__ import annotations

import os
import urllib.request
from pathlib import Path
from typing import Callable, Iterable, List, Tuple

import ujson

MODEL_USER_PATH = Path(os.path.expanduser("~/.config/vosk-models"))
MODEL_GLOBAL_PATH = Path("/usr/share/vosk-models")
MODEL_LIST = "model-list.json"
MODELS_URL = "https://alphacephei.com/vosk/models"


def get_size(start_path: os.PathLike[str] | str = ".") -> Tuple[float, str]:
    total_size = 0
    for dirpath, _, filenames in os.walk(start_path):
        for filename in filenames:
            fp = os.path.join(dirpath, filename)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    total = float(total_size)
    for unit in ("B", "Kb", "Mb", "Gb", "Tb"):
        if total < 1024:
            break
        total /= 1024
    return total, unit


def ensure_user_model_dir(path: Path | None = None) -> Path:
    target = Path(path) if path is not None else MODEL_USER_PATH
    target.mkdir(parents=True, exist_ok=True)
    return target


def model_list_path(base: Path | None = None) -> Path:
    base_path = ensure_user_model_dir(base)
    return base_path / MODEL_LIST


def load_model_index(base: Path | None = None) -> List[dict]:
    index_path = model_list_path(base)
    with index_path.open("r", encoding="utf-8") as handle:
        return ujson.load(handle)


Fetcher = Callable[[str, str | None, Callable[[int, int, int], None] | None], Tuple[str, object]]


def download_model_list(
    base: Path | None = None,
    *,
    fetcher: Fetcher = urllib.request.urlretrieve,
) -> Path:
    path = model_list_path(base)
    url = f"{MODELS_URL}/{MODEL_LIST}"
    fetcher(url, str(path), None)
    return path


def download_model_archive(
    url: str,
    *,
    fetcher: Fetcher = urllib.request.urlretrieve,
    reporthook: Callable[[int, int, int], None] | None = None,
) -> str:
    local_path, _ = fetcher(url, None, reporthook)
    return local_path


def filter_available_models(remote_models: Iterable[dict], installed_names: Iterable[str]) -> List[dict]:
    installed_set = set(installed_names)
    return [model for model in remote_models if model.get("name") not in installed_set and model.get("obsolete") != "true"]
