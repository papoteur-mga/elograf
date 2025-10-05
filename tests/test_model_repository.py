from __future__ import annotations

from pathlib import Path

import ujson

from eloGraf import model_repository as repo


def test_ensure_user_model_dir_creates_directory(tmp_path):
    target = tmp_path / "models"
    result = repo.ensure_user_model_dir(target)
    assert result == target
    assert target.exists()


def test_model_list_path_creates_parent(tmp_path):
    base = tmp_path / "nested"
    path = repo.model_list_path(base)
    assert path.name == repo.MODEL_LIST
    assert path.parent == base
    assert base.exists()


def test_load_model_index_reads_json(tmp_path):
    base = tmp_path / "models"
    data = [
        {"name": "vosk", "lang_text": "English"},
        {"name": "vosk-es", "lang_text": "Spanish"},
    ]
    path = repo.model_list_path(base)
    path.write_text(ujson.dumps(data))
    loaded = repo.load_model_index(base)
    assert loaded == data


def test_download_model_list_uses_fetcher(tmp_path):
    calls = []

    def fake_fetch(url, filename, reporthook):
        calls.append((url, filename, reporthook))
        Path(filename).write_text("[]")
        return filename, {}

    base = tmp_path / "models"
    result = repo.download_model_list(base, fetcher=fake_fetch)
    assert result.exists()
    assert calls and calls[0][0].endswith(repo.MODEL_LIST)


def test_download_model_archive_returns_path():
    def fake_fetch(url, filename, reporthook):
        return "/tmp/archive.zip", {}

    path = repo.download_model_archive("http://example/model.zip", fetcher=fake_fetch)
    assert path == "/tmp/archive.zip"


def test_filter_available_models_filters_names():
    remote = [
        {"name": "keep", "obsolete": "false"},
        {"name": "skip", "obsolete": "false"},
        {"name": "old", "obsolete": "true"},
    ]
    available = repo.filter_available_models(remote, ["skip"])
    assert available == [{"name": "keep", "obsolete": "false"}]
