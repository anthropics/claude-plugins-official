import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.name != "nt", reason="Windows command override")
def test_windows_commands_use_git_bash(tmp_path):
    shell = shutil.which("pwsh") or shutil.which("powershell")
    if not shell or not shutil.which("git.exe"):
        pytest.skip("PowerShell and Git for Windows are required")
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    commands = {hook["commandWindows"] for groups in hooks.values() for group in groups
                for hook in group["hooks"] if hook["type"] == "command"}
    assert len(commands) == 2
    env = os.environ | {"CLAUDE_PLUGIN_ROOT": str(ROOT), "CLAUDE_CONFIG_DIR": str(tmp_path),
                        "SECURITY_WARNINGS_STATE_DIR": str(tmp_path), "PIP_NO_INDEX": "1"}
    for command in commands:
        result = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command", command],
                                input="{}", text=True, capture_output=True, env=env, timeout=120)
        assert result.returncode == 0, result.stderr
    env["PATH"] = str(Path(os.environ["SystemRoot"]) / "System32")
    result = subprocess.run([shell, "-NoProfile", "-NonInteractive", "-Command", next(iter(commands))],
                            input="{}", text=True, capture_output=True, env=env, timeout=30)
    assert result.returncode != 0
