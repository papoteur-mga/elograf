from __future__ import annotations

import os
import subprocess
import sys


def test_cli_list_models_runs_without_qt(tmp_path, monkeypatch):
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    env["QT_QPA_PLATFORM"] = "offscreen"
    proc = subprocess.run(
        [sys.executable, "-m", "eloGraf.elograf", "--list-models"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        cwd=tmp_path,
    )
    assert proc.returncode in (0, 1)
    # Command should print a message about models even without GUI
    assert "models" in proc.stdout.lower()
